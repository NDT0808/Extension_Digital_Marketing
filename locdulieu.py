import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import time

# 1. Đọc file Excel gốc
import os
input_path = 'Danh_Sach_Khach_Hang_Sales_Pet_Grass_2026-10-16.xlsx' if os.path.exists('Danh_Sach_Khach_Hang_Sales_Pet_Grass_2026-10-16.xlsx') else 'Danh_Sach_Khach_Hang_Sales_Pet_Grass_2026-10-15.xlsx'
df = pd.read_excel(input_path, sheet_name='Khach_Hang_Sales')

GENERIC_OWNERS = {
    'Chủ trại / Quản lý chuồng trại (Breeder Owner / Kennel Manager)',
    'Huấn luyện viên trưởng / Quản lý cơ sở (Head Trainer / Facility Director)',
    'Giám đốc Tiếp nhận / Điều phối Cứu trợ (Shelter Intake Director)'
}

GENERIC_EMAIL_PREFIXES = {
    'info', 'contact', 'hello', 'support', 'sales', 'admin', 'team',
    'office', 'inquiries', 'help', 'service', 'grooming', 'webmaster',
    ' adopt', 'adoption', 'rescue', 'kennel', 'puppies', 'doodles'
}

# 2. Hàm mã hóa số điện thoại theo đúng chuẩn ảnh mẫu (电话)
def encode_phone(val, fb_url=''):
    if pd.isna(val):
        return ''
    s = str(val).strip()
    # Bỏ qua nếu bị lỗi ký hiệu khoa học của FB UID (ví dụ 6.1578E+13)
    if 'E+' in s or 'e+' in s:
        return ''
    parts = [p.strip() for p in s.split('|')]
    for p in parts:
        digits = re.sub(r'\D', '', p)
        # Loại bỏ các dãy số là UID Facebook (14-16 số bắt đầu bằng 1000, 615...) bị lẫn vào cột Phone
        if len(digits) >= 13 and (digits.startswith('1000') or digits.startswith('615') or digits in str(fb_url)):
            continue
        # Ưu tiên số chuẩn Mỹ (10 số hoặc 11 số bắt đầu bằng 1)
        if len(digits) in (10, 11):
            return digits
        elif 9 <= len(digits) <= 12:
            return digits
    return ''

# 3. Hàm trích xuất fb_id (ưu tiên Numeric ID, sau đó đến Username/Slug)
def extract_fb_id(row):
    fb_url = str(row['Facebook URL']) if pd.notna(row['Facebook URL']) else ''
    phone = str(row['Điện Thoại / Phone']) if pd.notna(row['Điện Thoại / Phone']) else ''
    
    # Tìm chuỗi UID 10-16 chữ số trong URL Facebook
    m_id = re.findall(r'(?:id=|/|-|;)(\d{10,16})(?:/|$|\?|&|;)', fb_url)
    if m_id:
        return re.sub(r'\.0+$', '', str(m_id[0]))
    
    # Kiểm tra xem UID Facebook có bị lẫn trong cột Phone không
    p_ids = re.findall(r'\b(1000\d{10,12}|615\d{11,12})\b', phone)
    if p_ids:
        return re.sub(r'\.0+$', '', str(p_ids[0]))
        
    # Lấy Username/Slug từ URL Facebook
    if 'facebook.com' in fb_url or 'fb.com' in fb_url:
        urls = [u.strip() for u in re.split(r'[;|]', fb_url) if 'facebook.com' in u or 'fb.com' in u]
        for u in urls:
            m_slug = re.search(r'(?:facebook\.com|fb\.com)/(?:people/[^/]+/|pages/[^/]+/|pg/)?([^/?&#;]+)', u)
            if m_slug:
                slug = m_slug.group(1)
                if slug.lower() not in {'profile.php', 'people', 'pages', 'pg', 'tab', 'friends', 'p', 'groups', 'share', 'wix'}:
                    return re.sub(r'\.0+$', '', slug)
    return ''

POPULAR_US_FIRST_NAMES = {
    'amanda', 'lisa', 'john', 'sarah', 'michael', 'david', 'james', 'robert',
    'william', 'mary', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
    'jessica', 'karen', 'ashley', 'emily', 'donna', 'michelle', 'carol', 'amy'
}

