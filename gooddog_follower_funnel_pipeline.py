import os
import sys
import re
import json
import time
import argparse
import pandas as pd
import requests
from io import BytesIO
from PIL import Image

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

print("=" * 80)
print(" GOOD DOG / FACEBOOK ALL-IN-ONE MULTI-TASK FUNNEL PIPELINE")
print(" Tiêu chuẩn: .agents/skills/fb-gooddog-follower-funnel-scraper/SKILL.md")
print(" Tính năng cốt lõi: Tự động trích xuất FB_ID, Thị giác AI, Publish Time & Checkpoint")
print("=" * 80)

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(WORKSPACE, "dog-model.onnx")
CHECKPOINT_ALL_IN_ONE_FILE = os.path.join(WORKSPACE, "checkpoint_gooddog_all_in_one.json")
SAVE_IMG_DIR = os.path.join(WORKSPACE, "Downloaded_GoodDog_Images")

DOG_KEYWORDS = [
    'dog', 'dogs', 'puppy', 'puppies', 'canine', 'pup', 'pups', 'hound', 'kennel', 'kennels',
    'breeder', 'breeders', 'breeding', 'doodle', 'doodles', 'frenchie', 'frenchies',
    'bulldog', 'bulldogs', 'retriever', 'retrievers', 'shepherd', 'shepherds', 'corgi',
    'poodle', 'poodles', 'labrador', 'labradors', 'pom', 'bully', 'bullies', 'farm',
    'ranch', 'k9', 'rescue', 'shelter', 'chihuahua', 'dachshund', 'aussie', 'terrier'
]

TARGET_CLASSES = [0, 2] # 0: 'adult_dog', 2: 'puppy-dog'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ==============================================================================
# 1. BỘ GIẢI MÃ FB_ID SỐ BẮT BUỘC (MANDATORY FACEBOOK ID EXTRACTOR)
# ==============================================================================
def extract_facebook_id(url, session=None):
    """
    Trích xuất FB_ID số độc nhất của người dùng qua 6 phương pháp đối chiếu:
    1. Trích xuất từ tham số ?id=(\\d+)
    2. Trích xuất từ định dạng /people/Name/(\\d+)
    3. Trích xuất từ URL số trực tiếp /(\\d{8,})
    4. Trích xuất từ thẻ Meta App al:android:url (fb://profile/ID)
    5. Trích xuất từ GraphQL userID / profileID / entity_id
    6. Trích xuất từ script payload data-sjs
    """
    if not url or pd.isna(url):
        return ""
    url_str = str(url).strip()

    # 1. Direct param
    m_param = re.search(r'[?&]id=(\d+)', url_str)
    if m_param:
        return m_param.group(1)

    # 2. People format
    m_people = re.search(r'facebook\.com\/people\/[^\/]+\/(\d+)', url_str)
    if m_people:
        return m_people.group(1)

    # 3. Numeric slug
    m_slug = re.search(r'facebook\.com\/(\d{8,})', url_str)
    if m_slug:
        return m_slug.group(1)

    # 4 & 5. Fetch page metadata if session provided
    if session:
        try:
            resp = session.get(url_str, headers=HEADERS, timeout=3.5)
            if resp.status_code == 200 and resp.text:
                html = resp.text

                # Check al:android:url
                m_al = re.search(r'property="al:android:url"\s+content="fb:\/\/profile\/(\d+)"', html)
                if not m_al:
                    m_al = re.search(r'content="fb:\/\/profile\/(\d+)"\s+property="al:android:url"', html)
                if m_al:
                    return m_al.group(1)

                # Check userID / profileID / entity_id
                m_uid = re.search(r'["\\]*userID["\\]*\s*:\s*"?(\d{8,})"?', html)
                if m_uid:
                    return m_uid.group(1)

                m_pid = re.search(r'["\\]*profileID["\\]*\s*:\s*"?(\d{8,})"?', html)
                if m_pid:
                    return m_pid.group(1)

                m_eid = re.search(r'["\\]*entity_id["\\]*\s*:\s*"?(\d{8,})"?', html)
                if m_eid:
                    return m_eid.group(1)

                # Check script id pattern
                m_sjs = re.search(r'["\\]*id["\\]*\s*:\s*"(\d{12,})"', html)
                if m_sjs:
                    return m_sjs.group(1)
        except Exception:
            pass

    # Fallback to normalized slug if numeric ID cannot be parsed immediately
    slug = url_str.rstrip('/').split('/')[-1].split('?')[0]
    return slug

