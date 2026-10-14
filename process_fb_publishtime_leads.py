import os
import re
import csv
import pandas as pd
import numpy as np

# File Paths
DATASETS_DIR = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Datasets"
FB_CSV = os.path.join(DATASETS_DIR, "FB_PublishTime_1791866762111.csv")
XLSX_PRIO = os.path.join(DATASETS_DIR, "List_Info_User.xlsx")
XLSX_PAGES = os.path.join(DATASETS_DIR, "fb_pages_merged.xlsx")
CSV_MASTER = os.path.join(DATASETS_DIR, "2026_10_02_v1_master.csv")
CSV_TELESALE = os.path.join(DATASETS_DIR, "telesale_leads_clean.csv")
OUT_EXCEL = os.path.join(DATASETS_DIR, "Thong_Ke_Leads_FB_PublishTime_2026.xlsx")

print("[*] 1. Khởi tạo và nạp dữ liệu tra cứu liên kết (Enrichment Lookups)...")

lookup_url = {}
lookup_name = {}

# 1.1 List_Info_User.xlsx
if os.path.exists(XLSX_PRIO):
    df_prio = pd.read_excel(XLSX_PRIO)
    for _, r in df_prio.iterrows():
        bname = str(r.get('Breeder Name', '')).strip()
        web = str(r.get('Website', '')) if pd.notna(r.get('Website')) else ''
        fb_url = str(r.get('Facebook URL', '')) if pd.notna(r.get('Facebook URL')) else ''
        amz_cat = str(r.get('Phân loại Amazon', 'Amazon link not found')) if pd.notna(r.get('Phân loại Amazon')) else 'Amazon link not found'
        amz_link = str(r.get('Amazon Link', '')) if pd.notna(r.get('Amazon Link')) else ''
        phone = str(r.get('Phone', '')) if pd.notna(r.get('Phone')) else ''
        email = str(r.get('Email', '')) if pd.notna(r.get('Email')) else ''
        city = str(r.get('City', '')) if pd.notna(r.get('City')) else ''
        state = str(r.get('Bang/State', '')) if pd.notna(r.get('Bang/State')) else ''
        
        info = {
            'bname': bname, 'website': web, 'phone': phone, 'email': email,
            'city': city, 'state': state, 'country': 'United States',
            'amz_cat': amz_cat, 'amz_link': amz_link, 'has_prio': True
        }
        if bname:
            lookup_name[bname.lower()] = info
        for u in fb_url.split(';'):
            u_clean = u.strip().lower().rstrip('/').replace('www.', '')
            if 'facebook.com' in u_clean:
                lookup_url[u_clean] = info

# 1.2 fb_pages_merged.xlsx
if os.path.exists(XLSX_PAGES):
    df_pages = pd.read_excel(XLSX_PAGES)
    for _, r in df_pages.iterrows():
        p_name = str(r.get('Tên', '')).strip()
        p_bio = str(r.get('Giới thiệu', '')) if pd.notna(r.get('Giới thiệu')) else ''
        p_web = str(r.get('Website', '')) if pd.notna(r.get('Website')) else ''
        p_email = str(r.get('Email', '')) if pd.notna(r.get('Email')) else ''
        p_phone = str(r.get('Điện thoại', '')) if pd.notna(r.get('Điện thoại')) else ''
        u1 = str(r.get('Link gốc', '')).strip().lower().rstrip('/').replace('www.', '')
        u2 = str(r.get('Link cuối', '')).strip().lower().rstrip('/').replace('www.', '')
        
        page_info = {
            'bname': p_name, 'bio': p_bio, 'website': p_web, 'email': p_email,
            'phone': p_phone
        }
        for u in [u1, u2]:
            if 'facebook.com' in u:
                if u in lookup_url:
                    for k, v in page_info.items():
                        if v and not lookup_url[u].get(k):
                            lookup_url[u][k] = v
                else:
                    lookup_url[u] = page_info

