import os
import re
import json
import pandas as pd

WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
CRM_CSV = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM_2026-10-15.csv")
RAG_EXCEL = os.path.join(WORKSPACE, "US_Hot_Leads_With_Owner_Representative.xlsx")
PAGES_EXCEL = os.path.join(WORKSPACE, "Datasets", "fb_pages_merged.xlsx")
TELE_CSV = os.path.join(WORKSPACE, "Datasets", "telesale_leads_clean.csv")
JSON_RAG_EXT = os.path.join(WORKSPACE, "fb_following_scraper", "rag_breeder_db.json")

print("[*] 1. Khởi động sửa tận gốc lỗi trùng lặp dữ liệu & làm giàu chuẩn hóa...")

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

POPULAR_US_NAMES = set([
    'javin', 'tanya', 'sarah', 'tammy', 'hillarie', 'holly', 'matt', 'melissa', 'james', 'denise',
    'gonzalo', 'wendy', 'brian', 'kayla', 'nicole', 'hannah', 'michelle', 'julian', 'sheryl', 'amy',
    'margie', 'trevor', 'christy', 'elizabeth', 'wayne', 'erin', 'jessica', 'katherine', 'jodi',
    'julia', 'paula', 'kelly', 'mandy', 'angela', 'peggy', 'patrick', 'sara', 'polly', 'bray',
    'laurell', 'grace', 'danny', 'heather', 'autumn', 'dan', 'robert', 'chelsea', 'darla', 'charles',
    'linda', 'miranda', 'tabitha', 'cassandra', 'travis', 'lisa', 'andrew', 'shari', 'ryan', 'scott',
    'joan', 'chase', 'darcy', 'rachael', 'karen', 'theresa', 'mary', 'shannon', 'daryl', 'helen',
    'jennifer', 'megan', 'jason', 'trina', 'donna', 'sherry', 'loretta', 'daria', 'lori', 'abby',
    'sharon', 'dave', 'david', 'mark', 'john', 'mike', 'michael', 'chris', 'amanda', 'steve', 'steven',
    'tom', 'katie', 'ashley', 'brittany', 'rachel', 'laura', 'daniel', 'kevin', 'eric', 'adam', 'justin',
    'gonzalez', 'wilson', 'stacy', 'hattie', 'frankline', 'franklin', 'polly', 'bray', 'casey'
])

def clean_fb_key(u):
    if not u or not isinstance(u, str): return ''
    u = u.strip().lower()
    m_id = re.search(r'[?&]id=(\d+)', u)
    if m_id:
        return m_id.group(1)
    m_people = re.search(r'people/[^/]+/(\d+)', u)
    if m_people:
        return m_people.group(1)
    u = re.sub(r'https?://(?:www\.|m\.)?facebook\.com/', '', u)
    u = re.sub(r'[?&].*$', '', u)
    u = u.strip('/')
    if u in ['profile.php', 'people', 'pages', 'groups', 'watch', 'marketplace', '']:
        return ''
    return u

def clean_name_key(n):
    if not n or not isinstance(n, str): return ''
    n = n.lower().replace('&', 'and')
    n = re.sub(r'[^a-z0-9]', '', n)
    if len(n) < 4 or n in ['facebook', 'breeder', 'puppy', 'kennel', 'dog']:
        return ''
    return n

def clean_phone(p):
    if not p or not isinstance(p, str): return ''
    # Bỏ các số test lặp của Paul
    if '860-564-8733' in p or '8605648733' in p: return ''
    digits = re.sub(r'\D', '', p)
    if len(digits) == 10 or (len(digits) == 11 and digits.startswith('1')):
        return digits
    elif len(digits) >= 7:
        return digits
    return ''

def clean_email(e):
    if not e or not isinstance(e, str): return ''
    # Bỏ email rác lặp
    if 'pauldesrochers.46@gmail.com' in e.lower(): return ''
    candidates = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', e)
    for c in candidates:
        c_low = c.lower().strip()
        if not any(bad in c_low for bad in ['facebook.com', 'meta.com', 'instagram.com', 'schema.org', 'example.com', '.png', '.jpg', '.js']):
            return c_low
    return ''

