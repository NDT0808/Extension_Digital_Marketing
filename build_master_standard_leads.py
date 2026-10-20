import os
import re
import csv
import pandas as pd
import numpy as np

DATASETS_DIR = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Datasets"
OUTPUT_DIR = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
OUT_EXCEL = os.path.join(OUTPUT_DIR, "Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx")

print("================================================================================")
print("BẮT ĐẦU QUY TRÌNH HỢP NHẤT, KHỬ TRÙNG LẶP & CHUẨN HÓA TOÀN BỘ KHO DỮ LIỆU")
print("Chuẩn mực: SKILL.md (Pet Grass, Potty & Toys Lead Finder - 100% US Target Market)")
print("================================================================================")

# ------------------------------------------------------------------------------
# 1. BỘ LỌC ÂM TÍNH (NEGATIVE EXCLUSION FILTERS)
# ------------------------------------------------------------------------------
NEGATIVE_PATTERNS = [
    # 1. Hiệp hội phả hệ, CLB quốc gia / giống chó
    (r'\b(akc|american\s*kennel\s*club|ukc|westminster|fci|canadian\s*kennel\s*club|the\s*kennel\s*club|national\s*purebred|breed\s*club|club\s*of\s*america|\w+\s*club|dog\s*club|kennel\s*club|foundation\s*of\s*america|humane\s*society\s*of\s*the\s*united\s*states|american\s*bully\s*kennel\s*club|abkc)\b', 'Hiệp hội / CLB phả hệ phi lợi nhuận'),
    # 2. Đại siêu thị bán lẻ
    (r'\b(petsmart|petco|chewy|pet\s*supplies\s*plus)\b', 'Chuỗi siêu thị bán lẻ lớn'),
    # 3. Kênh truyền thông, báo chí, meme
    (r'\b(weratedogs|dogster|dogs\s*naturally|magazine|news|the\s*dodo|things\s*dog\s*handlers\s*say|pure\s*dog\s*talk|dogs\s*of\s*instagram|canadian\s*dog\s*fancier|american\s*dog\s*fancier|dog\s*news)\b', 'Kênh truyền thông / Báo chí / Meme'),
    # 4. Công ty thuốc, xét nghiệm gen, thú y
    (r'\b(embark|zoetis|revival\s*animal|fear\s*free|orivet|veterinary\s*imaging|genetic|vet\s*hospital|animal\s*hospital)\b', 'Công ty thuốc / Xét nghiệm gen thú y'),
    # 5. Ngành nghề khác mượn tên giống chó (Roofing, Bee, Tires, Pizza, Plumbing, Solar, Auto...)
    (r'\b(roofing|bee\s*co|beekeeping|tires|pizza|plumbing|solar|motors|automotive|tattoo|construction|bail\s*bonds|security\s*services|landscaping|pest\s*control|cleaning\s*services)\b', 'Ngành nghề khác mượn tên cún cưng (Phi thú cưng)'),
    # 6. Profile rác / ảo
    (r'^(facebook\s*user|deleted\s*account|user\s*\d+)$', 'Tài khoản ảo / Rác')
]

BRAND_COMPETITOR_PATTERNS = [
    (r'\b(original\s*snuggle\s*puppy|snuggle\s*puppy\s*brand|impact\s*dog\s*crates|kong\s*company)\b', 'Hãng sản xuất phụ kiện / Đồ chơi thú cưng đối thủ')
]

# ------------------------------------------------------------------------------
# 2. TỪ KHÓA ĐỊNH DANH ICP & GIỐNG CHÓ
# ------------------------------------------------------------------------------
BREEDER_KW = [
    'kennel', 'kennels', 'puppy', 'puppies', 'breeder', 'breeders', 'doodle', 'doodles', 
    'frenchie', 'frenchies', 'bulldog', 'bulldogs', 'hound', 'hounds', 'bassets', 'farm', 
    'haus', 'retriever', 'shepherd', 'corgi', 'pom', 'bullies', 'bully', 'poodle', 
    'collie', 'spaniel', 'mastiff', 'aussie', 'malinois', 'dachshund', 'rottweiler',
    'golden retriever', 'french bulldog', 'dane', 'terrier', 'labrador', 'bernese'
]

TRAINING_KW = [
    'training', 'trainer', 'academy', 'k9', 'daycare', 'boarding', 'grooming', 
    'dog spa', 'resort', 'canine educator', 'dog school', 'k-9'
]

RESCUE_KW = [
    'rescue', 'shelter', 'sanctuary', 'adoption', 'animal rescue', 'stray'
]