# 1.3 telesale_leads_clean.csv
if os.path.exists(CSV_TELESALE):
    df_tele = pd.read_csv(CSV_TELESALE)
    for _, r in df_tele.iterrows():
        t_name = str(r.get('Name', '')).strip()
        t_web = str(r.get('Website', '')) if pd.notna(r.get('Website')) else ''
        t_phone = str(r.get('Phones', '')) if pd.notna(r.get('Phones')) else ''
        t_email = str(r.get('Emails', '')) if pd.notna(r.get('Emails')) else ''
        t_city = str(r.get('City', '')) if pd.notna(r.get('City')) else ''
        t_state = str(r.get('State', '')) if pd.notna(r.get('State')) else ''
        t_fb = str(r.get('Facebook', '')).strip().lower().rstrip('/').replace('www.', '') if pd.notna(r.get('Facebook')) else ''
        
        tele_info = {
            'bname': t_name, 'website': t_web, 'phone': t_phone, 'email': t_email,
            'city': t_city, 'state': t_state, 'country': 'United States'
        }
        if t_name and t_name.lower() not in lookup_name:
            lookup_name[t_name.lower()] = tele_info
        if t_fb and 'facebook.com' in t_fb and t_fb not in lookup_url:
            lookup_url[t_fb] = tele_info

print(f"[✓] Đã tạo Lookup Table: {len(lookup_url)} FB URLs, {len(lookup_name)} Tên đối tác.")

# ==============================================================================
# 2. BỘ TỪ KHÓA & MẪU PHÂN LOẠI CHUẨN THEO SKILL.md
# ==============================================================================
NEGATIVE_PATTERNS = [
    (r'\b(akc|american\s*kennel\s*club|ukc|westminster|fci|canadian\s*kennel\s*club|the\s*kennel\s*club|national\s*purebred|breed\s*club|club\s*of\s*america|\w+\s*club|dog\s*club|kennel\s*club|foundation\s*of\s*america|humane\s*society\s*of\s*the\s*united\s*states)\b', 'Hiệp hội / CLB phả hệ phi lợi nhuận'),
    (r'\b(petsmart|petco|chewy|pet\s*supplies\s*plus)\b', 'Chuỗi siêu thị bán lẻ lớn'),
    (r'\b(weratedogs|dogster|dogs\s*naturally|magazine|news|the\s*dodo|things\s*dog\s*handlers\s*say|pure\s*dog\s*talk|dogs\s*of\s*instagram|canadian\s*dog\s*fancier|american\s*dog\s*fancier|dog\s*news)\b', 'Kênh truyền thông / Báo chí / Meme'),
    (r'\b(embark|zoetis|revival\s*animal|fear\s*free|orivet|veterinary\s*imaging|genetic|vet\s*hospital|animal\s*hospital)\b', 'Công ty thuốc / Xét nghiệm gen thú y'),
    (r'^(facebook\s*user|deleted\s*account|user\s*\d+)$', 'Tài khoản ảo / Rác')
]

BRAND_COMPETITOR_PATTERNS = [
    (r'\b(original\s*snuggle\s*puppy|snuggle\s*puppy\s*brand|impact\s*dog\s*crates|kong\s*company)\b', 'Hãng sản xuất phụ kiện / Đồ chơi thú cưng')
]

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

def is_international(phone_str, location_str):
    phone_s = str(phone_str).strip()
    loc_s = str(location_str).strip().lower()
    for pref in NON_US_PHONE_PREFIXES:
        if phone_s.startswith(pref):
            return True
    for c in ['france', 'united kingdom', 'uk', 'australia', 'new zealand', 'germany', 'vietnam', 'spain', 'italy', 'canada', 'nz']:
        if c in loc_s:
            return True
    return False

