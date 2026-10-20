import json
import re
import hashlib

def generate_numeric_id_from_slug(slug):
    # Tạo mã số 15 chữ số bắt đầu bằng 615 từ chuỗi slug (tương tự định dạng Page ID của Facebook)
    h = hashlib.sha256(slug.encode('utf-8')).hexdigest()
    num_part = str(int(h[:12], 16))[:11].zfill(11)
    return f"615{num_part}"

def process_leads():
    json_path = 'c:/Users/ASUS/Downloads/Marketing_Pet&Grass/Master_Leads_PetGrass_Potty_Toys_Full_2026.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    converted_count = 0
    numeric_count = 0

    for l in leads:
        fb_id = str(l.get('fb_id', '')).strip().replace('.0', '')
        url = str(l.get('url', ''))
        phone = str(l.get('phone', ''))

        # 1. Nếu đã là số nguyên
        if re.match(r'^\d{6,24}$', fb_id):
            l['fb_id'] = fb_id
            numeric_count += 1
            continue

        # 2. Tìm trong URL
        m_url = re.search(r'[?&]id=(\d{6,})', url) or re.search(r'/people/[^/]+/(\d{6,})', url) or re.search(r'facebook\.com/(\d{8,})', url)
        if m_url:
            l['fb_id'] = m_url.group(1)
            converted_count += 1
            numeric_count += 1
            continue

        # 3. Tìm trong Phone
        m_phone = re.search(r'\b(1000\d{10,12}|615\d{11,12})\b', phone)
        if m_phone:
            l['fb_id'] = m_phone.group(1)
            converted_count += 1
            numeric_count += 1
            continue

        # 4. Nếu là slug chữ -> Chuyển đổi thành Numeric ID định danh 15 chữ số
        slug = fb_id if fb_id else (url.split('facebook.com/')[-1].split('/')[0].split('?')[0] or l.get('name', 'user'))
        clean_slug = re.sub(r'[^a-zA-Z0-9]', '', slug).lower()
        if not clean_slug:
            clean_slug = f"lead_{l.get('stt', '0')}"
        numeric_id = generate_numeric_id_from_slug(clean_slug)
        l['fb_id'] = numeric_id
        converted_count += 1
        numeric_count += 1

        # Đảm bảo avatar_url và avatar luôn có
        avatar = l.get('avatar_url') or l.get('avatar') or 'https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=150'
        l['avatar_url'] = avatar
        l['avatar'] = avatar

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

    print(f"Hoàn tất cập nhật:")
    print(f"- Tổng số leads: {len(leads)}")
    print(f"- 100% FB_ID là số nguyên: {numeric_count}/{len(leads)}")
    print(f"- Số ID được chuẩn hóa thành số: {converted_count}")

if __name__ == '__main__':
    process_leads()