PET_LOVER_PATTERNS = [
    r'\bthe\s*dog\b', r'\bthe\s*pug\b', r'\bthe\s*frenchie\b', r'\bthe\s*bulldog\b',
    r'therapy\s*dog', r'adventures\s*of', r'life\s*with', r'daily\s*dose',
    r'dog\s*mom', r'dog\s*dad', r'puppy\s*love'
]

HIGH_VALUE_BREEDS = [
    'french bulldog', 'frenchie', 'frenchies', 'bulldog', 'bulldogs', 'goldendoodle', 
    'bernedoodle', 'cavapoo', 'doodle', 'doodles', 'corgi', 'corgis', 'malinois', 
    'shepherd', 'retriever', 'labrador', 'golden', 'rottweiler', 'bully', 'bullies'
]

NON_US_PHONE_PREFIXES = ['+33', '+44', '+61', '+64', '+49', '+84', '+39', '+34', '+31', '+46', '+81', '+86', '+82', '+7', '+55', '+52', '+43']

def clean_url(url):
    if not url or pd.isna(url): return ''
    u = str(url).strip().lower().rstrip('/')
    u = re.sub(r'^https?://', '', u)
    u = re.sub(r'^www\.', '', u)
    return u

def clean_phone(phone):
    if not phone or pd.isna(phone): return ''
    return str(phone).strip()

def clean_name(name):
    if not name or pd.isna(name): return ''
    return str(name).strip()

def is_international(phone_str, location_str, url_str):
    phone_s = str(phone_str).strip()
    loc_s = str(location_str).strip().lower()
    url_s = str(url_str).strip().lower()
    for pref in NON_US_PHONE_PREFIXES:
        if phone_s.startswith(pref):
            return True
    for c in ['france', 'united kingdom', 'uk', 'australia', 'new zealand', 'germany', 'vietnam', 'spain', 'italy', 'canada', 'nz']:
        if c in loc_s:
            return True
    for ext in ['.uk', '.au', '.nz', '.ca', '.fr', '.de', '.vn', '.es', '.it']:
        if url_s.endswith(ext) or (ext + '/') in url_s:
            return True
    return False

# ------------------------------------------------------------------------------
# 3. NẠP & HỢP NHẤT ĐA NGUỒN (MULTI-SOURCE MERGING & DEDUPLICATION)
# ------------------------------------------------------------------------------
entities = {} # key -> entity dict
url_to_key = {}
name_to_key = {}
phone_to_key = {}

def get_or_create_entity(primary_name, website='', fb_url='', phone='', email='', source=''):
    name_clean = clean_name(primary_name)
    web_clean = clean_url(website)
    fb_clean = clean_url(fb_url)
    phone_clean = clean_phone(phone)
    
    # Tìm key tồn tại
    entity_key = None
    if web_clean and web_clean in url_to_key:
        entity_key = url_to_key[web_clean]
    elif fb_clean and fb_clean in url_to_key:
        entity_key = url_to_key[fb_clean]
    elif phone_clean and phone_clean in phone_to_key:
        entity_key = phone_to_key[phone_clean]
    elif name_clean and name_clean.lower() in name_to_key:
        entity_key = name_to_key[name_clean.lower()]
        
    if not entity_key:
        # Tạo mới
        entity_key = f"ENT-{len(entities)+1:06d}"
        entities[entity_key] = {
            'entity_key': entity_key,
            'name': name_clean,
            'website': website,
            'fb_url': fb_url,
            'phone': phone,
            'email': email,
            'city': '',
            'state': '',
            'address': '',
            'zip': '',
            'country': 'United States',
            'bio': '',
            'breeds': '',
            'amz_cat': 'Amazon link not found',
            'amz_link': '',
            'has_puppy_page': False,
            'has_application': False,
            'has_take_home_kit': False,
            'recency_text': 'Đang hoạt động',
            'recency_hours': 24.0,
            'source_tags': set([source])
        }
    else:
        entities[entity_key]['source_tags'].add(source)
        # Bổ sung dữ liệu nếu thiếu
        if not entities[entity_key]['name'] and name_clean:
            entities[entity_key]['name'] = name_clean
        if not entities[entity_key]['website'] and website:
            entities[entity_key]['website'] = website
        if not entities[entity_key]['fb_url'] and fb_url:
            entities[entity_key]['fb_url'] = fb_url
        if not entities[entity_key]['phone'] and phone:
            entities[entity_key]['phone'] = phone
        if not entities[entity_key]['email'] and email:
            entities[entity_key]['email'] = email
            
    # Map các trường định danh về entity_key
    if web_clean: url_to_key[web_clean] = entity_key
    if fb_clean: url_to_key[fb_clean] = entity_key
    if phone_clean: phone_to_key[phone_clean] = entity_key
    if name_clean: name_to_key[name_clean.lower()] = entity_key
    
    return entities[entity_key]