# 4. Hàm suy luận & điền tên Chủ Sở Hữu (Owner) từ Email, Tên trại, Ghi chú Phone & FB URL
def infer_owner(row):
    current_owner = str(row['Chủ Sở Hữu / Đại Diện (Owner)']).strip()
    if current_owner not in GENERIC_OWNERS and pd.notna(row['Chủ Sở Hữu / Đại Diện (Owner)']) and len(current_owner) >= 2:
        return current_owner
        
    phone_raw = str(row['Điện Thoại / Phone']) if pd.notna(row['Điện Thoại / Phone']) else ''
    email_raw = str(row['Email']) if pd.notna(row['Email']) else ''
    breeder_name = str(row['Tên Đối Tác / Breeder Name']) if pd.notna(row['Tên Đối Tác / Breeder Name']) else ''
    fb_url = str(row['Facebook URL']) if pd.notna(row['Facebook URL']) else ''

    # Cách 1: Tìm tên người đi kèm trong cột Phone (VD: "Linda 217-855-9075")
    m_phone_name = re.search(r'\b([A-Z][a-z]{2,15})\s+\d{3}[-.\s]\d{3}', phone_raw)
    if m_phone_name and m_phone_name.group(1).lower() not in {'tel', 'usa', 'ext'}:
        return m_phone_name.group(1)

    # Cách 2: Kiểm tra sở hữu cách trong Tên Đối Tác (VD: "Bella's Golden Doodles" -> "Bella")
    m_possessive = re.search(r"^([A-Z][a-zA-Z]+)(?:'s|’s)\b", breeder_name)
    if m_possessive and m_possessive.group(1).lower() not in {'oregon', 'california', 'america', 'nature', 'farmer', 'texas'}:
        return m_possessive.group(1)

    # Cách 3: Kiểm tra tiền tố Email theo quy tắc thông minh (VD: "amandabexleyab@gmail.com" -> "Amanda Bexley")
    if email_raw:
        first_email = email_raw.split('|')[0].strip()
        prefix, _, domain = first_email.partition('@')
        user_part = re.sub(r'^[\d\-_]+|[\d\-_]+$', '', prefix)
        domain_base = domain.split('.')[0].lower()
        
        if user_part.lower() not in GENERIC_EMAIL_PREFIXES and user_part.lower() != domain_base:
            # 3.1 Dạng firstname.lastname hoặc firstname_lastname
            m_dot = re.match(r'^([a-zA-Z]+)[._]([a-zA-Z]+)$', user_part)
            if m_dot:
                return f"{m_dot.group(1).capitalize()} {m_dot.group(2).capitalize()}"
            
            # 3.2 Dạng ghép tên như amandabexleyab -> Amanda Bexley
            lower_u = user_part.lower()
            for fn in POPULAR_US_FIRST_NAMES:
                if lower_u.startswith(fn) and len(lower_u) > len(fn):
                    rest = lower_u[len(fn):]
                    rest_clean = re.sub(r'(\d+|[a-z]{1,2})$', '', rest)
                    if len(rest_clean) >= 3:
                        return f"{fn.capitalize()} {rest_clean.capitalize()}"
                    elif len(rest) >= 3:
                        return f"{fn.capitalize()} {rest.capitalize()}"
                    else:
                        return fn.capitalize()

            # 3.3 Tách từ chung
            clean_words = re.sub(r'[\d_-]+', ' ', user_part).strip()
            clean_words = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_words)
            words = clean_words.split()
            if words and len(words[0]) >= 3:
                return ' '.join(w.capitalize() for w in words)

    # Cách 4: Kiểm tra URL Facebook cá nhân (VD: facebook.com/ankit.chhibber.90)
    m_fb_person = re.search(r'facebook\.com/([a-z]{3,15})\.([a-z]{3,15})(?:\.\d+)?/?$', fb_url, re.I)
    if m_fb_person:
        w1, w2 = m_fb_person.group(1).lower(), m_fb_person.group(2).lower()
        business_words = {'kennel', 'kennels', 'doodle', 'doodles', 'bulldog', 'bulldogs', 'frenchie', 'frenchies', 'farm', 'farms', 'ranch', 'puppies', 'puppy', 'labs', 'labradors', 'retrievers', 'corgis', 'k9'}
        if w1 not in business_words and w2 not in business_words:
            return f"{w1.capitalize()} {w2.capitalize()}"

    # Cách 5: Fallback về Tên Đối Tác / Facebook (Tuyệt đối không dùng generic)
    if breeder_name and breeder_name.strip() and breeder_name != 'Unknown Breeder':
        return breeder_name.strip()

    return 'Kennel Owner'

