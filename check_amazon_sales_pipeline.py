import os
import re
import time
import urllib.parse
from urllib.parse import urljoin
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# CẤU HÌNH ĐẦU VÀO / ĐẦU RA THEO ĐÚNG 4 NHÓM PHÂN LOẠI CỦA BẠN
# ==============================================================================
DEFAULT_INPUT_FILE = "priority_list_2026-10-06_v2_sorted.xlsx"
DEFAULT_OUTPUT_FILE = "priority_list_2026-10-06_v2_sorted_checked.xlsx"

# User-Agent xoay vòng để tránh bị chặn 403
HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
]

# 1. Bộ từ khóa Cỏ nhân tạo / Khay / Nhà vệ sinh cho chó (Mở rộng toàn diện)
POTTY_KEYWORDS = [
    'potty', 'toilet', 'pee pad', 'puppy pad', 'wee wee', 'pee mat', 'turf', 
    'artificial grass', 'dog grass', 'real grass', 'grass mat', 'grass pad',
    'dog lawn', 'fresh patch', 'potty patch', 'doggie lawn', 'porch potty',
    'indoor dog potty', 'potty tray', 'litter box', 'litter pan', 'potty training',
    'grass patch', 'pet loo', 'fake grass'
]

# 2. Bộ từ khóa Đồ chơi cho chó (Đã lọc bỏ các giống chó như Toy Poodle)
TOY_KEYWORDS_PHRASES = [
    'chew toy', 'dog toy', 'puppy toy', 'plush toy', 'rope toy', 'squeaky toy', 
    'interactive toy', 'teething toy', 'puzzle toy', 'fetch toy', 'kong', 
    'nylabone', 'snuggle puppy', 'chew stick', 'dental chew'
]

SUBPAGE_CANDIDATES = [
    'amazon', 'shop', 'store', 'product', 'supplies', 'puppy-supplies',
    'recommended', 'gear', 'favorite', 'buy'
]

# 4 CLASSIFICATION LABELS IN ENGLISH:
CLASS_TOY_ONLY = "Selling pet toys"
CLASS_POTTY_ONLY = "Selling artificial grass/pet toilets (TARGET)"
CLASS_BOTH = "Selling pet toys + Artificial grass/Pet toilets (TARGET)"
CLASS_OTHER_AMAZON = "There's an Amazon link, but no target sales."
CLASS_NO_AMAZON = "Amazon link not found"

# ==============================================================================
# HÀM BÓC TÁCH & PHÂN LOẠI THÔNG MINH
# ==============================================================================
def clean_url(url):
    if not url or pd.isna(url):
        return ""
    u = str(url).strip()
    if not u or u.lower() == 'nan':
        return ""
    if not u.startswith(('http://', 'https://')):
        u = 'https://' + u
    return u

def get_html_with_fallback(url, timeout=10):
    for headers in HEADERS_LIST:
        try:
            r = requests.get(url, headers=headers, timeout=timeout, verify=False, allow_redirects=True)
            if r.status_code == 200:
                return r
        except Exception:
            continue
    return None

def is_dog_toy(text):
    """
    Nhận diện đồ chơi chó, lọc bỏ trường hợp đề cập giống chó 'Toy Poodle', 'Toy Breed'
    """
    text_lower = text.lower()
    # Loại bỏ các từ chỉ giống chó: "toy poodle", "toy breed", "toy australian", "toy group"...
    cleaned = re.sub(r'\btoy\s+(poodle|dog|breed|australian|fox|group|maltese|spaniel|terrier)\b', '', text_lower)
    
    for kw in TOY_KEYWORDS_PHRASES:
        if kw in cleaned:
            return True
            
    # Bắt từ đơn chew, rope, plush, squeak kèm ranh giới từ
    if re.search(r'\b(chew|chews|chewing|squeaker|squeak|squeaky|plush|rope)\b', cleaned):
        return True
        
    # Bắt từ toys, pet toy
    if re.search(r'\b(toys|pet toy|play toy)\b', cleaned):
        return True
        
    return False

