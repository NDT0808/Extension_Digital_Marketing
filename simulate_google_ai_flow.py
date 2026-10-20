"""
Script: simulate_google_ai_flow.py
Mục đích: Giả lập hành vi người dùng chậm mà chắc (Human-like pacing)
- Mở tab Google Search / Google AI (Gemini Overview)
- Tự động gõ link Facebook + bộ từ khóa các trường dữ liệu bằng tiếng Việt / Trung
- Đặt câu hỏi cho Google AI: "hãy tìm và dịch ra tiếng việt giúp tôi"
- Chờ Google AI sinh câu trả lời hoàn tất
- Bóc tách tự động các trường dữ liệu theo đúng cấu trúc priority-data-8
- Xuất / Ghi trực tiếp vào file Excel priority-data-8-20261013.xlsx
"""

import time
import re
import urllib.parse
from playwright.sync_api import sync_playwright
import openpyxl

# Query mẫu đúng như trong video của người dùng:
# [FB_URL] 名字 全名 用户社交 工作职位 国家地址 行业 添加日期 公司名称 公司网址 公司社交 公司所属国家 州 城市 公司所在行业 电话 hãy tìm và dịch ra tiếng việt giúp tôi
PROMPT_TEMPLATE = "{fb_url} 名字 全名 用户社交 工作职位 国家地址 行业 添加日期 公司名称 公司网址 公司社交 公司所属国家 州 城市 公司所在行业 电话 hãy tìm và dịch ra tiếng việt giúp tôi"

def parse_google_ai_text(raw_text):
    """
    Bóc tách các trường từ câu trả lời có cấu trúc của Google AI / Gemini
    """
    data = {}
    
    # 1. 名字 (Tên)
    m = re.search(r'[•\-*]?\s*(?:名字|\bTên\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['first_name'] = m.group(1).strip()
    
    # 2. 全名 (Họ và tên)
    m = re.search(r'[•\-*]?\s*(?:全名|\bHọ và tên\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['full_name'] = m.group(1).strip()
    
    # 3. 用户社交 (Mạng xã hội cá nhân)
    m = re.search(r'[•\-*]?\s*(?:用户社交|\bMạng xã hội cá nhân\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['user_social'] = m.group(1).strip()
    
    # 4. 工作职位 (Chức vụ / Vị trí)
    m = re.search(r'[•\-*]?\s*(?:工作职位|\bChức vụ\b|\bVị trí\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['job_title'] = m.group(1).strip()
    
    # 5. 国家地址 (Quốc gia & Địa chỉ)
    m = re.search(r'[•\-*]?\s*(?:国家地址|\bQuốc gia & Địa chỉ\b|\bĐịa chỉ\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['address'] = m.group(1).strip()
    
    # 6. 行业 (Ngành nghề cá nhân)
    m = re.search(r'[•\-*]?\s*(?:行业|\bNgành nghề cá nhân\b|\bNgành nghề\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['industry'] = m.group(1).strip()
    
    # 7. 公司名称 (Tên công ty)
    m = re.search(r'[•\-*]?\s*(?:公司名称|\bTên công ty\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['company_name'] = m.group(1).strip()
    
    # 8. 公司网址 (Website công ty)
    m = re.search(r'[•\-*]?\s*(?:公司网址|\bWebsite công ty\b|\bWebsite\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['company_website'] = m.group(1).strip()
    
    # 9. 公司社交 (Mạng xã hội của công ty)
    m = re.search(r'[•\-*]?\s*(?:公司社交|\bMạng xã hội của công ty\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['company_social'] = m.group(1).strip()
    
    # 10. 公司所属国家 (Quốc gia của công ty)
    m = re.search(r'[•\-*]?\s*(?:公司所属国家|\bQuốc gia của công ty\b|\bQuốc gia\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['company_country'] = m.group(1).strip()
    
    # 11. 州 (Bang)
    m = re.search(r'[•\-*]?\s*(?:州|\bBang\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['state'] = m.group(1).strip()
    
    # 12. 城市 (Thành phố)
    m = re.search(r'[•\-*]?\s*(?:城市|\bThành phố\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['city'] = m.group(1).strip()
    
    # 13. 公司所在行业 (Ngành nghề công ty)
    m = re.search(r'[•\-*]?\s*(?:公司所在行业|\bNgành nghề của công ty\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['company_industry'] = m.group(1).strip()
    
    # 14. 电话 (Điện thoại)
    m = re.search(r'[•\-*]?\s*(?:电话|\bĐiện thoại\b|\bSố điện thoại\b)\s*\(?[^):]*\)?\s*[:：]\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m: data['phone'] = m.group(1).strip()
    
    return data

def simulate_user_google_search(fb_url, headless=True):
    """
    Giả lập mở tab Google, gõ từng ký tự từ từ, bấm Enter và đợi Google AI trả lời
    """
    full_prompt = PROMPT_TEMPLATE.format(fb_url=fb_url)
    print(f"\n[Flow] Đang mở tab Google để tra cứu: {fb_url}")
    print(f"[Prompt] '{full_prompt[:60]}...'")
    
    with sync_playwright() as p:
        # Launch browser (có thể set headless=False để xem trực tiếp)
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="vi-VN"
        )
        page = context.new_page()
        
        # 1. Mở trang Google
        page.goto("https://www.google.com", timeout=30000)
        time.sleep(1.5)  # Nghỉ chậm rãi như người dùng
        
        # 2. Tìm ô tìm kiếm
        search_input = page.locator('textarea[name="q"], input[name="q"]').first
        if not search_input.is_visible():
            search_input = page.locator('textarea, input[type="text"]').first
            
        search_input.click()
        time.sleep(0.5)
        
        # 3. Gõ từ từ từng ký tự (hoặc chunk tự nhiên)
        print("[Giả lập gõ phím] Đang gõ câu hỏi vào Google...")
        search_input.type(full_prompt, delay=25)  # 25ms mỗi phím, mượt mà chuẩn xác
        time.sleep(1.0)
        
        # 4. Nhấn Enter để gửi truy vấn
        print("[Giả lập phím Enter] Đặt câu hỏi cho Google AI...")
        search_input.press("Enter")
        
        # 5. Đợi trang nạp và Google AI trả lời (chậm mà chắc: 8 - 12 giây)
        print("[Chờ Google AI] Đang đợi kết quả từ Google AI...")
        time.sleep(8.0)
        
        # Lấy nội dung trang
        body_text = page.locator("body").inner_text()
        
        # Bóc tách
        parsed = parse_google_ai_text(body_text)
        print(f"[Kết quả bóc tách] Tìm thấy {len(parsed)} trường: {list(parsed.keys())}")
        
        browser.close()
        return parsed

if __name__ == '__main__':
    # Test thử 1 lead như trong video
    test_fb = "https://www.facebook.com/HuskerDoodles"
    res = simulate_user_google_search(test_fb, headless=True)
    print("Parsed result:", res)
