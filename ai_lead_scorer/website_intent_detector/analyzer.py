import asyncio
import json
import os
import csv
import sys
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Vui lòng cài đặt playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

def load_keywords():
    with open('keywords.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_urls_from_csv(csv_path):
    """Trích xuất cột 'websites' hoặc 'resolved_urls' từ file CSV"""
    urls = set()
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                websites_str = row.get('websites', '') or row.get('resolved_urls', '')
                if websites_str:
                    for w in websites_str.split('|'):
                        w = w.strip()
                        if w.startswith('http') and 'facebook.com' not in w and 'instagram.com' not in w and 'google.com' not in w:
                            urls.add(w)
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
    return list(urls)

async def get_page_content(page, url):
    """Truy cập trang, cuộn xuống, chờ JS và lấy nội dung HTML"""
    try:
        # domcontentloaded nhanh hơn networkidle, đủ để script chính chạy
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        
        # Cuộn chuột xuống từ từ để kích hoạt lazy-loading của một số trang
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Chờ 1 giây để JS vẽ nội dung
        await asyncio.sleep(1) 
        
        # Lấy text
        text = await page.evaluate("document.body.innerText")
        text = text.lower() if text else ""
        
        # Lấy link để quét trang con
        links = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
        
        # Kiểm tra xem có thẻ <form> hoặc iframe chứa form phổ biến không (Google Form, Typeform)
        forms = await page.query_selector_all("form, iframe[src*='form'], iframe[src*='typeform'], iframe[src*='docs.google.com/forms']")
        has_form_tag = len(forms) > 0
        
        return text, links, has_form_tag
    except Exception as e:
        # Nếu lỗi (ví dụ timeout) vẫn có thể trang đã load một phần, trả về mảng rỗng để không bị chết tiến trình
        return "", [], False

def get_subpages(links, base_url):
    domain = urlparse(base_url).netloc
    subpages = set()
    priority_keywords = ['contact', 'apply', 'application', 'puppies', 'available', 'litters', 'about', 'adopt', 'form', 'inquir']
    
    for full_url in links:
        if not full_url or full_url.strip().startswith('javascript:') or full_url.strip().startswith('mailto:') or full_url.strip().startswith('tel:'):
            continue
            
        try:
            parsed_url = urlparse(full_url)
            # Chỉ lọc link nội bộ
            if parsed_url.netloc == domain and parsed_url.scheme in ['http', 'https']:
                clean_url = full_url.split('#')[0] # bỏ tham chiếu tới id (vd: #about)
                if clean_url != base_url:
                    subpages.add(clean_url)
        except:
            pass
                
    # Sắp xếp để ưu tiên quét các trang quan trọng trước
    def sort_key(url):
        url_lower = url.lower()
        for kw in priority_keywords:
            if kw in url_lower:
                return 0 
        return 1
        
    return sorted(list(subpages), key=sort_key)

async def analyze_website(browser, url, keywords_data, sem):
    if not url.startswith('http'):
        url = 'https://' + url
        
    result = {
        'url': url,
        'sells_dogs': False,
        'has_form': False,
        'has_take_home_kit': False,
        'pages_scanned': 0,
        'error': None
    }
    
    # sem để giới hạn số tab mở cùng lúc, tránh quá tải RAM
    async with sem:
        context = None
        try:
            # Tạo 1 session duyệt web ẩn danh riêng biệt
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
                ignore_https_errors=True,
                viewport={"width": 1280, "height": 800}
            )
            
            # Chặn tải file không cần thiết (ảnh, font, css, media) để chạy thật nhanh
            await context.route("**/*", lambda route: route.continue_() if route.request.resource_type in ["document", "script", "xhr", "fetch"] else route.abort())
            
            page = await context.new_page()
            
            base_text, base_links, has_form_tag = await get_page_content(page, url)
            
            if not base_text and not base_links:
                raise Exception("Không thể tải nội dung trang hoặc bị chặn truy cập")
                
            subpages = get_subpages(base_links, url)[:3]
            pages_to_scan = [url] + subpages
            result['pages_scanned'] = len(pages_to_scan)
            
            combined_text = base_text
            
            # Quét các trang con ưu tiên
            for page_url in subpages:
                try:
                    text, _, sub_form = await get_page_content(page, page_url)
                    combined_text += " " + text
                    if sub_form:
                        has_form_tag = True
                except:
                    continue
                    
            # 1. So khớp: Bán chó
            for kw in keywords_data['selling_dogs']:
                if kw.lower() in combined_text:
                    result['sells_dogs'] = True
                    break
                    
            # 2. So khớp: Form đăng ký
            if has_form_tag:
                result['has_form'] = True
            else:
                for kw in keywords_data['forms']:
                    if kw.lower() in combined_text:
                        result['has_form'] = True
                        break
                        
            # 3. So khớp: Take home kit
            for kw in keywords_data['take_home_kit']:
                if kw.lower() in combined_text:
                    result['has_take_home_kit'] = True
                    break
                    
        except Exception as e:
            result['error'] = str(e)
        finally:
            if context:
                await context.close()
                
        return result