def is_potty_or_grass(text):
    """
    Nhận diện cỏ nhân tạo / khay / nhà vệ sinh cho chó
    """
    text_lower = text.lower()
    for kw in POTTY_KEYWORDS:
        if kw in text_lower:
            return True
            
    # Kiểm tra ranh giới từ grass, turf, litter
    if re.search(r'\b(grass|turf|litter)\b', text_lower):
        return True
        
    return False

def find_amazon_links_on_page(soup, base_url):
    direct_links = []
    subpages = []

    # 1. Tìm trong thẻ <a>
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        href_lower = href.lower()
        if 'amazon.com' in href_lower or 'amzn.to' in href_lower:
            direct_links.append(href)
        elif 'amazon' in href_lower and not href.startswith('#'):
            subpages.append(urljoin(base_url, href))
        elif any(cand in href_lower for cand in SUBPAGE_CANDIDATES) and not href.startswith('#'):
            full_sub = urljoin(base_url, href)
            if urllib.parse.urlparse(full_sub).netloc == urllib.parse.urlparse(base_url).netloc:
                subpages.append(full_sub)

    # 2. Tìm trong thẻ <img> (Logo/Banner Amazon)
    for img in soup.find_all('img'):
        src = img.get('src', '').lower()
        alt = img.get('alt', '').lower()
        if 'amazon' in src or 'amazon' in alt or 'amzn' in src:
            parent_a = img.find_parent('a')
            if parent_a and parent_a.get('href'):
                p_href = parent_a.get('href').strip()
                if 'amazon.com' in p_href.lower() or 'amzn.to' in p_href.lower():
                    direct_links.append(p_href)
                elif 'amazon' in p_href.lower():
                    subpages.append(urljoin(base_url, p_href))

    return direct_links, subpages

def process_single_website(raw_url):
    """
    Quét 1 website đối tác:
    Trả về: (amazon_link, phan_loai)
    """
    web = clean_url(raw_url)
    if not web:
        return None, CLASS_NO_AMAZON

    resp = get_html_with_fallback(web, timeout=10)
    if resp is None:
        return None, CLASS_NO_AMAZON

    soup = BeautifulSoup(resp.text, 'html.parser')
    page_text = soup.get_text()

    # Thu thập link Amazon và trang con
    amz_links, subpages = find_amazon_links_on_page(soup, web)
    combined_texts = [page_text[:5000]]

    # Quét thêm các trang con nếu có
    if subpages:
        for sub in list(dict.fromkeys(subpages))[:3]:
            sub_resp = get_html_with_fallback(sub, timeout=8)
            if sub_resp:
                sub_soup = BeautifulSoup(sub_resp.text, 'html.parser')
                sub_amz, _ = find_amazon_links_on_page(sub_soup, sub)
                amz_links.extend(sub_amz)
                combined_texts.append(sub_soup.get_text()[:5000])

    # Nếu không tìm thấy bất kỳ link Amazon nào
    if not amz_links:
        if 'amazon' in page_text.lower():
            return None, CLASS_OTHER_AMAZON
        return None, CLASS_NO_AMAZON

    # Chọn 1 link Amazon đại diện đẹp nhất
    chosen_amz_link = amz_links[0]
    for l in amz_links:
        if 'amazon.com/shop' in l.lower() or 'amzn.to' in l.lower():
            chosen_amz_link = l
            break

    # Quét nội dung trực tiếp trên các trang Amazon tìm được
    for link in list(dict.fromkeys(amz_links))[:4]:
        try:
            r = get_html_with_fallback(link, timeout=10)
            if r is not None:
                combined_texts.append(r.url)
                combined_texts.append(r.text[:20000])
            else:
                combined_texts.append(link)
        except Exception:
            combined_texts.append(link)

    # Gộp toàn bộ văn bản liên quan đến đối tác và Amazon để phân loại chuẩn xác
    all_context = " ".join(combined_texts)
    has_toy = is_dog_toy(all_context)
    has_potty = is_potty_or_grass(all_context)

    # PHÂN LOẠI CHUẨN XÁC 4 NHÓM:
    if has_toy and has_potty:
        phan_loai = CLASS_BOTH
    elif has_potty:
        phan_loai = CLASS_POTTY_ONLY
    elif has_toy:
        phan_loai = CLASS_TOY_ONLY
    else:
        phan_loai = CLASS_OTHER_AMAZON

    return chosen_amz_link, phan_loai