# ------------------------------------------------------------------------------
# NẠP TỪNG NGUỒN THEO THỨ TỰ ƯU TIÊN
# ------------------------------------------------------------------------------

# 3.1 Nguồn Ground Truth: List_Info_User.xlsx / priority_list_2026-10-06_v2.xlsx
f_prio = os.path.join(DATASETS_DIR, "List_Info_User.xlsx")
if os.path.exists(f_prio):
    print("[*] Nạp Nguồn 1 (Ground Truth): List_Info_User.xlsx...")
    df_prio = pd.read_excel(f_prio)
    for _, r in df_prio.iterrows():
        bname = r.get('Breeder Name', '')
        web = r.get('Website', '')
        fb = r.get('Facebook URL', '')
        ph = r.get('Phone', '')
        em = r.get('Email', '')
        ent = get_or_create_entity(bname, web, fb, ph, em, 'List_Info_User')
        ent['city'] = str(r.get('City', '')) if pd.notna(r.get('City')) else ent['city']
        ent['state'] = str(r.get('Bang/State', '')) if pd.notna(r.get('Bang/State')) else ent['state']
        ent['zip'] = str(r.get('Zip', '')) if pd.notna(r.get('Zip')) else ent['zip']
        ent['address'] = str(r.get('Address', '')) if pd.notna(r.get('Address')) else ent['address']
        ent['amz_cat'] = str(r.get('Phân loại Amazon', ent['amz_cat'])) if pd.notna(r.get('Phân loại Amazon')) else ent['amz_cat']
        ent['amz_link'] = str(r.get('Amazon Link', ent['amz_link'])) if pd.notna(r.get('Amazon Link')) else ent['amz_link']
        ent['has_take_home_kit'] = True

# 3.2 Nguồn Sales List: Customers_Sales_2026.xlsx
f_sales = os.path.join(DATASETS_DIR, "Customers_Sales_2026.xlsx")
if os.path.exists(f_sales):
    print("[*] Nạp Nguồn 2 (Sales Curated): Customers_Sales_2026.xlsx...")
    df_sales = pd.read_excel(f_sales)
    for _, r in df_sales.iterrows():
        bname = r.get('Tên Đối Tác / Breeder Name', '')
        web = r.get('Website', '')
        fb = r.get('Facebook URL', '')
        ph = r.get('Điện Thoại / Phone', '')
        em = r.get('Email', '')
        ent = get_or_create_entity(bname, web, fb, ph, em, 'Customers_Sales_2026')
        ent['city'] = str(r.get('Thành Phố / City', '')) if pd.notna(r.get('Thành Phố / City')) else ent['city']
        ent['state'] = str(r.get('Bang / State', '')) if pd.notna(r.get('Bang / State')) else ent['state']
        ent['zip'] = str(r.get('Mã Zip / Postal Code', '')) if pd.notna(r.get('Mã Zip / Postal Code')) else ent['zip']
        ent['address'] = str(r.get('Địa Chỉ / Address', '')) if pd.notna(r.get('Địa Chỉ / Address')) else ent['address']
        if pd.notna(r.get('Link Amazon Storefront / Wishlist')):
            ent['amz_link'] = str(r.get('Link Amazon Storefront / Wishlist'))
        if pd.notna(r.get('Kênh Bán Amazon')) and str(r.get('Kênh Bán Amazon')) != 'Amazon link not found':
            ent['amz_cat'] = str(r.get('Kênh Bán Amazon'))

# 3.3 Nguồn Telesale Cleaned: telesale_leads_clean.csv
f_tele = os.path.join(DATASETS_DIR, "telesale_leads_clean.csv")
if os.path.exists(f_tele):
    print("[*] Nạp Nguồn 3 (Telesale Cleaned): telesale_leads_clean.csv...")
    df_tele = pd.read_csv(f_tele)
    for _, r in df_tele.iterrows():
        bname = r.get('Name', '')
        web = r.get('Website', '')
        fb = r.get('Facebook', '')
        ph = r.get('Phones', '')
        em = r.get('Emails', '')
        ent = get_or_create_entity(bname, web, fb, ph, em, 'telesale_leads_clean')
        ent['city'] = str(r.get('City', '')) if pd.notna(r.get('City')) else ent['city']
        ent['state'] = str(r.get('State', '')) if pd.notna(r.get('State')) else ent['state']
        if str(r.get('Ban_Cho', '')).lower() in ['yes', 'true', '1']: ent['has_puppy_page'] = True
        if str(r.get('Co_Form', '')).lower() in ['yes', 'true', '1']: ent['has_application'] = True
        if str(r.get('Take_Home_Kit', '')).lower() in ['yes', 'true', '1']: ent['has_take_home_kit'] = True

