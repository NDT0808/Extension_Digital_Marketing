import csv
import requests
from bs4 import BeautifulSoup
import re
import os

# Đường dẫn file input (File CSV xuất từ Chrome Extension)
# Tạm thời để tên file cứng, người dùng có thể đổi tên khi chạy
INPUT_CSV = 'ket_qua_quet_website.csv' 
DATASETS_CSV = r'c:\Users\ASUS\Downloads\plugin_marketing\ai_lead_scorer\website_intent_detector\Datasets.csv'
OUTPUT_CSV = 'scored_leads_final.csv'

def normalize_url(url):
    if not url: return ""
    return url.replace('http://', '').replace('https://', '').replace('www.', '').strip().rstrip('/')

def load_datasets():
    datasets = {}
    if not os.path.exists(DATASETS_CSV):
        print(f"⚠️ Không tìm thấy {DATASETS_CSV}. Bỏ qua bước merge data.")
        return datasets
    
    with open(DATASETS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_urls = row.get('websites', '')
            if not raw_urls:
                continue
            for u in raw_urls.split('|'):
                norm = normalize_url(u)
                if norm:
                    datasets[norm] = row
    return datasets

def find_social_links(url):
    """
    Quét mã nguồn của website để tìm link Facebook, Instagram và Email
    """
    social_data = {
        'facebook': '',
        'instagram': '',
        'email': ''
    }
    
    try:
        # Thêm header để giả lập trình duyệt, tránh bị chặn
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm tất cả thẻ <a>
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].lower()
                
                # Tìm Facebook
                if 'facebook.com' in href and not social_data['facebook']:
                    if 'sharer' not in href: # Bỏ qua link share
                        social_data['facebook'] = a_tag['href']
                        
                # Tìm Instagram
                if 'instagram.com' in href and not social_data['instagram']:
                    social_data['instagram'] = a_tag['href']
                    
                # Tìm Email
                if href.startswith('mailto:') and not social_data['email']:
                    email_raw = a_tag['href'].replace('mailto:', '').split('?')[0].strip()
                    social_data['email'] = email_raw
            
            # Nếu chưa tìm thấy email qua thẻ <a>, dùng Regex tìm trên toàn bộ text
            if not social_data['email']:
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
                if emails:
                    # Lấy email đầu tiên hợp lệ (bỏ qua mấy cái email ảo của wix, sentry...)
                    for em in emails:
                        if not any(x in em.lower() for x in ['sentry', 'wix', 'example', 'domain']):
                            social_data['email'] = em
                            break
                            
    except Exception as e:
        print(f"[-] Lỗi khi quét social cho {url}: {e}")
        
    return social_data

def calculate_score_and_grade(row, social):
    """
    Chấm điểm (Lead Score) dựa trên marketing_parameter.html
    Và phân loại A, B, C, D
    """
    score = 0
    
    # 1. Có website hoạt động
    if row.get('Trang_Thai') != 'Không thể quét':
        score += 5
        
    # 2. Có Puppy Page (Bán chó)
    if row.get('Ban_Cho') == 'CO':
        score += 10
        
    # 3. Có Online Application (Form)
    if row.get('Co_Form') == 'CO':
        score += 10
        
    # 4. Có Take-home kit (thể hiện sự chuyên nghiệp/quan tâm sp)
    if row.get('Take_Home_Kit') == 'CO':
        score += 10
        
    # 5. Có Facebook
    if social['facebook']:
        score += 5
        
    # 6. Có Instagram
    if social['instagram']:
        score += 5

    # Phân loại (Grade)
    # Hạng A: Có web + bán chó + form + (social hoặc email) -> Đủ phễu bán hàng cao cấp
    if row.get('Ban_Cho') == 'CO' and row.get('Co_Form') == 'CO' and (social['facebook'] or social['instagram'] or social['email']):
        grade = 'A'
    # Hạng B: Có web + bán chó nhưng thiếu form hoặc thiếu social
    elif row.get('Ban_Cho') == 'CO':
        grade = 'B'
    # Hạng D: Web sập, hoặc quét báo lỗi hoàn toàn
    elif 'lỗi' in str(row.get('Trang_Thai')).lower() or 'timeout' in str(row.get('Trang_Thai')).lower():
        grade = 'D'
    # Hạng C: Các trường hợp còn lại (Web sống nhưng ko rõ bán chó)
    else:
        grade = 'C'
        
    return score, grade

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Không tìm thấy file '{INPUT_CSV}'.")
        print("Vui lòng tải file CSV từ Chrome Extension (đặt tên là ket_qua_quet_website.csv) và để chung thư mục với script này.")
        return

    print("🚀 Bắt đầu quy trình chấm điểm và gộp data...")
    datasets = load_datasets()
    
    leads = []
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
            
    results = []
    
    for idx, row in enumerate(leads):
        url = row['Website']
        print(f"[{idx+1}/{len(leads)}] Đang phân tích & Chấm điểm: {url}")
        
        norm_url = normalize_url(url)
        dataset_row = datasets.get(norm_url, {})
        
        # Lấy data có sẵn từ file tổng
        social = {
            'facebook': dataset_row.get('facebook_url', ''),
            'instagram': dataset_row.get('instagram_url', ''),
            'email': dataset_row.get('emails', '')
        }
        
        # Nếu thiếu email hoặc fb thì mới đi cào thêm để tiết kiệm thời gian
        if not social['facebook'] or not social['email']:
            scraped = find_social_links(url)
            if not social['facebook']: social['facebook'] = scraped['facebook']
            if not social['instagram']: social['instagram'] = scraped['instagram']
            if not social['email']: social['email'] = scraped['email']
        
        # Bước 2: Chấm điểm dựa trên dữ liệu Extension + Social
        score, grade = calculate_score_and_grade(row, social)
        
        # Gộp dữ liệu
        final_row = {
            'Name': dataset_row.get('name', ''),
            'Website': url,
            'Ban_Cho': row.get('Ban_Cho', ''),
            'Co_Form': row.get('Co_Form', ''),
            'Take_Home_Kit': row.get('Take_Home_Kit', ''),
            'Loai_Trang': row.get('Loai_Trang', 'Không rõ'),
            'State': dataset_row.get('state', ''),
            'City': dataset_row.get('city', ''),
            'Phones': dataset_row.get('phones', ''),
            'Email': social['email'],
            'Facebook': social['facebook'],
            'Instagram': social['instagram'],
            'Lead_Score': score,
            'Grade': grade,
            'Extension_Status': row.get('Trang_Thai', '')
        }
        results.append(final_row)
        
    # Xuất file kết quả
    fieldnames = ['Name', 'Website', 'Ban_Cho', 'Co_Form', 'Take_Home_Kit', 'Loai_Trang', 'State', 'City', 'Phones', 'Email', 'Facebook', 'Instagram', 'Lead_Score', 'Grade', 'Extension_Status']
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n✅ Hoàn tất! Đã chấm điểm {len(leads)} website.")
    print(f"📂 File kết quả đã được lưu tại: {OUTPUT_CSV}")

if __name__ == '__main__':
    main()