def clean_website(w):
    if not w or not isinstance(w, str): return ''
    # Bỏ web rác lặp
    if 'abulldoggepurpose.com' in w.lower(): return ''
    w = w.strip()
    parts = [p.strip() for p in w.split('|')]
    for p in parts:
        if any(bad in p.lower() for bad in ['mailto:', 'where1=', 'bing.com', 'google.com/maps', 'facebook.com', 'instagram.com', 'static.xx', 'rsrc']):
            continue
        p = re.sub(r'[?&]fbclid=.*$', '', p)
        if re.search(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', p) or p.startswith('http'):
            if not p.startswith('http'): p = 'https://' + p
            return p.strip('/')
    return ''

# Xây dựng Master DB sạch
master_db = {}

def insert_db(key, data):
    if not key or key in ['profile.php', 'facebook.com', '']: return
    if key not in master_db:
        master_db[key] = data
    else:
        for k, v in data.items():
            if v and not master_db[key].get(k):
                master_db[key][k] = v

print("[*] 2. Nạp dữ liệu đối chiếu chuẩn từ 3 nguồn...")

# Nguồn 1: US_Hot_Leads_With_Owner_Representative.xlsx (3,324 verified leads)
df_rag = pd.read_excel(RAG_EXCEL, dtype=str).fillna('')
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
        'owner': owner,
        'owner_conf': owner_conf,
        'amz_status': amz_status,
        'amz_link': amz_link
    }
    insert_db(u, entry)
    insert_db(nk, entry)

# Nguồn 2: fb_pages_merged.xlsx
df_pages = pd.read_excel(PAGES_EXCEL, dtype=str).fillna('')
for _, r in df_pages.iterrows():
    u1 = clean_fb_key(r.get('Link gốc', ''))
    u2 = clean_fb_key(r.get('Link cuối', ''))
    name = r.get('Tên', '').strip()
    nk = clean_name_key(name)
    
    web = clean_website(r.get('Website', ''))
    em = clean_email(r.get('Email', ''))
    ph = clean_phone(r.get('Điện thoại', ''))
    ig = r.get('Instagram', '').strip()
    
    entry = {
        'name': name,
        'website': web,
        'email': em,
        'phone': ph,
        'ig_url': ig,
        'city': '',
        'state': '',
        'zip_code': '',
        'owner': '',
        'owner_conf': ''
    }
    insert_db(u1, entry)
    insert_db(u2, entry)
    insert_db(nk, entry)

print(f"[✓] Đã tạo Master DB sạch với {len(master_db)} khóa định danh (ĐÃ XÓA TRIỆT ĐỂ profile.php).")

# 3. Làm giàu và làm sạch 1.059 leads CRM
print("[*] 3. Đang xử lý làm sạch 1.059 dòng trong GoodDog_Followers_Master_CRM_2026-10-15.csv...")
df_crm = pd.read_csv(CRM_CSV, encoding='utf-8-sig', dtype=str).fillna('')

rows_cleaned = []