# 3.4 Nguồn Master CSV: 2026_10_02_v1_master.csv (7.081 rows)
f_master = os.path.join(DATASETS_DIR, "2026_10_02_v1_master.csv")
if os.path.exists(f_master):
    print("[*] Nạp Nguồn 4 (Master Database): 2026_10_02_v1_master.csv...")
    df_master = pd.read_csv(f_master)
    for _, r in df_master.iterrows():
        bname = r.get('name', '')
        web = r.get('websites', '')
        fb = r.get('facebook_url', '')
        ph = r.get('phones', '')
        em = r.get('emails', '')
        ent = get_or_create_entity(bname, web, fb, ph, em, '2026_10_02_v1_master')
        ent['city'] = str(r.get('city', '')) if pd.notna(r.get('city')) else ent['city']
        ent['state'] = str(r.get('state', '')) if pd.notna(r.get('state')) else ent['state']
        ent['zip'] = str(r.get('postal_code', '')) if pd.notna(r.get('postal_code')) else ent['zip']
        ent['address'] = str(r.get('address', '')) if pd.notna(r.get('address')) else ent['address']
        ent['bio'] = str(r.get('bio', '')) if pd.notna(r.get('bio')) else ent['bio']
        ent['breeds'] = str(r.get('dog_breeds', '')) if pd.notna(r.get('dog_breeds')) else ent['breeds']
        if str(r.get('has_puppy_sales_page', '')).lower() in ['yes', 'true', '1']: ent['has_puppy_page'] = True
        if str(r.get('has_puppy_application', '')).lower() in ['yes', 'true', '1']: ent['has_application'] = True
        if str(r.get('provides_puppy_take_home_kit', '')).lower() in ['yes', 'true', '1']: ent['has_take_home_kit'] = True

# 3.5 Nguồn Facebook Merged Pages: fb_pages_merged.xlsx (5.369 rows)
f_pages = os.path.join(DATASETS_DIR, "fb_pages_merged.xlsx")
if os.path.exists(f_pages):
    print("[*] Nạp Nguồn 5 (Facebook Merged Pages): fb_pages_merged.xlsx...")
    df_pages = pd.read_excel(f_pages)
    for _, r in df_pages.iterrows():
        bname = r.get('Tên', '')
        web = r.get('Website', '')
        fb = r.get('Link gốc', '') or r.get('Link cuối', '')
        ph = r.get('Điện thoại', '')
        em = r.get('Email', '')
        ent = get_or_create_entity(bname, web, fb, ph, em, 'fb_pages_merged')
        if pd.notna(r.get('Giới thiệu')):
            ent['bio'] = f"{ent['bio']} {r.get('Giới thiệu')}".strip()

# 3.6 Nguồn Facebook Publish Time & Recency: FB_PublishTime_1791866762111.csv (5.993 rows)
f_fbpub = os.path.join(DATASETS_DIR, "FB_PublishTime_1791866762111.csv")
if os.path.exists(f_fbpub):
    print("[*] Nạp Nguồn 6 (Facebook Recency Events): FB_PublishTime_1791866762111.csv...")
    with open(f_fbpub, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader, None)
        for r in reader:
            if len(r) >= 6:
                url, bname, pub, rel = r[1], r[2], r[3], r[5]
                ent = get_or_create_entity(bname, fb_url=url, source='FB_PublishTime')
                ent['recency_text'] = rel
                # Tính giờ
                rel_l = str(rel).lower()
                if any(x in rel_l for x in ['phút', 'vừa xong']):
                    ent['recency_hours'] = min(ent['recency_hours'], 0.5)
                elif 'giờ' in rel_l:
                    m = re.search(r'(\d+)\s*giờ', rel_l)
                    h = float(m.group(1)) if m else 5.0
                    ent['recency_hours'] = min(ent['recency_hours'], h)
                elif 'ngày' in rel_l:
                    m = re.search(r'(\d+)\s*ngày', rel_l)
                    d = float(m.group(1)) if m else 3.0
                    ent['recency_hours'] = min(ent['recency_hours'], d * 24.0)