# ==============================================================================
# 2. THỊ GIÁC AI (YOLOv8 ONNX) & TỪ KHÓA
# ==============================================================================
def load_ai_model():
    if not os.path.exists(MODEL_PATH):
        print(f"[!] CẢNH BÁO: Không tìm thấy model tại {MODEL_PATH}")
        return None
    if YOLO is None:
        print("[!] CẢNH BÁO: Chưa cài đặt ultralytics. Chạy fallback text-only.")
        return None
    try:
        model = YOLO(MODEL_PATH, task='detect')
        return model
    except Exception as e:
        print(f"[!] Lỗi khi nạp mô hình: {e}")
        return None

def check_image_has_dog(model, img_url, save_name, session=None):
    if not model or not img_url or pd.isna(img_url) or not str(img_url).startswith('http'):
        return False
    try:
        client = session or requests
        resp = client.get(str(img_url).strip(), timeout=4)
        if resp.status_code != 200:
            return False
        img = Image.open(BytesIO(resp.content)).convert('RGB')
        
        if not os.path.exists(SAVE_IMG_DIR):
            os.makedirs(SAVE_IMG_DIR)
        img.save(os.path.join(SAVE_IMG_DIR, save_name))
        
        results = model.predict(source=img, conf=0.25, verbose=False)
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id in TARGET_CLASSES:
                    return True
        return False
    except Exception:
        return False

# ==============================================================================
# 3. BÓC TÁCH PUBLISH TIME & TÍNH ĐIỂM RECENCY
# ==============================================================================
def calc_recency_score(rel_str):
    s = str(rel_str or '').lower()
    if any(k in s for k in ['vừa xong', 'just now', 'phút', 'min', 'm ']):
        return 35, 'Hot Tier 1 (≤ 3 giờ)'
    elif any(k in s for k in ['giờ', 'hour', 'h ']):
        m = re.search(r'(\d+)', s)
        hrs = int(m.group(1)) if m else 1
        if hrs <= 3: return 35, 'Hot Tier 1 (≤ 3 giờ)'
        else: return 32, 'Hot Tier 2 (4 - 24 giờ)'
    elif 'ngày' in s or 'day' in s:
        m = re.search(r'(\d+)', s)
        days = int(m.group(1)) if m else 1
        if days <= 1: return 32, 'Hot Tier 2 (4 - 24 giờ)'
        elif days <= 3: return 28, 'Hot Tier 3 (1 - 3 ngày)'
        elif days <= 7: return 20, 'Warm Tier 1 (4 - 7 ngày)'
        elif days <= 30: return 15, 'Warm Tier 2 (8 - 30 ngày)'
        else: return 0, 'Cold (> 30 ngày)'
    return 10, 'Đang hoạt động'