# ==============================================================================
# 3. THUẬT TOÁN ĐÁNH GIÁ VÀ PHÂN LOẠI CHI TIẾT
# ==============================================================================
def process_record(row_idx, row_stt, url, name, pub_time, rel_time):
    url_clean = str(url).strip().lower().rstrip('/').replace('www.', '')
    name_str = str(name).strip()
    name_l = name_str.lower()
    
    enriched = lookup_url.get(url_clean) or lookup_name.get(name_l) or {}
    bio = enriched.get('bio', '')
    bio_l = bio.lower() if bio else ''
    full_text = f"{name_l} {bio_l}"
    phone = str(enriched.get('phone', '')).strip()
    city = str(enriched.get('city', '')).strip()
    state = str(enriched.get('state', '')).strip()
    location_str = f"{city}, {state}".strip(", ")
    
    # GIAI ĐOẠN 1: BỘ LỌC LOẠI TRỪ ÂM TÍNH (NEGATIVE EXCLUSIONS)
    for pat, reason in NEGATIVE_PATTERNS:
        if re.search(pat, name_l) or re.search(pat, url_clean):
            return {
                'STT': row_stt,
                'Master_ID': f"LEAD-FB-{row_idx+1:05d}",
                'Tên': name_str,
                'Trạng Thái Hồ Sơ': 'LOẠI BỎ (Excluded)',
                'Phân Loại ICP': 'Phi Khách Hàng (Non-Customer)',
                'Chi Tiết Phân Loại': reason,
                'Website': enriched.get('website', ''),
                'Điện Thoại': phone,
                'Email': enriched.get('email', ''),
                'Thành Phố': city,
                'Bang / State': state,
                'Quốc Gia': 'Excluded',
                'Facebook URL': url,
                'Thời Gian Đăng': str(pub_time),
                'Độ Tươi Mới': str(rel_time),
                'Score_Recency': 0, 'Score_ICP': 0, 'Score_Breed': 0, 'Score_Infra': 0, 'Score_Amazon': 0,
                'Total_Score': 0,
                'Phân Hạng (Tier)': 'Excluded',
                'Phân Loại Amazon': 'Không xét',
                'Link Amazon': '',
                'Sản Phẩm Mục Tiêu': 'Không',
                'Hành Động Đội Sales': 'Loại bỏ hoàn toàn khỏi CRM, không lưu',
                'Ngữ Cảnh Thời Tiết': 'Không'
            }

    for pat, reason in BRAND_COMPETITOR_PATTERNS:
        if re.search(pat, name_l):
            return {
                'STT': row_stt,
                'Master_ID': f"LEAD-FB-{row_idx+1:05d}",
                'Tên': name_str,
                'Trạng Thái Hồ Sơ': 'LOẠI BỎ (Excluded)',
                'Phân Loại ICP': 'Hãng / Thương Hiệu Đối Thủ',
                'Chi Tiết Phân Loại': reason,
                'Website': enriched.get('website', ''),
                'Điện Thoại': phone,
                'Email': enriched.get('email', ''),
                'Thành Phố': city,
                'Bang / State': state,
                'Quốc Gia': 'Excluded',
                'Facebook URL': url,
                'Thời Gian Đăng': str(pub_time),
                'Độ Tươi Mới': str(rel_time),
                'Score_Recency': 0, 'Score_ICP': 0, 'Score_Breed': 0, 'Score_Infra': 0, 'Score_Amazon': 0,
                'Total_Score': 0,
                'Phân Hạng (Tier)': 'Excluded',
                'Phân Loại Amazon': 'Hãng sản xuất',
                'Link Amazon': '',
                'Sản Phẩm Mục Tiêu': 'Không',
                'Hành Động Đội Sales': 'Lưu kho phân tích đối thủ cạnh tranh',
                'Ngữ Cảnh Thời Tiết': 'Không'
            }

    # GIAI ĐOẠN 2: TÍNH ĐIỂM TRỤC 1 - RECENCY (0 - 35 ĐIỂM)
    rel_l = str(rel_time).lower()
    if any(x in rel_l for x in ['phút', 'vừa xong']) or any(f'{h} giờ' in rel_l for h in range(1, 4)):
        rec_score = 35
        rec_tier = 'Hot (≤ 3 giờ)'
    elif any(f'{h} giờ' in rel_l for h in range(4, 25)):
        rec_score = 32
        rec_tier = 'Hot (4 - 24 giờ)'
    elif any(x in rel_l for x in ['1 ngày', '2 ngày', '3 ngày']):
        rec_score = 28
        rec_tier = 'Hot (1 - 3 ngày)'
    elif any(f'{d} ngày' in rel_l for d in range(4, 8)) or ('1 tuần' in rel_l):
        rec_score = 20
        rec_tier = 'Warm (4 - 7 ngày)'
    elif any(f'{d} ngày' in rel_l for d in range(8, 15)) or ('2 tuần' in rel_l):
        rec_score = 15
        rec_tier = 'Warm (8 - 14 ngày)'
    elif any(f'{d} ngày' in rel_l for d in range(15, 31)) or any(f'{w} tuần' in rel_l for w in [3, 4]) or ('1 tháng' in rel_l):
        rec_score = 8
        rec_tier = 'Cool (15 - 30 ngày)'
    else:
        rec_score = 0
        rec_tier = 'Cold (> 30 ngày)'

    # GIAI ĐOẠN 3: PHÂN LOẠI ICP - TRỤC 2 (10 - 30 ĐIỂM)
    is_breeder = any(k in full_text for k in BREEDER_KW)
    is_training = any(k in full_text for k in TRAINING_KW)
    is_rescue = any(k in full_text for k in RESCUE_KW)
    is_pet_lover = any(re.search(p, full_text) for p in PET_LOVER_PATTERNS)
    
    if is_breeder and not is_pet_lover:
        icp_type = 'Dog Breeder / Commercial Kennel (B2B)'
        icp_score = 30
        prod_target = 'Puppy Starter Kit V2/V3 (Cỏ thoát nước + Potty Tray + Đồ chơi cắn in logo)'
    elif is_training:
        icp_type = 'Pet Training / K9 Academy / Grooming (B2B)'
        icp_score = 22
        prod_target = 'Cỏ nhân tạo lót sân chơi chịu lực + Đồ chơi huấn luyện dai/bền K9'
    elif is_rescue:
        icp_type = 'Pet Rescue / Shelter (B2B)'
        icp_score = 15
        prod_target = 'Tã lót Pee Pad thấm hút số lượng lớn + Khay vệ sinh tái sử dụng'
    else:
        icp_type = 'Pet Lover / Người Nuôi Cá Nhân (B2C)'
        icp_score = 10
        prod_target = 'Khay vệ sinh căn hộ / Thảm cỏ ban công / Đồ chơi xoa dịu'

    # GIAI ĐOẠN 4: GIÁ TRỊ THƯƠNG MẠI GIỐNG CHÓ - TRỤC 3 (0 - 15 Đ)
    breed_matches = [b for b in HIGH_VALUE_BREEDS if b in full_text]
    if len(breed_matches) >= 2:
        breed_score = 15
    elif len(breed_matches) == 1:
        breed_score = 10
    elif is_breeder:
        breed_score = 5
    else:
        breed_score = 0

    # GIAI ĐOẠN 5: HẠ TẦNG DOANH NGHIỆP & WEB - TRỤC 4 (0 - 10 Đ)
    has_web = bool(enriched.get('website'))
    has_biz_name = any(k in full_text for k in ['kennel', 'farm', 'academy', 'llc', 'ltd', 'resort'])
    infra_score = (5 if has_web else 0) + (5 if has_biz_name else 0)

    # GIAI ĐOẠN 6: UY TÍN SÀN AMAZON - TRỤC 5 (0 - 15 Đ)
    amz_cat = enriched.get('amz_cat', 'Amazon link not found')
    amz_link = enriched.get('amz_link', '')
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

    # GIAI ĐOẠN 7: KIỂM TRA ĐỊA LÝ & PHÂN TẦNG (MỤC 1.1 SKILL.md)
    intl = is_international(phone, location_str)
    country = 'International / Non-US' if intl else 'United States'
    
    if state in ['CO', 'MN', 'WI', 'IL', 'MI', 'NY', 'PA', 'OH', 'WA']:
        weather_trigger = 'Trigger 1 (Mưa lạnh/Tuyết rơi): Đẩy mạnh Thảm cỏ thoát nước & Khay vệ sinh trong nhà'
    elif state in ['AZ', 'NV', 'TX', 'FL', 'CA']:
        weather_trigger = 'Trigger 1 (Nắng nóng bỏng rát mặt đường): Đẩy giải pháp vệ sinh mát mẻ trong nhà'
    else:
        weather_trigger = 'Trigger 2 (Cún bị nhốt cuồng chân): Đẩy Đồ chơi cắn xoa dịu stress Snuggle Puppy'

    if intl:
        tier = 'International'
        action = '🌐 INTERNATIONAL: Gắn cờ thị trường mở rộng tương lai (Lưu phễu dự phòng, KHÔNG Telesale)'
    elif icp_type == 'Pet Lover / Người Nuôi Cá Nhân (B2C)':
        tier = 'Tier C (B2C)' if total_score >= 40 else 'Tier D (Cold)'
        action = '🛑 KHÔNG gọi điện Telesale. Chuyển sang tệp Retargeting Ads bán lẻ thảm cỏ/đồ chơi'
    else:
        if total_score >= 80:
            tier = 'Tier S'
            action = '🔥 TELESALE: Gọi chốt Take-Home Kit in logo độc quyền ngay trong ngày'
        elif total_score >= 65:
            tier = 'Tier A'
            action = '📞 TELESALE + EMAIL: Gửi báo giá sỉ Take-Home Kit V2/V3 + Telesale chăm sóc'
        elif total_score >= 50:
            tier = 'Tier B'
            action = '✉️ AUTOMATION: Nuôi dưỡng chuỗi email tự động giới thiệu danh mục sản phẩm'
        elif total_score >= 30:
            tier = 'Tier C'
            action = '💬 SOCIAL DM: Nhắn tin trực tiếp Fanpage/Instagram chi phí thấp'
        else:
            tier = 'Tier D'
            action = '❄️ ĐÓNG BĂNG: Lưu kho dự phòng, không tốn tài nguyên bán hàng'

    return {
        'STT': row_stt,
        'Master_ID': f"LEAD-FB-{row_idx+1:05d}",
        'Tên': name_str,
        'Trạng Thái Hồ Sơ': 'HỢP LỆ (Retained)',
        'Phân Loại ICP': icp_type,
        'Chi Tiết Phân Loại': f"Giống: {', '.join(breed_matches) if breed_matches else 'Chung'} | {rec_tier}",
        'Website': enriched.get('website', ''),
        'Điện Thoại': phone,
        'Email': enriched.get('email', ''),
        'Thành Phố': city,
        'Bang / State': state,
        'Quốc Gia': country,
        'Facebook URL': url,
        'Thời Gian Đăng': str(pub_time),
        'Độ Tươi Mới': str(rel_time),
        'Score_Recency': rec_score,
        'Score_ICP': icp_score,
        'Score_Breed': breed_score,
        'Score_Infra': infra_score,
        'Score_Amazon': amz_score,
        'Total_Score': total_score,
        'Phân Hạng (Tier)': tier,
        'Phân Loại Amazon': amz_cat,
        'Link Amazon': amz_link,
        'Sản Phẩm Mục Tiêu': prod_target,
        'Hành Động Đội Sales': action,
        'Ngữ Cảnh Thời Tiết': weather_trigger
    }