async def async_main():
    if not os.path.exists('keywords.json'):
        print("Lỗi: Không tìm thấy file keywords.json")
        return
        
    keywords_data = load_keywords()
    urls = set()
    
    # 1. Nhận URL từ tham số lệnh (vd: python analyzer.py https://marthadach.com)
    if len(sys.argv) > 1:
        single_url = sys.argv[1]
        urls.add(single_url)
        print(f"🔍 Đang chạy Playwright (JavaScript Crawler) cho 1 link: {single_url}")
    else:
        if os.path.exists('urls.txt'):
            with open('urls.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        urls.add(line.strip())
                        
        csv_file = 'Datasets.csv'
        if os.path.exists(csv_file):
            print(f"Phát hiện file {csv_file}, đang trích xuất URLs...")
            csv_urls = extract_urls_from_csv(csv_file)
            urls.update(csv_urls)
            print(f"Đã lấy được {len(csv_urls)} website từ {csv_file}.")
        
    urls = list(urls)
    if not urls:
        print("Không có URL nào.")
        return

    # Giới hạn quét 50 trang đầu để không chờ lâu (Thích thì có thể gỡ bỏ)
    urls_to_test = urls[:50]
    print(f"\nBắt đầu phân tích (Bằng Playwright) {len(urls_to_test)} website (Quét trang chủ + Tối đa 3 trang con)...\n")
    
    results = []
    
    async with async_playwright() as p:
        # Bật trình duyệt ẩn danh
        browser = await p.chromium.launch(headless=True)
        # Giới hạn số lượng trình duyệt mở cùng lúc để không treo máy (RAM/CPU)
        sem = asyncio.Semaphore(4) 
        
        # Tạo danh sách các task bất đồng bộ
        tasks = [analyze_website(browser, url, keywords_data, sem) for url in urls_to_test]
        
        # Chạy đồng thời và in kết quả ngay khi một task hoàn thành
        for future in asyncio.as_completed(tasks):
            res = await future
            results.append(res)
            
            status = "✅" if not res['error'] else "❌"
            print(f"[{status}] {res['url']} (Đã quét {res['pages_scanned']} trang)")
            if not res['error']:
                print(f"  - Bán chó thật: {'CÓ' if res['sells_dogs'] else 'KHÔNG'}")
                print(f"  - Có Form đăng ký: {'CÓ' if res['has_form'] else 'KHÔNG'}")
                print(f"  - Có Take home kit: {'CÓ' if res['has_take_home_kit'] else 'KHÔNG'}")
            else:
                print(f"  - Lỗi: {res['error']}")
            print("-" * 40)
            
        await browser.close()
        
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print("\nHoàn tất! Đã lưu kết quả vào analysis_results.json")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    main()