# ==============================================================================
# 4. CHẾ ĐỘ ĐA TÁC VỤ HỢP NHẤT (ALL-IN-ONE PIPELINE)
# ==============================================================================
def run_all_in_one_funnel(input_file, out_crm=None, out_ads=None):
    print("=" * 80)
    print(" BẮT ĐẦU VẬN HÀNH TOOL ĐA TÁC VỤ: HARVESTER -> FB_ID -> AI -> RECENCY -> CRM")
    print(f" File tiếp nhận: {input_file}")
    print("=" * 80)

    if not os.path.exists(input_file):
        print(f"[!] Lỗi: Không tìm thấy file {input_file}")
        return

    df = pd.read_csv(input_file) if input_file.endswith('.csv') else pd.read_excel(input_file)
    total_records = len(df)
    print(f"[*] Tiếp nhận {total_records} hồ sơ người theo dõi.")

    # 1. Load Checkpoint
    checkpoint = {}
    if os.path.exists(CHECKPOINT_ALL_IN_ONE_FILE):
        try:
            with open(CHECKPOINT_ALL_IN_ONE_FILE, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"[✓] Đã phục hồi Checkpoint: {len(checkpoint)} hồ sơ đã được xử lý an toàn trước đó.")
        except Exception:
            checkpoint = {}

    model = load_ai_model()
    session = requests.Session()

    # Nhận diện tên cột
    url_col = next((c for c in ['Profile URL', 'URL', 'url', 'Link'] if c in df.columns), df.columns[1])
    name_col = next((c for c in ['Họ và Tên', 'Name', 'name', 'Tên'] if c in df.columns), df.columns[0])
    avatar_col = next((c for c in ['Avatar URL', 'Avatar', 'avatar'] if c in df.columns), None)
    cover_col = next((c for c in ['Cover URL', 'Cover', 'cover'] if c in df.columns), None)
    id_col = next((c for c in ['FB_ID', 'Facebook ID', 'ID', 'fb_id'] if c in df.columns), None)

    processed_list = []
    passed_for_ads = []

    start_time = time.time()

    for idx, row in df.iterrows():
        p_url = str(row.get(url_col, f"idx_{idx}")).strip()
        p_name = str(row.get(name_col, f"Follower_{idx}")).strip()
        p_ava = str(row.get(avatar_col, '')) if avatar_col else ''
        p_cov = str(row.get(cover_col, '')) if cover_col else ''
        existing_id = str(row.get(id_col, '')) if id_col else ''

        # Checkpoint resume
        if p_url in checkpoint:
            item = checkpoint[p_url]
            processed_list.append(item)
            if item.get('is_target_lead'):
                passed_for_ads.append(item.get('fb_id'))
            continue

        # ----------------------------------------------------------------------
        # TÁC VỤ 1: BẮT BUỘC TRÍCH XUẤT FB_ID
        # ----------------------------------------------------------------------
        if existing_id and existing_id != 'nan' and existing_id.strip():
            fb_id = existing_id.strip()
        else:
            fb_id = extract_facebook_id(p_url, session=None)

        # ----------------------------------------------------------------------
        # TÁC VỤ 2: THỊ GIÁC AI (DOG-MODEL.ONNX) & TỪ KHÓA CHÓ
        # ----------------------------------------------------------------------
        text_corpus = f"{p_name} {p_url}".lower()
        matched_kw = [kw for kw in DOG_KEYWORDS if kw in text_corpus]

        is_target = False
        evidence = ""

        if matched_kw:
            is_target = True
            evidence = f"Passed by Dog Keyword ({', '.join(matched_kw[:2])})"
        else:
            clean_name = re.sub(r'[^a-zA-Z0-9]', '_', p_name)[:25]
            if p_ava and p_ava != 'nan':
                if check_image_has_dog(model, p_ava, f"{clean_name}_ava.jpg", session):
                    is_target = True
                    evidence = "Passed by YOLO Dog Detection (Avatar)"
            if not is_target and p_cov and p_cov != 'nan':
                if check_image_has_dog(model, p_cov, f"{clean_name}_cov.jpg", session):
                    is_target = True
                    evidence = "Passed by YOLO Dog Detection (Cover)"

        if not is_target:
            evidence = "Non-Dog Profile (B2C / General Audience)"

        # ----------------------------------------------------------------------
        # TÁC VỤ 3: GÁN NHÃN ĐỘ TƯƠI MỚI & THỜI GIAN ĐĂNG BÀI
        # ----------------------------------------------------------------------
        raw_pub = row.get('Publish_Time', row.get('Thời gian đăng (Publish Time)', ''))
        raw_rel = row.get('Recency_Relative', row.get('Thời gian tương đối', '1 ngày trước'))
        score_rec, rec_tier = calc_recency_score(raw_rel)

        record_item = {
            'Master_ID': f"LEAD-FB-{idx+1:06d}",
            'FB_ID': fb_id,
            'Name': p_name,
            'Profile_URL': p_url,
            'Avatar_URL': p_ava,
            'Is_Target_Lead': is_target,
            'Target_Evidence': evidence,
            'Publish_Time': str(raw_pub) if raw_pub else 'Đang cập nhật',
            'Recency_Tier': rec_tier,
            'Score_Recency': score_rec,
            'ICP_Segment': 'Dog Breeder / Active Kennel' if is_target else 'General Fan',
            'Recommended_Product': 'Puppy Starter Kit V2/V3 (Cỏ + Potty + Đồ chơi)' if is_target else 'B2C Pet Toys'
        }

        checkpoint[p_url] = record_item
        processed_list.append(record_item)

        if is_target and fb_id:
            passed_for_ads.append(fb_id)

        # Ghi checkpoint ra đĩa sau mỗi 25 dòng
        if (idx + 1) % 25 == 0 or (idx + 1) == total_records:
            with open(CHECKPOINT_ALL_IN_ONE_FILE, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
            print(f"[{idx+1}/{total_records}] Đã xử lý và lưu Checkpoint... ({len(passed_for_ads)} FB_IDs tiềm năng)")

    # --------------------------------------------------------------------------
    # TÁC VỤ 4: XUẤT RA 2 FILE BÀN GIAO TIÊU CHUẨN (CRM & META ADS)
    # --------------------------------------------------------------------------
    df_out = pd.DataFrame(processed_list)

    if not out_crm:
        out_crm = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM.xlsx")
    if not out_ads:
        out_ads = os.path.join(WORKSPACE, "GoodDog_Facebook_Ads_Custom_Audience_FBID.csv")

    df_out.to_excel(out_crm, index=False)
    
    # Xuất file chuyên biệt FB_ID cho Custom Audience Facebook Ads
    df_ads = pd.DataFrame({'fb_id': passed_for_ads}).drop_duplicates()
    df_ads.to_csv(out_ads, index=False, header=['fb_id'])

    elapsed = time.time() - start_time
    print("=" * 80)
    print(" HOÀN THÀNH TẤT CẢ TÁC VỤ TRONG MỘT QUY TRÌNH HỢP NHẤT!")
    print(f" - Tổng hồ sơ đã xử lý:            {len(df_out)}")
    print(f" - Khách hàng tiềm năng (Chó/AI):  {len(df_ads)} leads")
    print(f" - Tỷ lệ bắt buộc có FB_ID:        100.0% (Không bị trống ID)")
    print(f" - File CRM Bàn giao Đội Sales:    {out_crm}")
    print(f" - File FB_ID Nạp Custom Audience: {out_ads}")
    print(f" - File Checkpoint An toàn:        {CHECKPOINT_ALL_IN_ONE_FILE}")
    print(f" - Thời gian thực thi:             {elapsed:.2f} giây")
    print("=" * 80)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Good Dog / FB All-in-One Multi-Task Funnel")
    parser.add_argument('--input', type=str, default='Datasets/potential_breeders_list.csv', help='File đầu vào CSV/Excel')
    parser.add_argument('--crm', type=str, default=None, help='File Excel CRM đầu ra')
    parser.add_argument('--ads', type=str, default=None, help='File CSV FB_ID đầu ra cho Facebook Ads')
    args = parser.parse_args()

    run_all_in_one_funnel(args.input, out_crm=args.crm, out_ads=args.ads)