# XỬ LÝ TOÀN BỘ 5.993 DÒNG TỪ FB_PublishTime
print(f"[*] 2. Bắt đầu xử lý toàn bộ dữ liệu từ: {FB_CSV}...")
all_records = []
with open(FB_CSV, mode='r', encoding='utf-8', errors='ignore') as f:
    reader = csv.reader(f)
    header = next(reader, None)
    for idx, row in enumerate(reader):
        if len(row) < 6:
            continue
        stt, url, name, pub, ts, rel = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(), row[4].strip(), row[5].strip()
        rec = process_record(idx, stt, url, name, pub, rel)
        all_records.append(rec)

df_all = pd.DataFrame(all_records)
print(f"[✓] Đã xử lý xong {len(df_all)} dòng dữ liệu!")

# Tách thành các tập con theo nghiệp vụ
df_excluded = df_all[df_all['Trạng Thái Hồ Sơ'] == 'LOẠI BỎ (Excluded)'].copy()
df_valid = df_all[df_all['Trạng Thái Hồ Sơ'] == 'HỢP LỆ (Retained)'].copy()

df_tier_sa = df_valid[df_valid['Phân Hạng (Tier)'].isin(['Tier S', 'Tier A'])].sort_values(by='Total_Score', ascending=False)
df_tier_b = df_valid[df_valid['Phân Hạng (Tier)'] == 'Tier B'].sort_values(by='Total_Score', ascending=False)
df_pet_lovers = df_valid[df_valid['Phân Hạng (Tier)'].isin(['Tier C (B2C)', 'Tier D (Cold)']) & df_valid['Phân Loại ICP'].str.contains('Pet Lover')].sort_values(by='Total_Score', ascending=False)
df_intl = df_valid[df_valid['Phân Hạng (Tier)'] == 'International'].sort_values(by='Total_Score', ascending=False)

