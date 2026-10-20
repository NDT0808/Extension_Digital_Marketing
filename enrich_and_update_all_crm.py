import os
import re
import json
import pandas as pd

# Paths
WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
CRM_CSV = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM_2026-10-15.csv")
RAG_EXCEL = os.path.join(WORKSPACE, "US_Hot_Leads_With_Owner_Representative.xlsx")
PAGES_EXCEL = os.path.join(WORKSPACE, "Datasets", "fb_pages_merged.xlsx")
TELE_CSV = os.path.join(WORKSPACE, "Datasets", "telesale_leads_clean.csv")
JSON_RAG_EXT = os.path.join(WORKSPACE, "fb_following_scraper", "rag_breeder_db.json")

print("[*] 1. Khởi động pipeline hợp nhất dữ liệu từ 3 nguồn tri thức lớn...")

US_STATES = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
    'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
    'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
    'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
    'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
}
US_STATE_CODES = set(US_STATES.values())

DOG_KEYWORDS = [
    'cavapoo', 'cavapoos', 'maltipoo', 'maltipoos', 'yorkipoo', 'yorkipoos', 'cockapoo', 'cockapoos',
    'schnoodle', 'bernedoodle', 'bernedoodles', 'aussiedoodle', 'aussiedoodles', 'goldendoodle', 'goldendoodles',
    'labradoodle', 'labradoodles', 'doodle', 'doodles', 'poo', 'yorkie', 'yorkies', 'schnauzer',
    'corgi', 'corgis', 'frenchie', 'frenchies', 'french bulldog', 'bulldog', 'bulldogs', 'chihuahua',
    'dachshund', 'dachshunds', 'wiener', 'doxie', 'retriever', 'retrievers', 'golden', 'goldens',
    'labrador', 'labradors', 'shepherd', 'shepherds', 'malinois', 'beagle', 'boxer', 'rottweiler',
    'doberman', 'mastiff', 'cane corso', 'corso', 'pitbull', 'bully', 'bullies', 'staffy', 'terrier',
    'shih tzu', 'shihtzu', 'maltese', 'bichon', 'havanese', 'pomeranian', 'pom', 'spitz', 'husky',
    'samoyed', 'malamute', 'shiba', 'akita', 'pug', 'hound', 'basset', 'spaniel', 'collie', 'aussie',
    'pyrenees', 'schipperke', 'brittany', 'kennel', 'kennels', 'breeder', 'breeders', 'breeding',
    'puppy', 'puppies', 'pup', 'pups', 'litter', 'stud', 'canine', 'k9', 'k-9', 'bark', 'woof',
    'snout', 'paw', 'paws', 'doggo', 'house of', 'adestrador', 'trainer', 'training', 'grooming',
    'pet', 'pets', 'pet grass', 'potty', 'dog toy', 'chó', 'cún', 'trại chó', 'nhân giống'
]

def clean_fb_key(u):
    if not u or not isinstance(u, str): return ''
    u = u.lower().strip()
    u = re.sub(r'https?://(?:www\.|m\.)?facebook\.com/', '', u)
    u = re.sub(r'[?&].*$', '', u)
    return u.strip('/')

def clean_name_key(n):
    if not n or not isinstance(n, str): return ''
    n = n.lower().replace('&', 'and')
    return re.sub(r'[^a-z0-9]', '', n)

def clean_phone(p):
    if not p or not isinstance(p, str): return ''
    digits = re.sub(r'\D', '', p)
    if len(digits) == 10:
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) >= 7:
        return p.strip()
    return ''

def clean_email(e):
    if not e or not isinstance(e, str): return ''
    candidates = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', e)
    for c in candidates:
        c_low = c.lower().strip()
        if not any(bad in c_low for bad in ['facebook.com', 'meta.com', 'instagram.com', 'schema.org', 'example.com', '.png', '.jpg', '.js']):
            return c_low
    return ''