# ==============================================================================
# HÀM CHÍNH ĐIỀN ĐỦ 167 HÀNG VÀO FILE EXCEL
# ==============================================================================
def run_amazon_pipeline(input_file=DEFAULT_INPUT_FILE, output_file=DEFAULT_OUTPUT_FILE):
    print("=" * 80)
    print(" BẮT ĐẦU QUÉT VÀ PHÂN LOẠI THEO 4 NHÓM CHO TOÀN BỘ DANH SÁCH ")
    print(f" File nguồn: {input_file}")
    print(f" File đích:   {output_file}")
    print("=" * 80)

    if not os.path.exists(input_file):
        print(f"[!] Không tìm thấy file: {input_file}")
        return

    xl = pd.ExcelFile(input_file)
    sheet_name = xl.sheet_names[0]
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    total_rows = len(df)
    print(f"[*] Tổng số hàng cần xử lý: {total_rows} (Sheet: {sheet_name})")

    # Đảm bảo 2 cột đích tồn tại
    if 'Amazon Link' not in df.columns:
        df['Amazon Link'] = None
    if 'Phân loại Amazon' not in df.columns:
        df['Phân loại Amazon'] = None
    df['Amazon Link'] = df['Amazon Link'].astype(object)
    df['Phân loại Amazon'] = df['Phân loại Amazon'].astype(object)

    start_time = time.time()

    for idx, row in df.iterrows():
        current_num = idx + 1
        breeder = str(row.get('Breeder Name', f'Row {current_num}'))
        web = row.get('Website')

        prefix = f"[{current_num}/{total_rows}] {breeder[:28]:<30}"

        if not web or pd.isna(web):
            df.at[idx, 'Amazon Link'] = None
            df.at[idx, 'Phân loại Amazon'] = CLASS_NO_AMAZON
            print(f"{prefix} | Không có website.")
            continue

        print(f"{prefix} | Đang quét: {web}")
        amz_link, phan_loai = process_single_website(web)

        df.at[idx, 'Amazon Link'] = amz_link
        df.at[idx, 'Phân loại Amazon'] = phan_loai

        print(f"   -> Link:      {amz_link}")
        print(f"   -> Phân loại: {phan_loai}")

        # Tự động lưu checkpoint mỗi 15 hàng để không bị mất dữ liệu
        if current_num % 15 == 0:
            df.to_excel(output_file, sheet_name=sheet_name, index=False)
            print(f"   [Checkpoint] Đã lưu tiến độ {current_num}/{total_rows} vào {output_file}")

    # Lưu kết quả cuối cùng
    df.to_excel(output_file, sheet_name=sheet_name, index=False)
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f" HOÀN TẤT QUÉT {total_rows} HÀNG TRONG {elapsed:.1f} GIÂY!")
    print(f" KẾT QUẢ ĐÃ LƯU TẠI: {output_file}")
    print("=" * 80)

    # Thống kê phân loại
    print("\n--- BẢNG TỔNG KẾT PHÂN LOẠI AMAZON CHO BÊN SALE ---")
    print(df['Phân loại Amazon'].value_counts(dropna=False))
    print("----------------------------------------------------\n")

if __name__ == "__main__":
    run_amazon_pipeline()