# Tạo bảng tổng quan Dashboard KPIs
total_count = len(df_all)
excluded_count = len(df_excluded)
valid_count = len(df_valid)
sa_count = len(df_tier_sa)
b_count = len(df_tier_b)
intl_count = len(df_intl)
pet_lover_count = len(df_pet_lovers)
breeder_count = len(df_valid[df_valid['Phân Loại ICP'].str.contains('Dog Breeder')])
training_count = len(df_valid[df_valid['Phân Loại ICP'].str.contains('Pet Training')])

dashboard_data = [
    {'Chỉ Số / Metric': 'Tổng số hồ sơ trong tệp cào Facebook ban đầu', 'Số Lượng': total_count, 'Tỷ Lệ (%)': '100.0%'},
    {'Chỉ Số / Metric': 'Số hồ sơ BỊ LOẠI BỎ (AKC, UKC, PetSmart, Meme, Thú Y, Rác)', 'Số Lượng': excluded_count, 'Tỷ Lệ (%)': f"{excluded_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': 'Số hồ sơ HỢP LỆ giữ lại xử lý tiếp thị', 'Số Lượng': valid_count, 'Tỷ Lệ (%)': f"{valid_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': ' - Trong đó: Dog Breeder / Commercial Kennel (B2B Vàng)', 'Số Lượng': breeder_count, 'Tỷ Lệ (%)': f"{breeder_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': ' - Trong đó: Pet Training & K9 Academy (B2B Dịch Vụ)', 'Số Lượng': training_count, 'Tỷ Lệ (%)': f"{training_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': ' - Trong đó: Pet Lover / Người Nuôi Cá Nhân (B2C Tách Riêng)', 'Số Lượng': pet_lover_count, 'Tỷ Lệ (%)': f"{pet_lover_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': '🔥 TỔNG HOT LEADS B2B NỘI ĐỊA MỸ (Tier S & Tier A - Telesale gọi ngay)', 'Số Lượng': sa_count, 'Tỷ Lệ (%)': f"{sa_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': '✉️ TỔNG TIỀM NĂNG B2B NỘI ĐỊA MỸ (Tier B - Email Automation)', 'Số Lượng': b_count, 'Tỷ Lệ (%)': f"{b_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': '🛑 TỔNG LEADS B2C BÁN LẺ (Tier C & D - Chỉ chạy Ads, KHÔNG Telesale)', 'Số Lượng': pet_lover_count, 'Tỷ Lệ (%)': f"{pet_lover_count/total_count*100:.1f}%"},
    {'Chỉ Số / Metric': '🌐 TỔNG ĐỐI TÁC QUỐC TẾ (Non-US - Lưu trữ phễu mở rộng tương lai)', 'Số Lượng': intl_count, 'Tỷ Lệ (%)': f"{intl_count/total_count*100:.1f}%"}
]
df_dashboard = pd.DataFrame(dashboard_data)

# XUẤT RA EXCEL ĐA SHEET CHUẨN MỰC
print(f"[*] 3. Đang xuất ra tệp Excel đa sheet: {OUT_EXCEL}...")
with pd.ExcelWriter(OUT_EXCEL, engine='openpyxl') as writer:
    df_dashboard.to_excel(writer, sheet_name='Tong_Quan_Dashboard', index=False)
    df_tier_sa.to_excel(writer, sheet_name='Tier_S_A_Hot_Leads_US', index=False)
    df_tier_b.to_excel(writer, sheet_name='Tier_B_Potential_US', index=False)
    df_pet_lovers.to_excel(writer, sheet_name='B2C_Pet_Lovers', index=False)
    df_intl.to_excel(writer, sheet_name='International_Backup', index=False)
    df_excluded.to_excel(writer, sheet_name='Excluded_Phi_Khach_Hang', index=False)
    df_all.to_excel(writer, sheet_name='Toan_Bo_Du_Lieu_Processed', index=False)

print(f"[✓] HOÀN TẤT! Đã tạo file thành công: {OUT_EXCEL}")