def clean_website(w):
    if not w or not isinstance(w, str): return ''
    w = w.strip()
    # Tách nếu bị nối bởi |
    parts = [p.strip() for p in w.split('|')]
    for p in parts:
        if 'mailto:' in p.lower() or 'where1=' in p.lower() or 'bing.com' in p.lower() or 'google.com/maps' in p.lower():
            continue
        # Bỏ facebook, instagram
        if 'facebook.com' in p.lower() or 'instagram.com' in p.lower() or 'static.xx' in p.lower() or 'rsrc' in p.lower():
            continue
        p = re.sub(r'[?&]fbclid=.*$', '', p)
        if re.search(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', p) or p.startswith('http'):
            if not p.startswith('http'): p = 'https://' + p
            return p.strip('/')
    return ''

def extract_city_state(text, where_str=''):
    city = ''
    state = ''
    zip_code = ''
    
    cand = where_str or text
    if cand:
        m_where = re.search(r'where1=([^&"\']+)', cand)
        if m_where:
            cand = m_where.group(1).replace('%20', ' ').replace('+', ' ')
        
        # Check ZIP
        m_zip = re.search(r'\b(\d{5})(?:-\d{4})?\b', cand)
        if m_zip and not m_zip.group(1).startswith('00000'):
            zip_code = m_zip.group(1)
            
        # Check State
        parts = [p.strip() for p in cand.split(',')]
        for p in parts:
            m_st = re.search(r'\b([A-Z]{2})\b', p)
            if m_st and m_st.group(1) in US_STATE_CODES:
                state = m_st.group(1)
                break
            for sname, scode in US_STATES.items():
                if sname in p.lower():
                    state = scode
                    break
            if state: break
            
        if len(parts) >= 2 and not city:
            c_cand = parts[0].strip()
            if len(c_cand) > 1 and not any(bad in c_cand.lower() for bad in ['facebook', 'united states', 'http', 'page']):
                city = c_cand

    return city, state, zip_code

# Đọc các file dữ liệu
df_rag = pd.read_excel(RAG_EXCEL, dtype=str).fillna('')
df_pages = pd.read_excel(PAGES_EXCEL, dtype=str).fillna('')
df_tele = pd.read_csv(TELE_CSV, dtype=str).fillna('')

master_db = {}

def insert_db(key, data):
    if not key: return
    if key not in master_db:
        master_db[key] = data
    else:
        # Merge, ưu tiên trường có giá trị
        for k, v in data.items():
            if v and not master_db[key].get(k):
                master_db[key][k] = v

print("[*] 2. Nạp dữ liệu từ fb_pages_merged.xlsx...")
for _, r in df_pages.iterrows():
    u1 = clean_fb_key(r.get('Link gốc', ''))
    u2 = clean_fb_key(r.get('Link cuối', ''))
    name = r.get('Tên', '').strip()
    nk = clean_name_key(name)
    
    web = clean_website(r.get('Website', ''))
    em = clean_email(r.get('Email', ''))
    ph = clean_phone(r.get('Điện thoại', ''))
    ig = r.get('Instagram', '').strip()
    intro = r.get('Giới thiệu', '').strip()
    c, s, z = extract_city_state(intro, r.get('Website', ''))
    
    entry = {
        'name': name,
        'website': web,
        'email': em,
        'phone': ph,
        'ig_url': ig,
        'city': c,
        'state': s,
        'zip_code': z,
        'intro': intro,
        'owner': '',
        'owner_conf': ''
    }
    insert_db(u1, entry)
    insert_db(u2, entry)
    insert_db(nk, entry)

print("[*] 3. Nạp dữ liệu từ telesale_leads_clean.csv...")
for _, r in df_tele.iterrows():
    u = clean_fb_key(r.get('Facebook', ''))
    name = r.get('Name', '').strip()
    nk = clean_name_key(name)
    
    web = clean_website(r.get('Website', ''))
    em = clean_email(r.get('Emails', ''))
    ph = clean_phone(r.get('Phones', ''))
    ig = r.get('Instagram', '').strip()
    c = r.get('City', '').strip()
    s = r.get('State', '').strip().upper()
    if s not in US_STATE_CODES: s = US_STATES.get(s.lower(), '')
    
    entry = {
        'name': name,
        'website': web,
        'email': em,
        'phone': ph,
        'ig_url': ig,
        'city': c,
        'state': s,
        'zip_code': '',
        'intro': '',
        'owner': '',
        'owner_conf': ''
    }
    insert_db(u, entry)
    insert_db(nk, entry)

print("[*] 4. Nạp dữ liệu từ US_Hot_Leads_With_Owner_Representative.xlsx...")
for _, r in df_rag.iterrows():
    u = clean_fb_key(r.get('Facebook_URL', ''))
    name = r.get('Breeder_Name', '').strip()
    nk = clean_name_key(name)
    
    web = clean_website(r.get('Website', ''))
    em = clean_email(r.get('Email', ''))
    ph = clean_phone(r.get('Phone', ''))
    c = r.get('City', '').strip()
    s = r.get('State', '').strip().upper()
    if s not in US_STATE_CODES: s = US_STATES.get(s.lower(), '')
    z = r.get('Zip_Code', '').strip()
    owner = r.get('Owner_Representative', '').strip()
    owner_conf = r.get('Owner_Confidence', '').strip()
    amz_status = r.get('Amazon_Status', '').strip()
    amz_link = r.get('Amazon_Link', '').strip()
    
    entry = {
        'name': name,
        'website': web,
        'email': em,
        'phone': ph,
        'ig_url': '',
        'city': c,
        'state': s,
        'zip_code': z,
        'intro': '',
        'owner': owner,
        'owner_conf': owner_conf,
        'amz_status': amz_status,
        'amz_link': amz_link
    }
    insert_db(u, entry)
    insert_db(nk, entry)

print(f"[✓] Đã gom {len(master_db)} khóa định danh khách hàng tiềm năng!")

# 5. Đọc và làm giàu GoodDog_Followers_Master_CRM_2026-10-15.csv
print("[*] 5. Đang đọc và làm giàu Master CRM CSV...")
df_crm = pd.read_csv(CRM_CSV, encoding='utf-8-sig', dtype=str).fillna('')

rows_enriched = []

for idx, r in df_crm.iterrows():
    row = dict(r)
    name = row.get('Họ và Tên (Breeder Name)', '').strip()
    fb_url = row.get('Facebook URL', '').strip()
    u_key = clean_fb_key(fb_url)
    n_key = clean_name_key(name)
    
    # Tìm kiếm đối chiếu
    db_match = master_db.get(u_key) or master_db.get(n_key) or {}
    
    # 1. Phone
    cur_phone = clean_phone(row.get('Số Điện Thoại (Phone)', ''))
    db_phone = clean_phone(db_match.get('phone', ''))
    row['Số Điện Thoại (Phone)'] = db_phone or cur_phone
    
    # 2. Email
    cur_email = clean_email(row.get('Email', ''))
    db_email = clean_email(db_match.get('email', ''))
    # Kiểm tra nếu email bị dính trong website
    cur_web_raw = row.get('Website Chính Thức', '')
    if 'mailto:' in cur_web_raw:
        m_em = re.search(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', cur_web_raw)
        if m_em and not cur_email:
            cur_email = m_em.group(1).lower()
    row['Email'] = db_email or cur_email
    
    # 3. Website
    db_web = clean_website(db_match.get('website', ''))
    cur_web = clean_website(cur_web_raw)
    row['Website Chính Thức'] = db_web or cur_web
    
    # 4. Instagram
    cur_ig = row.get('Instagram URL', '').strip()
    db_ig = db_match.get('ig_url', '').strip()
    row['Instagram URL'] = db_ig or cur_ig
    
    # 5. City, State, Zip
    cur_c = row.get('Thành Phố (City)', '').strip()
    cur_s = row.get('Bang (State)', '').strip()
    cur_z = row.get('Mã Zip (Zip Code)', '').strip()
    
    # Check if where1 was in website string
    if 'where1=' in cur_web_raw:
        ext_c, ext_s, ext_z = extract_city_state('', cur_web_raw)
        if ext_c and not cur_c: cur_c = ext_c
        if ext_s and not cur_s: cur_s = ext_s
        if ext_z and not cur_z: cur_z = ext_z
        
    db_c = db_match.get('city', '').strip()
    db_s = db_match.get('state', '').strip()
    db_z = db_match.get('zip_code', '').strip()
    
    final_c = db_c or cur_c
    final_s = db_s or cur_s
    if final_s == 'DE' and not db_s: final_s = '' # Xóa bỏ fake DE
    final_z = db_z or cur_z
    
    row['Thành Phố (City)'] = final_c
    row['Bang (State)'] = final_s
    row['Mã Zip (Zip Code)'] = final_z
    row['Quốc Gia (Country)'] = 'United States'
    
    # 6. Chủ sở hữu (Owner)
    cur_owner = row.get('Chủ Sở Hữu (Owner_Representative)', '').strip()
    cur_owner_conf = row.get('Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)', '').strip()
    db_owner = db_match.get('owner', '').strip()
    db_owner_conf = db_match.get('owner_conf', '').strip()
    
    if db_owner and 'rorState' not in db_owner and 'Breeder Owner' not in db_owner:
        row['Chủ Sở Hữu (Owner_Representative)'] = db_owner
        row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = db_owner_conf or 'Tier 1 - High (Verified Lead)'
    elif 'rorState' in cur_owner:
        # Fallback possessive
        m_poss = re.match(r"^([A-Z][a-z]+(?:'s|’s))\b", name)
        if m_poss:
            row['Chủ Sở Hữu (Owner_Representative)'] = m_poss.group(1).replace("'s", "").replace("’s", "")
            row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium-High (Breeder Possessive Match)'
        else:
            row['Chủ Sở Hữu (Owner_Representative)'] = 'Chủ trại / Quản lý chuồng trại (Breeder Owner / Kennel Manager)'
            row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 4 - Role-Based (Sales Inquire)'
    
    # 7. PHƯƠNG THỨC NHẬN DIỆN (DETECTION METHOD) - TRƯỜNG MỚI THEO YÊU CẦU!
    ai_vision = str(row.get('Kết Quả AI Thị Giác (AI dog-model.onnx)', ''))
    has_ai_dog = ('Chó lớn' in ai_vision or 'Adult Dog' in ai_vision or 'Cún con' in ai_vision or 'Puppy' in ai_vision)
    
    text_corpus = f"{name} {fb_url}".lower()
    has_keyword = any(kw in text_corpus for kw in DOG_KEYWORDS)
    
    if has_ai_dog and has_keyword:
        detection_method = 'Kết hợp (Hình ảnh AI + Từ khóa)'
    elif has_ai_dog:
        detection_method = 'Hình ảnh AI (dog-model.onnx)'
    elif has_keyword:
        detection_method = 'Từ khóa (Keyword Match)'
    elif db_match:
        detection_method = 'Kho tri thức RAG (RAG Ground-Truth)'
    else:
        detection_method = 'Từ khóa (Keyword Match)'
        
    row['Phương Thức Nhận Diện (Detection Method)'] = detection_method

    # 8. Weather Trigger
    cold_snow_states = {'WA', 'OR', 'ID', 'MT', 'WY', 'ND', 'SD', 'MN', 'WI', 'MI', 'IL', 'IN', 'OH', 'PA', 'NY', 'VT', 'NH', 'ME', 'MA', 'CT', 'RI', 'NJ', 'CO', 'AK'}
    hot_sunbelt_states = {'TX', 'FL', 'AZ', 'NV', 'NM', 'GA', 'AL', 'MS', 'LA', 'SC'}
    
    st_up = final_s.upper()
    c_low = final_c.lower()
    if st_up in cold_snow_states or any(x in c_low for x in ['seattle', 'portland', 'chicago', 'detroit', 'minneapolis', 'buffalo', 'denver']):
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 1 (Mưa/Tuyết/Lạnh giá): Đẩy mạnh Thảm cỏ thoát nước + Khay vệ sinh trong nhà (Tránh cún ướt chân, bẩn sàn)'
    elif st_up in hot_sunbelt_states or any(x in c_low for x in ['phoenix', 'las vegas', 'miami', 'houston', 'dallas', 'orlando']):
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 1 (Nắng gắt mặt đường >90°F): Đẩy mạnh Cỏ nhân tạo làm mát + Khay Potty ban công (Tránh cún bỏng đệm chân)'
    elif st_up or c_low:
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 2 (Chó cuồng chân nhốt trong nhà): Chào Combo Đồ chơi ngứa răng Chew Toy + Snuggle Puppy xoa dịu stress'
    else:
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 3 (Khí hậu biến động): Chào trọn gói Take-Home Starter Kit V2/V3 (Giải pháp vệ sinh + đồ chơi toàn diện)'
        
    # 9. Lead Score
    rec_score = int(row.get('Điểm Recency (0-35)', 15) or 15)
    score_infra = (5 if row['Website Chính Thức'] else 0) + 5
    score_amz = 15 if 'TARGET' in str(row.get('Kênh Bán Amazon (Amazon Status)', '')) else 0
    total_score = min(100, rec_score + 28 + 15 + score_infra + score_amz)
    row['Tổng Điểm Lead Score (0-100)'] = str(total_score)
    
    if total_score >= 85:
        row['Phân Hạng Đối Tác (Tier Rank)'] = 'Tier S (Kim Cương)'
        row['Hành Động Sales'] = 'Gọi điện chốt hợp đồng ngay trong ngày + Chào Take-Home Kit V2/V3'
    elif total_score >= 70:
        row['Phân Hạng Đối Tác (Tier Rank)'] = 'Tier A (Vàng)'
        row['Hành Động Sales'] = 'Ưu tiên gọi điện trong 24h + Email chào hàng Starter Kit'
    elif total_score < 50:
        row['Phân Hạng Đối Tác (Tier Rank)'] = 'Tier C (Đồng)'
        row['Hành Động Sales'] = 'Tiếp cận chi phí thấp qua Facebook/Instagram'
    else:
        row['Phân Hạng Đối Tác (Tier Rank)'] = 'Tier B (Bạc)'
        row['Hành Động Sales'] = 'Chuỗi email marketing tự động nuôi dưỡng + Nhắn tin Fanpage'

    rows_enriched.append(row)

# Tạo DataFrame mới 34 cột chuẩn hóa
ORDERED_34_COLS = [
    'STT',
    'Master_ID',
    'FB_ID',
    'Họ và Tên (Breeder Name)',
    'Phương Thức Nhận Diện (Detection Method)',
    'Chủ Sở Hữu (Owner_Representative)',
    'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)',
    'Số Điện Thoại (Phone)',
    'Email',
    'Website Chính Thức',
    'Facebook URL',
    'Instagram URL',
    'Địa Chỉ (Address)',
    'Thành Phố (City)',
    'Bang (State)',
    'Mã Zip (Zip Code)',
    'Quốc Gia (Country)',
    'Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)',
    'Kết Quả AI Thị Giác (AI dog-model.onnx)',
    'Kênh Bán Amazon (Amazon Status)',
    'Link Amazon',
    'Thời Gian Đăng Bài Gần Nhất',
    'Thời Gian Tương Đối',
    'Độ Tươi Mới (Recency Tier)',
    'Điểm Recency (0-35)',
    'Tổng Điểm Lead Score (0-100)',
    'Phân Hạng Đối Tác (Tier Rank)',
    'Lượt Cảm Xúc',
    'Số Bình Luận',
    'Phân Khúc Khách Hàng (ICP)',
    'Sản Phẩm Đề Xuất',
    'Hành Động Sales',
    'Nguồn Dữ Liệu',
    'Avatar URL'
]

df_out = pd.DataFrame(rows_enriched)
# Đảm bảo đủ các cột
for c in ORDERED_34_COLS:
    if c not in df_out.columns:
        df_out[c] = ''

df_out = df_out[ORDERED_34_COLS]

# Lưu CSV với UTF-8 BOM
df_out.to_csv(CRM_CSV, index=False, encoding='utf-8-sig')
print(f"[✓] Đã ghi thành công file CSV Master CRM 34 cột: {CRM_CSV}")
print(f"    - Tổng số dòng: {len(df_out)}")
print(f"    - Số email có dữ liệu: {(df_out['Email'] != '').sum()}")
print(f"    - Số phone có dữ liệu: {(df_out['Số Điện Thoại (Phone)'] != '').sum()}")
print(f"    - Số website có dữ liệu: {(df_out['Website Chính Thức'] != '').sum()}")
print(f"    - Số bang có dữ liệu: {(df_out['Bang (State)'] != '').sum()}")
print(f"    - Phân bố Phương Thức Nhận Diện:\n{df_out['Phương Thức Nhận Diện (Detection Method)'].value_counts()}")

# 6. Cập nhật RAG breeder db json cho tiện ích mở rộng Chrome
print("[*] 6. Đang cập nhật rag_breeder_db.json cho Extension...")
with open(JSON_RAG_EXT, 'w', encoding='utf-8') as f:
    json.dump(master_db, f, ensure_ascii=False, indent=2)
print(f"[✓] Đã cập nhật {JSON_RAG_EXT} ({len(master_db)} đối tác)!")