# 5. Hàm đào sâu Online (Vibe Code Deep Scraper) lấy Numeric FB_ID, Phone & Owner từ Web/FB
def scrape_online_details(fb_url, website_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}):
    found_fb_id, found_phone, found_owner = None, None, None
    # Quét Facebook Page source để lấy Numeric page_id / userID
    if fb_url and 'facebook.com' in fb_url:
        try:
            r = requests.get(fb_url.split(';')[0].split('|')[0].strip(), headers=headers, timeout=8)
            if r.status_code == 200:
                m_uid = re.search(r'"(?:userID|pageID|entity_id)"\s*:\s*"(\d{10,16})"', r.text)
                if m_uid:
                    found_fb_id = m_uid.group(1)
        except Exception:
            pass
            
    # Quét Website (Home, About, Our Story, Meet Breeder, Contact)
    if website_url and 'http' in website_url:
        base_url = website_url.split('|')[0].strip()
        paths = ['', '/about', '/about/', '/about-us', '/our-story', '/meet-the-breeder', '/contact', '/contact-us']
        for path in paths:
            try:
                target = base_url.rstrip('/') + path if path else base_url
                r = requests.get(target, headers=headers, timeout=8)
                if r.status_code == 200:
                    html_text = r.text
                    soup = BeautifulSoup(html_text, 'html.parser')
                    text = soup.get_text(' ', strip=True)

                    if not found_phone:
                        m_ph = re.search(r'(?:\+?1[\s.-]?)?\(?([2-9]\d{2})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b', text)
                        if m_ph:
                            found_phone = f"1{m_ph.group(1)}{m_ph.group(2)}{m_ph.group(3)}"

                    if not found_owner:
                        # 1. Good Dog Profile
                        m_gd = re.search(r'breederFullName:\s*[\'"]([^\'"]+)[\'"]', html_text, re.I) or \
                               re.search(r'<h[1-6][^>]*>([A-Z][a-z]+(?:\s+[A-Z]\.?)?)<\/h[1-6]>\s*<p[^>]*>Breeder of', html_text, re.I)
                        if m_gd:
                            found_owner = m_gd.group(1).strip()

                        # 2. Image alt: alt="Amanda Bexley, breeder and founder..."
                        if not found_owner:
                            for img in soup.find_all('img', alt=True):
                                alt = img['alt'].strip()
                                m_alt = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(?:breeder|founder|owner|head breeder)', alt, re.I)
                                if m_alt and not re.search(r'cavapoo|puppy|doodle|terrier|dog|kennel|farm', m_alt.group(1), re.I):
                                    found_owner = m_alt.group(1).strip()
                                    break

                        # 3. Headings "Meet Amanda Bexley."
                        if not found_owner:
                            for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                                h_txt = h.get_text(' ', strip=True)
                                m_h = re.search(r'Meet\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', h_txt, re.I)
                                if m_h and not re.search(r'cavapoo|puppy|doodle|terrier|dog|kennel|farm|parents|mamas|studs', m_h.group(1), re.I):
                                    found_owner = m_h.group(1).strip()
                                    break

                        # 4. Text "[Name] is the breeder and founder..."
                        if not found_owner:
                            m_is = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+is the (?:breeder|founder|owner|head breeder)', text)
                            if m_is and not re.search(r'cavapoo|puppy|doodle|terrier|dog|kennel|farm', m_is.group(1), re.I):
                                found_owner = m_is.group(1).strip()

                        # 5. Form / waitlist direct name
                        if not found_owner:
                            m_cf = re.search(r'(?:sent directly to|Contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:for|via|directly)', text)
                            if m_cf and not re.search(r'us|me|support|office|admin', m_cf.group(1), re.I):
                                found_owner = m_cf.group(1).strip()

                    if found_phone and found_owner:
                        break
            except Exception:
                continue
    return found_fb_id, found_phone, found_owner

# Áp dụng xử lý lên toàn bộ DataFrame
df['fb_id'] = df.apply(extract_fb_id, axis=1)
df['电话 (Phone Mã Hóa)'] = df.apply(lambda r: encode_phone(r['Điện Thoại / Phone'], r['Facebook URL']), axis=1)
df['Chủ Sở Hữu / Đại Diện (Owner)'] = df.apply(infer_owner, axis=1)

# Điền khuyết Tên Đối Tác nếu bị trống dựa trên FB Slug hoặc Domain Email
def fill_breeder_name(row):
    if pd.notna(row['Tên Đối Tác / Breeder Name']):
        return row['Tên Đối Tác / Breeder Name']
    if row['fb_id'] and not str(row['fb_id']).isdigit():
        return row['fb_id']
    if pd.notna(row['Email']):
        return str(row['Email']).split('@')[0]
    return 'Unknown Breeder'

df['Tên Đối Tác / Breeder Name'] = df.apply(fill_breeder_name, axis=1)

# Xếp hạng theo Điểm Chuẩn (Score) giảm dần
df = df.sort_values(by=['Điểm Chuẩn (Score)', 'STT / Mã'], ascending=[False, True]).reset_index(drop=True)

# 6. Xuất ra file Excel chuẩn: chia thành các bảng, mỗi bảng đúng 20 người dùng
output_path = 'Bao_Cao_Khach_Hang_Chuan_Hoa_20_User_Moi_Bang.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # Sheet 1: Tổng hợp chia theo từng cụm 20 người dùng ngăn cách rõ ràng
    chunks = []
    for i in range(0, len(df), 20):
        chunk = df.iloc[i:i+20].copy()
        chunk.insert(0, 'Hạng (Rank 1-20)', range(1, len(chunk) + 1))
        chunk.insert(0, 'Bảng Số', f'Bảng {(i//20) + 1} (User {i+1} - {min(i+20, len(df))})')
        chunks.append(chunk)
    
    final_df = pd.concat(chunks, ignore_index=True)
    final_df.to_excel(writer, sheet_name='Tat_Ca_Bang_20_User', index=False)

print(f"Đã xuất thành công {len(df)} khách hàng thành {(len(df)+19)//20} bảng (mỗi bảng 20 người dùng)!")