for idx, r in df_crm.iterrows():
    row = dict(r)
    name = row.get('Họ và Tên (Breeder Name)', '').strip()
    fb_url = row.get('Facebook URL', '').strip()
    fb_id = str(row.get('FB_ID', '')).strip()
    
    u_key = clean_fb_key(fb_url) or clean_fb_key(fb_id)
    n_key = clean_name_key(name)
    
    # Tìm kiếm đối chiếu an toàn
    db_match = master_db.get(u_key) or master_db.get(n_key) or {}

    # XỬ LÝ ĐẶC BIỆT CHO ROLEEZ YORKIES (Theo minh chứng người dùng chụp)
    if 'roleez' in name.lower() or '61576157853580' in fb_url or fb_id == '61576157853580':
        row['Họ và Tên (Breeder Name)'] = 'Roleez Yorkies'
        row['Chủ Sở Hữu (Owner_Representative)'] = 'Lisa Z.'
        row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 1 - High (Good Dog Verified Breeder)'
        row['Số Điện Thoại (Phone)'] = '14133173410'
        row['Email'] = 'roleezyorkies@gmail.com'
        row['Website Chính Thức'] = 'https://my.gooddog.com/roleez-yorkies-massachusetts'
        row['Instagram URL'] = 'https://www.instagram.com/roleezyorkies/'
        row['Thành Phố (City)'] = 'Wilbraham'
        row['Bang (State)'] = 'MA'
        row['Mã Zip (Zip Code)'] = '01095'
        row['Quốc Gia (Country)'] = 'United States'
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 1 (Mưa/Tuyết/Lạnh giá): Đẩy mạnh Thảm cỏ thoát nước + Khay vệ sinh trong nhà (Tránh cún ướt chân, bẩn sàn)'
        row['Tổng Điểm Lead Score (0-100)'] = '92'
        row['Phân Hạng Đối Tác (Tier Rank)'] = 'Tier S (Kim Cương)'
        row['Hành Động Sales'] = 'Gọi điện chốt hợp đồng ngay trong ngày + Chào Take-Home Kit V2/V3'
        row['Phương Thức Nhận Diện (Detection Method)'] = 'Kết hợp (Hình ảnh AI + Từ khóa)'
        rows_cleaned.append(row)
        continue

    # 1. Phone
    cur_ph = row.get('Số Điện Thoại (Phone)', '').strip()
    clean_p = clean_phone(cur_ph)
    db_p = clean_phone(db_match.get('phone', ''))
    row['Số Điện Thoại (Phone)'] = db_p or clean_p

    # 2. Email
    cur_em = row.get('Email', '').strip()
    clean_e = clean_email(cur_em)
    db_e = clean_email(db_match.get('email', ''))
    row['Email'] = db_e or clean_e

    # 3. Website
    cur_web = row.get('Website Chính Thức', '').strip()
    clean_w = clean_website(cur_web)
    db_w = clean_website(db_match.get('website', ''))
    row['Website Chính Thức'] = db_w or clean_w

    # 4. Instagram
    cur_ig = row.get('Instagram URL', '').strip()
    if 'instagram.com/gmail.com' in cur_ig: cur_ig = ''
    db_ig = db_match.get('ig_url', '').strip()
    row['Instagram URL'] = db_ig or cur_ig

    # 5. City, State, Zip
    cur_c = row.get('Thành Phố (City)', '').strip()
    if '18th Century Purity Farms' in cur_c: cur_c = ''
    cur_s = row.get('Bang (State)', '').strip()
    if cur_s in ['DE', 'AL'] and 'Purity' in row.get('Thành Phố (City)', ''): cur_s = ''
    cur_z = row.get('Mã Zip (Zip Code)', '').strip()
    if cur_z == '91307' and 'Purity' in row.get('Thành Phố (City)', ''): cur_z = ''

    db_c = db_match.get('city', '').strip()
    db_s = db_match.get('state', '').strip()
    db_z = db_match.get('zip_code', '').strip()

    row['Thành Phố (City)'] = db_c or cur_c
    row['Bang (State)'] = db_s or cur_s
    row['Mã Zip (Zip Code)'] = db_z or cur_z
    row['Quốc Gia (Country)'] = 'United States'

    # 6. Chủ sở hữu (Owner Representative) giải quyết triệt để theo luật người dùng!
    db_owner = db_match.get('owner', '').strip()
    db_owner_conf = db_match.get('owner_conf', '').strip()

    if db_owner and not any(bad in db_owner.lower() for bad in ['rorstate', 'breeder owner', 'chủ trại']):
        row['Chủ Sở Hữu (Owner_Representative)'] = db_owner
        row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = db_owner_conf or 'Tier 1 - High (Verified Lead)'
    else:
        # Luật 1: Tên sở hữu cách trong tên trại (Ví dụ: Hattie's Texas Cavapoos -> Hattie)
        m_poss = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:'s|’s)\b", name)
        if m_poss and not re.search(r'kennel|puppy|farm|bulldog|frenchie|corgi|doodle', m_poss.group(1), re.I):
            row['Chủ Sở Hữu (Owner_Representative)'] = m_poss.group(1).strip()
            row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium-High (Breeder Possessive Match)'
        # Luật 2: Tên người phổ biến đầu tên trại (Ví dụ: Gonzalez Bulldog -> Gonzalez)
        elif name.split()[0].lower() in POPULAR_US_NAMES:
            row['Chủ Sở Hữu (Owner_Representative)'] = name.split()[0].capitalize()
            row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium-High (Breeder Name Match)'
        # Luật 3 (Theo người dùng): Lấy tiền tố trước @ trong Gmail (Ví dụ: roleezyorkies@gmail.com -> Roleez Yorkies)
        elif row['Email'] and '@' in row['Email']:
            prefix = row['Email'].split('@')[0].strip()
            clean_pref = re.sub(r'\d+$', '', prefix).replace('.', ' ').replace('_', ' ').replace('-', ' ').strip()
            if len(clean_pref) >= 3 and not re.match(r'^(info|sales|contact|support|hello|admin)$', clean_pref, re.I):
                row['Chủ Sở Hữu (Owner_Representative)'] = clean_pref.title()
                row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium (Email Prefix Match)'
            else:
                row['Chủ Sở Hữu (Owner_Representative)'] = name
                row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 3 - Medium (Facebook Page Name Fallback)'
        # Luật 4: Lấy trực tiếp tên Facebook của người đó
        else:
            row['Chủ Sở Hữu (Owner_Representative)'] = name
            row['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 3 - Medium (Facebook Page Name Fallback)'

    # 7. Tính lại Weather Trigger
    st_up = (row['Bang (State)'] or '').upper()
    c_low = (row['Thành Phố (City)'] or '').lower()
    cold_snow_states = {'WA', 'OR', 'ID', 'MT', 'WY', 'ND', 'SD', 'MN', 'WI', 'MI', 'IL', 'IN', 'OH', 'PA', 'NY', 'VT', 'NH', 'ME', 'MA', 'CT', 'RI', 'NJ', 'CO', 'AK'}
    hot_sunbelt_states = {'TX', 'FL', 'AZ', 'NV', 'NM', 'GA', 'AL', 'MS', 'LA', 'SC'}

    if st_up in cold_snow_states or any(x in c_low for x in ['seattle', 'portland', 'chicago', 'detroit', 'minneapolis', 'buffalo', 'denver', 'wilbraham']):
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 1 (Mưa/Tuyết/Lạnh giá): Đẩy mạnh Thảm cỏ thoát nước + Khay vệ sinh trong nhà (Tránh cún ướt chân, bẩn sàn)'
    elif st_up in hot_sunbelt_states or any(x in c_low for x in ['phoenix', 'las vegas', 'miami', 'houston', 'dallas', 'orlando']):
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 1 (Nắng gắt mặt đường >90°F): Đẩy mạnh Cỏ nhân tạo làm mát + Khay Potty ban công (Tránh cún bỏng đệm chân)'
    elif st_up or c_low:
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 2 (Chó cuồng chân nhốt trong nhà): Chào Combo Đồ chơi ngứa răng Chew Toy + Snuggle Puppy xoa dịu stress'
    else:
        row['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'] = 'Trigger 3 (Khí hậu biến động): Chào trọn gói Take-Home Starter Kit V2/V3 (Giải pháp vệ sinh + đồ chơi toàn diện)'

    # 8. Tính lại Lead Score
    rec_score = int(row.get('Điểm Recency (0-35)', 15) or 15)
    score_infra = (5 if row['Website Chính Thức'] else 0) + (5 if row['Email'] else 0)
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

    rows_cleaned.append(row)

df_out = pd.DataFrame(rows_cleaned)
df_out.to_csv(CRM_CSV, index=False, encoding='utf-8-sig')
print(f"[✓] ĐÃ LÀM SẠCH HOÀN TOÀN FILE CSV MASTER: {CRM_CSV}")
print(f"    - Tổng dòng: {len(df_out)}")
print(f"    - Số email duy nhất: {df_out['Email'][df_out['Email'] != ''].nunique()}")
print(f"    - Số website duy nhất: {df_out['Website Chính Thức'][df_out['Website Chính Thức'] != ''].nunique()}")
print(f"    - Số phone duy nhất: {df_out['Số Điện Thoại (Phone)'][df_out['Số Điện Thoại (Phone)'] != ''].nunique()}")
print(f"    - Chủ sở hữu chứa placeholder: {df_out['Chủ Sở Hữu (Owner_Representative)'].str.contains('Chủ trại / Quản lý chuồng trại', na=False).sum()} dòng (ĐÃ VỀ 0!)")

# Cập nhật rag_breeder_db.json sạch
print("[*] 4. Cập nhật rag_breeder_db.json loại bỏ vĩnh viễn profile.php...")
with open(JSON_RAG_EXT, 'w', encoding='utf-8') as f:
    json.dump(master_db, f, ensure_ascii=False, indent=2)
print(f"[✓] Đã cập nhật {JSON_RAG_EXT}!")