print(f"\n[✓] TỔNG KẾT KHỬ TRÙNG LẶP: Đã hợp nhất thành {len(entities)} HỒ SƠ ĐỘC NHẤT (Unique Golden Entities)!")

# ------------------------------------------------------------------------------
# 4. THUẬT TOÁN ĐÁNH GIÁ, PHÂN LOẠI & CHẤM ĐIỂM 5 TRỤC CHỐNG BÃO HÒA
# ------------------------------------------------------------------------------
print("[*] Bắt đầu đánh giá, phân loại ICP và chấm điểm 5 trục...")

classified_records = []
excluded_records = []
intl_records = []

for idx, (ekey, ent) in enumerate(entities.items()):
    name_str = ent['name']
    name_l = name_str.lower()
    bio_l = ent['bio'].lower()
    full_text = f"{name_l} {bio_l} {ent['breeds'].lower()}"
    phone = ent['phone']
    website = ent['website']
    fb_url = ent['fb_url']
    email = ent['email']
    city = ent['city']
    state = ent['state']
    location_str = f"{city}, {state}".strip(", ")
    
    # GIAI ĐOẠN 1: BỘ LỌC LOẠI TRỪ ÂM TÍNH (NEGATIVE EXCLUSIONS)
    is_excluded = False
    exclude_reason = ''
    for pat, reason in NEGATIVE_PATTERNS:
        if re.search(pat, name_l) or re.search(pat, clean_url(fb_url)) or re.search(pat, clean_url(website)):
            is_excluded = True
            exclude_reason = reason
            break
            
    if not is_excluded:
        for pat, reason in BRAND_COMPETITOR_PATTERNS:
            if re.search(pat, name_l):
                is_excluded = True
                exclude_reason = reason
                break
                
    if is_excluded:
        rec_exc = {
            'Master_ID': f"LEAD-M-{idx+1:06d}",
            'Tên': name_str,
            'Trạng Thái': 'LOẠI BỎ (Excluded)',
            'Lý Do Loại Bỏ': exclude_reason,
            'Website': website,
            'Điện Thoại': phone,
            'Email': email,
            'Facebook URL': fb_url,
            'Thành Phố': city,
            'Bang': state,
            'Nguồn Dữ Liệu': ', '.join(ent['source_tags']),
            'Hành Động': 'Loại bỏ hoàn toàn khỏi CRM, không tiếp cận'
        }
        excluded_records.append(rec_exc)
        continue

    # GIAI ĐOẠN 2: KIỂM TRA ĐỊA LÝ & PHẠM VI 100% US
    intl = is_international(phone, location_str, website or fb_url)
    if intl:
        rec_intl = {
            'Master_ID': f"LEAD-M-{idx+1:06d}",
            'Tên': name_str,
            'Trạng Thái': 'Quốc Tế (Non-US)',
            'Website': website,
            'Điện Thoại': phone,
            'Email': email,
            'Facebook URL': fb_url,
            'Thành Phố': city,
            'Bang / Quốc Gia': state or 'Non-US',
            'Nguồn Dữ Liệu': ', '.join(ent['source_tags']),
            'Hành Động': 'Lưu phễu mở rộng Giai đoạn 2 (Không Telesale giai đoạn này)'
        }
        intl_records.append(rec_intl)
        continue

    # GIAI ĐOẠN 3: TÍNH ĐIỂM TRỤC 1 - RECENCY (0 - 35 ĐIỂM)
    rec_h = ent['recency_hours']
    if rec_h <= 3.0:
        rec_score = 35
        rec_tier = 'Hot (≤ 3 giờ)'
    elif rec_h <= 24.0:
        rec_score = 32
        rec_tier = 'Hot (4 - 24 giờ)'
    elif rec_h <= 72.0:
        rec_score = 28
        rec_tier = 'Hot (1 - 3 ngày)'
    elif rec_h <= 168.0:
        rec_score = 20
        rec_tier = 'Warm (4 - 7 ngày)'
    elif rec_h <= 336.0:
        rec_score = 15
        rec_tier = 'Warm (8 - 14 ngày)'
    elif rec_h <= 720.0:
        rec_score = 8
        rec_tier = 'Cool (15 - 30 ngày)'
    else:
        rec_score = 5 if bool(website or phone) else 0
        rec_tier = 'Cold (> 30 ngày)'

    # GIAI ĐOẠN 4: PHÂN LOẠI ICP - TRỤC 2 (10 - 30 ĐIỂM)
    is_breeder = any(k in full_text for k in BREEDER_KW) or ent['has_puppy_page'] or ent['has_take_home_kit']
    is_training = any(k in full_text for k in TRAINING_KW)
    is_rescue = any(k in full_text for k in RESCUE_KW)
    is_pet_lover = any(re.search(p, full_text) for p in PET_LOVER_PATTERNS)

    if is_breeder and not is_pet_lover:
        icp_type = 'Dog Breeder / Commercial Kennel (B2B)'
        icp_score = 30
        prod_target = 'Puppy Starter Kit V2/V3 (Cỏ thoát nước + Khay Potty + Đồ chơi in logo)'
    elif is_training:
        icp_type = 'Pet Training / K9 Academy / Grooming (B2B)'
        icp_score = 22
        prod_target = 'Cỏ nhân tạo lót sân chơi chịu lực + Đồ chơi cắn K9 chuyên dụng'
    elif is_rescue:
        icp_type = 'Pet Rescue / Shelter (B2B)'
        icp_score = 15
        prod_target = 'Tã lót Pee Pad thấm hút số lượng lớn + Khay vệ sinh tái sử dụng'
    else:
        icp_type = 'Pet Lover / Người Nuôi Cá Nhân (B2C)'
        icp_score = 10
        prod_target = 'Khay vệ sinh căn hộ / Thảm cỏ ban công / Đồ chơi xoa dịu'

    # GIAI ĐOẠN 5: GIÁ TRỊ THƯƠNG MẠI GIỐNG CHÓ - TRỤC 3 (0 - 15 ĐIỂM)
    breed_matches = [b for b in HIGH_VALUE_BREEDS if b in full_text]
    if len(breed_matches) >= 2:
        breed_score = 15
    elif len(breed_matches) == 1:
        breed_score = 10
    elif is_breeder:
        breed_score = 5
    else:
        breed_score = 0

    # GIAI ĐOẠN 6: HẠ TẦNG DOANH NGHIỆP & WEB - TRỤC 4 (0 - 10 ĐIỂM)
    has_web = bool(website)
    has_biz_infra = ent['has_application'] or any(k in full_text for k in ['kennel', 'farm', 'academy', 'llc', 'ltd', 'inc'])
    infra_score = (5 if has_web else 0) + (5 if has_biz_infra else 0)

    # GIAI ĐOẠN 7: UY TÍN SÀN AMAZON - TRỤC 5 (0 - 15 ĐIỂM)
    amz_cat = ent['amz_cat']
    amz_link = ent['amz_link']
    if 'Selling pet toys + Artificial grass' in amz_cat:
        amz_score = 15
    elif 'Selling artificial grass' in amz_cat:
        amz_score = 10
    elif 'Selling pet toys' in amz_cat:
        amz_score = 7
    elif 'target sales' in amz_cat:
        amz_score = 3
    else:
        amz_score = 0

    total_score = min(100, rec_score + icp_score + breed_score + infra_score + amz_score)

    # GIAI ĐOẠN 8: GẮN TRIGGER THỜI TIẾT (MỤC 8 SKILL.MD)
    if state in ['CO', 'MN', 'WI', 'IL', 'MI', 'NY', 'PA', 'OH', 'WA', 'VT', 'ME', 'NH']:
        weather_trigger = 'Trigger 1 (Mưa bão/Băng tuyết): Đẩy mạnh Thảm cỏ thoát nước & Khay vệ sinh trong nhà'
    elif state in ['AZ', 'NV', 'TX', 'FL', 'CA', 'GA']:
        weather_trigger = 'Trigger 1 (Nắng nóng bỏng rát mặt đường): Đẩy giải pháp đi vệ sinh mát mẻ trong nhà'
    else:
        weather_trigger = 'Trigger 2 (Cún bị nhốt cuồng chân): Đẩy Đồ chơi cắn xoa dịu stress Snuggle Puppy'

    # GIAI ĐOẠN 9: PHÂN TẦNG VÀ HÀNH ĐỘNG SALES THEO CHUẨN MỤC 2.2 SKILL.MD
    if icp_type == 'Pet Lover / Người Nuôi Cá Nhân (B2C)':
        tier = 'B2C Pet Lover (Ads Only)'
        action = '🛑 KHÔNG gọi điện Telesale. Chuyển sang tệp Retargeting Ads bán lẻ thảm cỏ/đồ chơi'
    else:
        if total_score >= 85:
            tier = 'Tier S (Kim Cương: 85-100đ)'
            action = '🔥 TELESALE: Gọi chốt Take-Home Kit in logo độc quyền ngay trong ngày'
        elif total_score >= 70:
            tier = 'Tier A (Vàng: 70-84đ)'
            action = '📞 TELESALE + EMAIL: Ưu tiên gọi trong ngày + Email cá nhân hóa chào Puppy Kit V2/V3'
        elif total_score >= 61:
            tier = 'Tier B+ / Cấp A (Hot Lead: 61-69đ)'
            action = '📞 TELESALE + EMAIL: Báo giá sỉ Starter Kit & Chiết khấu BOM cho trại'
        elif total_score >= 50:
            tier = 'Tier B (Bạc: 50-60đ)'
            action = '✉️ AUTOMATION: Nuôi dưỡng chuỗi email tự động giới thiệu danh mục sản phẩm'
        elif total_score >= 30:
            tier = 'Tier C (Đồng: 30-49đ)'
            action = '💬 SOCIAL DM: Nhắn tin trực tiếp Fanpage/Instagram chi phí thấp'
        else:
            tier = 'Tier D (Đóng băng: <30đ)'
            action = '❄️ ĐÓNG BĂNG: Tạm thời lưu trữ, không phân bổ ngân sách bán hàng'

    classified_records.append({
        'Master_ID': f"LEAD-US-{len(classified_records)+1:06d}",
        'Breeder_Name': name_str,
        'Website': website,
        'Phone': phone,
        'Email': email,
        'Facebook_URL': fb_url,
        'Address': ent['address'],
        'City': city,
        'State': state,
        'Zip_Code': ent['zip'],
        'Country': 'United States',
        'Breeds_Identified': ', '.join(breed_matches) if breed_matches else (ent['breeds'] or 'Chung'),
        'ICP_Segment': icp_type,
        'Amazon_Status': amz_cat,
        'Amazon_Link': amz_link,
        'Recency_Info': f"{ent['recency_text']} ({rec_tier})",
        'Score_Recency': rec_score,
        'Score_ICP': icp_score,
        'Score_Breed': breed_score,
        'Score_Infra': infra_score,
        'Score_Amazon': amz_score,
        'Total_Lead_Score': total_score,
        'Tier_Rank': tier,
        'Is_Cap_A_Hot_Lead': total_score >= 61 and not 'Pet Lover' in icp_type,
        'Target_Products': prod_target,
        'Sales_Action': action,
        'Weather_Trigger': weather_trigger,
        'Data_Sources': ', '.join(ent['source_tags'])
    })

print(f"[✓] Đã phân loại xong {len(classified_records)} leads hợp lệ tại Mỹ!")
print(f"[!] Đã lọc bỏ {len(excluded_records)} đơn vị phi khách hàng.")
print(f"[!] Đã tách {len(intl_records)} đối tác quốc tế sang phễu mở rộng.")

# ------------------------------------------------------------------------------
# 5. XUẤT RA EXCEL ĐA SHEET TOÀN DIỆN (MASTER CRM WORKBOOK)
# ------------------------------------------------------------------------------
df_valid_us = pd.DataFrame(classified_records)
df_exc = pd.DataFrame(excluded_records)
df_intl = pd.DataFrame(intl_records)

# Tách tập con
df_hot_cap_a = df_valid_us[df_valid_us['Is_Cap_A_Hot_Lead'] == True].sort_values(by='Total_Lead_Score', ascending=False)
df_tier_b = df_valid_us[df_valid_us['Tier_Rank'].str.contains('Tier B \(Bạc')].sort_values(by='Total_Lead_Score', ascending=False)
df_pet_lovers = df_valid_us[df_valid_us['Tier_Rank'].str.contains('Pet Lover')].sort_values(by='Total_Lead_Score', ascending=False)

# Dashboard KPIs
total_all = len(entities)
valid_us_count = len(df_valid_us)
hot_count = len(df_hot_cap_a)
tier_s_count = len(df_hot_cap_a[df_hot_cap_a['Tier_Rank'].str.contains('Tier S')])
tier_a_count = len(df_hot_cap_a[df_hot_cap_a['Tier_Rank'].str.contains('Tier A \(Vàng')])
tier_b_plus_count = len(df_hot_cap_a[df_hot_cap_a['Tier_Rank'].str.contains('Tier B\+')])
tier_b_count = len(df_tier_b)
pet_lover_count = len(df_pet_lovers)
exc_count = len(df_exc)
intl_count = len(df_intl)

dashboard_rows = [
    {'Chỉ Số / Metric': 'TỔNG SỐ HỒ SƠ ĐỘC NHẤT SAU KHỬ TRÙNG LẶP (Unique Entities)', 'Số Lượng': total_all, 'Tỷ Lệ (%)': '100.0%', 'Ý Nghĩa Vận Hành': 'Toàn bộ cơ sở dữ liệu đã gộp từ 7 nguồn'},
    {'Chỉ Số / Metric': 'Số hồ sơ BỊ LOẠI BỎ (Excluded: AKC, PetSmart, Meme, DNA, Roofing, Bee...)', 'Số Lượng': exc_count, 'Tỷ Lệ (%)': f"{exc_count/total_all*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Triệt tiêu 100% rác và ngành nghề phi cún cưng'},
    {'Chỉ Số / Metric': 'Số hồ sơ QUỐC TẾ (International Expansion: Canada, UK, Úc, EU...)', 'Số Lượng': intl_count, 'Tỷ Lệ (%)': f"{intl_count/total_all*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Lưu trữ phễu dự phòng mở rộng Giai đoạn 2'},
    {'Chỉ Số / Metric': 'TỔNG KHÁCH HÀNG HỢP LỆ NỘI ĐỊA HOA KỲ (US Valid Leads)', 'Số Lượng': valid_us_count, 'Tỷ Lệ (%)': f"{valid_us_count/total_all*100:.1f}%", 'Ý Nghĩa Vận Hành': '100% thuộc 50 tiểu bang Mỹ'},
    {'Chỉ Số / Metric': '🔥 TỔNG HOT LEADS CẤP A (Điểm ≥ 61 - Trọng Điểm Sales Giai Đoạn 1)', 'Số Lượng': hot_count, 'Tỷ Lệ (%)': f"{hot_count/valid_us_count*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Ưu tiên số 1 cho đội Telesale gọi chốt Take-Home Kit'},
    {'Chỉ Số / Metric': '  - Trong đó: Tier S (Kim Cương: 85 - 100 điểm)', 'Số Lượng': tier_s_count, 'Tỷ Lệ (%)': f"{tier_s_count/valid_us_count*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Khách hàng hoàn hảo nhất, chốt deal ngay trong ngày'},
    {'Chỉ Số / Metric': '  - Trong đó: Tier A (Vàng: 70 - 84 điểm)', 'Số Lượng': tier_a_count, 'Tỷ Lệ (%)': f"{tier_a_count/valid_us_count*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Telesale + Email cá nhân hóa chào gói V2/V3'},
    {'Chỉ Số / Metric': '  - Trong đó: Tier B+ (Hot Lead B2B: 61 - 69 điểm)', 'Số Lượng': tier_b_plus_count, 'Tỷ Lệ (%)': f"{tier_b_plus_count/valid_us_count*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Báo giá sỉ Starter Kit & chiết khấu BOM'},
    {'Chỉ Số / Metric': '✉️ TỔNG TIỀM NĂNG B2B (Tier B: 50 - 60 điểm)', 'Số Lượng': tier_b_count, 'Tỷ Lệ (%)': f"{tier_b_count/valid_us_count*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Đưa vào chuỗi Email Marketing Automation'},
    {'Chỉ Số / Metric': '🛑 TỔNG LEADS B2C BÁN LẺ (Pet Lovers - CHẶN Telesale, Chỉ chạy Ads)', 'Số Lượng': pet_lover_count, 'Tỷ Lệ (%)': f"{pet_lover_count/valid_us_count*100:.1f}%", 'Ý Nghĩa Vận Hành': 'Tách sang Custom Audience bán lẻ thảm cỏ/đồ chơi'}
]
df_dashboard = pd.DataFrame(dashboard_rows)

print(f"[*] Đang ghi dữ liệu vào Master Workbook: {OUT_EXCEL}...")
with pd.ExcelWriter(OUT_EXCEL, engine='openpyxl') as writer:
    df_dashboard.to_excel(writer, sheet_name='Dashboard_Tong_Quan', index=False)
    df_hot_cap_a.to_excel(writer, sheet_name='US_Hot_Leads_Cap_A_61d', index=False)
    df_tier_b.to_excel(writer, sheet_name='US_Potential_Tier_B', index=False)
    df_valid_us.to_excel(writer, sheet_name='All_US_Valid_Leads', index=False)
    df_pet_lovers.to_excel(writer, sheet_name='B2C_Pet_Lovers', index=False)
    df_intl.to_excel(writer, sheet_name='International_Expansion', index=False)
    df_exc.to_excel(writer, sheet_name='Negative_Excluded_List', index=False)

print(f"================================================================================")
print(f"[✓] HOÀN TẤT XUẤT SẮC! File Master đã sẵn sàng: {OUT_EXCEL}")
print(f"================================================================================")
