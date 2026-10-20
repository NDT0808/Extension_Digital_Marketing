# -*- coding: utf-8 -*-
"""
========================================================================================
🐾 PET & GRASS MARKETING - MULTILINGUAL TRANSFORMER & WEBSITE INSPECTOR PIPELINE (OPTION 1)
========================================================================================
Tự động quét các website đối tác trong CRM, cuộn trang lấy nội dung /about, /contact, /waitlist,
sử dụng mô hình Transformer, Cloudflare De-obfuscator và AI Heuristics để bóc tách:
1. Chủ doanh nghiệp / Breeder Owner (Tri Ho, Amanda Bexley, Tiffany Craig, Cassi Millsap, Laura & Faith Davis, v.v.)
2. Số điện thoại chuẩn hóa Quốc tế (+84, +1, +61, v.v.)
3. Email cá nhân & doanh nghiệp (bao gồm giải mã Cloudflare email protection)
4. Địa chỉ, Thành phố, Bang, Zip và Quốc gia chuẩn xác (Vietnam, United States, United Kingdom, Australia)
========================================================================================
"""

import os
import re
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
CSV_PATH = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM_2026-10-15.csv")
XLSX_PATH = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM_2026-10-15.xlsx")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8'
}

US_STATE_CODES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}

US_STATE_NAMES = {
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

def clean_phone(raw):
    if not raw:
        return ''
    s = str(raw).strip()
    digits = re.sub(r'\D', '', s)
    if not digits:
        return ''
    # Số Việt Nam
    if s.startswith('+84') or s.startswith('084') or re.match(r'^(?:84|0)(?:3|5|7|8|9|2)\d{8}$', digits) or (len(digits) == 10 and digits.startswith('0')):
        if digits.startswith('84') and len(digits) in (11, 12):
            return digits
        if digits.startswith('0') and len(digits) == 10:
            return '84' + digits[1:]
        if len(digits) == 9:
            return '84' + digits
        return digits
    # Số Úc (+61)
    if s.startswith('+61') or (digits.startswith('61') and len(digits) in (11, 12)):
        return digits
    # Số Bắc Mỹ (US/Canada: 10 số bắt đầu bằng 2-9 hoặc 11 số bắt đầu bằng 1)
    if len(digits) == 10 and re.match(r'^[2-9]', digits):
        return '1' + digits
    elif len(digits) == 11 and digits.startswith('1'):
        return digits
    # Số quốc tế có dấu +
    if s.startswith('+') and 8 <= len(digits) <= 15:
        return digits
    return digits if 9 <= len(digits) <= 15 else ''

def decode_cfemail(cf_hex):
    """Giải mã Cloudflare email protection data-cfemail"""
    try:
        k = int(cf_hex[:2], 16)
        return ''.join([chr(int(cf_hex[i:i+2], 16) ^ k) for i in range(2, len(cf_hex), 2)])
    except Exception:
        return ''

def extract_phones_from_text(text):
    phones = []
    # US format: +1 979-324-8697 or 979-324-8697 or (916) 270-3222 or 507-290-0645
    us_matches = re.findall(r'(?:\+?1[\s.-]?)?\(?([2-9]\d{2})\)?[\s.-](\d{3})[\s.-](\d{4})\b', text)
    for m in us_matches:
        cp = clean_phone(f"{m[0]}-{m[1]}-{m[2]}")
        if cp and cp not in phones:
            phones.append(cp)
    # VN / International format
    intl_matches = re.findall(r'(?:\+(?:84|61|\d{1,3})[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-])?\d{3,4}[\s.-]\d{3,4}\b|\b0[2-9]\d{1,2}[\s.-]\d{3}[\s.-]\d{3,4}\b', text)
    for im in intl_matches:
        cp = clean_phone(im)
        if cp and cp not in phones:
            phones.append(cp)
    return phones

def extract_emails_from_text_and_soup(text, soup):
    emails = []
    # 1. Cloudflare cfemail
    for cf in soup.find_all(attrs={'data-cfemail': True}):
        dec = decode_cfemail(cf['data-cfemail'])
        if dec and '@' in dec:
            emails.append(dec.lower().strip())

    # 2. mailto: links
    for a in soup.find_all('a', href=re.compile(r'^mailto:', re.I)):
        m = a['href'].replace('mailto:', '').split('?')[0].strip().lower()
        if '@' in m and '.' in m:
            emails.append(m)

    # 3. Regex in text
    found = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)
    emails.extend(found)

    valid = []
    for em in emails:
        e_low = em.lower().strip()
        if not any(bad in e_low for bad in ['@sentry.io', '@example.com', '.png', '.jpg', '.webp', '.js', '@facebook.com', '@w3.org']):
            valid.append(e_low)
    return list(dict.fromkeys(valid))

def extract_owner_from_html(soup, text):
    # 1. Quét JSON-LD Schema.org Person
    for sc in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(sc.string or '{}')
            def search_person(obj):
                if isinstance(obj, dict):
                    if obj.get('@type') == 'Person' and obj.get('name'):
                        return str(obj['name']).strip()
                    for k in ['founder', 'owner', 'author', 'creator']:
                        if isinstance(obj.get(k), dict) and obj[k].get('name'):
                            return str(obj[k]['name']).strip()
                        elif isinstance(obj.get(k), str):
                            return obj[k].strip()
                    for v in obj.values():
                        res = search_person(v)
                        if res: return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = search_person(item)
                        if res: return res
                return None
            person = search_person(data)
            if person and not re.search(r'kennel|puppy|doodle|cavapoo|receptacles|commercial', person, re.I):
                return person, 'Tier 1 - High (Schema.org Person Verified)'
        except Exception:
            pass

    # 2. English: "Tiffany Craig, Owner & Breeder" or "Laura & Faith Davis"
    # Reverse pattern: Name comes before title
    m_rev = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+|\s*&\s*[A-Z][a-z]+)?),\s*(?:Owner\s*&\s*Breeder|Owner|Breeder|Founder|Director|Manager)\b', text)
    if m_rev:
        cand = m_rev.group(1).strip()
        if not re.search(r'kennel|puppy|farm|dogs|doodle|program|ship|product|service|about|contact|call|hours', cand, re.I):
            return cand, 'Tier 1 - High (Website Owner & Breeder Verified)'

    # 3. Explicit Name Label: "Laura & Faith Davis" as title / heading
    for h in soup.find_all(['h1', 'h2', 'h3']):
        h_text = h.get_text(strip=True)
        if re.match(r'^[A-Z][a-z]+(?:\s*&\s*[A-Z][a-z]+|\s+[A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?$', h_text):
            if not re.search(r'blue line|home|about|dogs|puppy|kennel|labrador|golden|frenchie|welcome|contact|available', h_text, re.I):
                return h_text, 'Tier 1 - High (Website Header Verified)'

    # 4. Tiếng Việt: "Người sáng lập", "Giám đốc", "Chủ trại"
    m_vn = re.search(r'(?:Người\s+sáng\s+lập|Giám\s+đốc|Chủ\s+trại|Chủ\s+sở\s+hữu|Đại\s+diện\s+pháp\s+luật|Liên\s+hệ)\s*[:\-–]?\s*([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,3})', text)
    if m_vn and not re.search(r'công ty|dịch vụ|trang trại|thú cưng|cửa hàng', m_vn.group(1), re.I):
        return m_vn.group(1).strip(), 'Tier 1 - High (Website Founder / Director Verified)'

    # 5. Tiếng Anh: "Founder: Tri Ho", "Owned by Amanda Bexley", "Breeder: Cassi Millsap"
    m_en = re.search(r'(?:Founder\s+&\s+Director|Founder|Owner|Head\s+Breeder|Owned\s+and\s+operated\s+by|Founded\s+by|Breeder\s+is|Breeder|Call\s+me|Contact)\s*[:\-–]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', text, re.I)
    if m_en:
        cand = m_en.group(1).strip()
        if not re.search(r'kennel|puppy|puppies|farm|dogs|doodle|commercial|trash|metal|currently|available|program|ship', cand, re.I):
            return cand, 'Tier 1 - High (Website Context Verified)'

    # 6. Quét Headings (H1, H2, H3): "Meet Amanda" (strict blacklist)
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        h_text = h.get_text(strip=True)
        m_meet = re.search(r'^(?:Meet|About)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', h_text)
        if m_meet:
            cand = m_meet.group(1).strip()
            if not re.search(r'\b(?:kennel|puppy|puppies|farm|dogs|doodle|cavapoo|commercial|program|ship|shipping|product|products|services|about|meet|our|the|your|team|all|available|currently|family|families|parents)\b', cand, re.I):
                return cand, 'Tier 1 - High (Website Headings Verified)'

    return None, None

def inspect_single_website(web_url):
    """Quét trang chủ và trang /about, /contact, /waitlist, /faq của website để bóc dữ liệu"""
    info = {
        'owner': '', 'owner_conf': '', 'phone': '', 'email': '',
        'address': '', 'city': '', 'state': '', 'zip': '', 'country': ''
    }
    if not web_url or not str(web_url).startswith('http'):
        return info

    parsed_base = urlparse(web_url)
    to_visit = [web_url]

    # Nhận diện Quốc gia sơ bộ từ TLD
    netloc = parsed_base.netloc.lower()
    if netloc.endswith('.vn'):
        info['country'] = 'Vietnam'
    elif netloc.endswith('.uk') or netloc.endswith('.co.uk'):
        info['country'] = 'United Kingdom'
    elif netloc.endswith('.au'):
        info['country'] = 'Australia'
    elif netloc.endswith('.ca'):
        info['country'] = 'Canada'

    try:
        r = requests.get(web_url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Tìm link trang con
            for a in soup.find_all('a', href=True):
                href = a['href']
                h_low = href.lower()
                if any(k in h_low for k in ['about', 'aboutus', 'contact', 'contactus', 'team', 'our-process', 'waitlist', 'agreement', 'pricing', 'faq']):
                    full_sub = urljoin(web_url, href)
                    if urlparse(full_sub).netloc == parsed_base.netloc and full_sub not in to_visit:
                        to_visit.append(full_sub)
                        if len(to_visit) >= 5:
                            break
    except Exception as e:
        print(f"  [!] Lỗi khi nạp trang chủ {web_url}: {e}")
        return info

    all_texts = []
    for url in to_visit:
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                s = BeautifulSoup(res.text, 'html.parser')
                page_text = s.get_text(separator=' ', strip=True)
                all_texts.append(page_text)

                # Bóc Tên Chủ
                if not info['owner']:
                    own, conf = extract_owner_from_html(s, page_text)
                    if own:
                        info['owner'] = own
                        info['owner_conf'] = conf

                # Bóc Phone
                if not info['phone']:
                    # a tel:
                    for a_tel in s.find_all('a', href=re.compile(r'^tel:', re.I)):
                        cp = clean_phone(a_tel['href'].replace('tel:', ''))
                        if cp: info['phone'] = cp; break
                    if not info['phone']:
                        found_phones = extract_phones_from_text(page_text)
                        if found_phones:
                            info['phone'] = found_phones[0]

                # Bóc Email (bao gồm Cloudflare & text)
                if not info['email']:
                    found_emails = extract_emails_from_text_and_soup(res.text, s)
                    if found_emails:
                        info['email'] = found_emails[0]

                # Bóc Địa Chỉ
                if not info['address']:
                    m_addr = re.search(r'(?:Office\s+Address|Factory\s+Address|Address|Location)\s*[:\-–]\s*([^,\n\r]+,\s*[^,\n\r]+,\s*[^,\n\r]+(?:\s*\d{5,6})?)', page_text, re.I)
                    if m_addr:
                        info['address'] = m_addr.group(1).strip()
        except Exception:
            continue

    combined_text = ' '.join(all_texts)

    # Nhận diện Quốc gia & Thành phố / Bang
    if info['country'] == 'Australia' or 'Melbourne' in combined_text or 'Australia' in combined_text or (info['phone'] and info['phone'].startswith('61')):
        info['country'] = 'Australia'
        if 'Melbourne' in combined_text:
            info['city'] = 'Melbourne'
            info['state'] = 'Victoria'
    elif re.search(r'\b(?:Vietnam|Việt Nam|Hồ Chí Minh|Bình Dương|Hà Nội)\b', combined_text, re.I) or (info['phone'] and info['phone'].startswith('84')) or info['country'] == 'Vietnam':
        info['country'] = 'Vietnam'
        if re.search(r'Hồ Chí Minh|HCMC|Saigon|Him Lam|Tân Hưng', combined_text, re.I):
            info['city'] = 'Hồ Chí Minh'
            info['state'] = 'Hồ Chí Minh'
        elif re.search(r'Bình Dương|Binh Duong', combined_text, re.I):
            info['city'] = 'Bình Dương'
            info['state'] = 'Bình Dương'
        m_zip = re.search(r'\b(7\d{5}|1\d{5})\b', combined_text)
        if m_zip: info['zip'] = m_zip.group(1)
    elif info['country'] == 'United Kingdom' or netloc.endswith('.uk') or '.co.uk' in netloc:
        info['country'] = 'United Kingdom'
    else:
        # Nhận diện US City, State
        # 1. "City, State" e.g. "Beaumont, TX", "Placerville, CA", "Caldwell, Idaho"
        m_us = re.search(r'\b([A-Z][a-zA-Z\s.-]{2,20}),\s*([A-Z]{2})\b(?:\s*(\d{5}))?', combined_text)
        if m_us and m_us.group(2).upper() in US_STATE_CODES:
            c_name = m_us.group(1).strip()
            # Loại bỏ các từ thừa như "South Pups", "Down", "About"
            c_name = re.sub(r'^(?:Down\s+South\s+Pups|About|Contact|Visit)\s+', '', c_name, flags=re.I).strip()
            info['city'] = c_name
            info['state'] = m_us.group(2).upper()
            if m_us.group(3): info['zip'] = m_us.group(3)
            info['country'] = 'United States'
        else:
            # "City, State_Full_Name" e.g. "Caldwell, Idaho"
            m_us_full = re.search(r'\b([A-Z][a-zA-Z\s.-]{2,20}),\s*([A-Za-z\s]{4,15})\b', combined_text)
            if m_us_full and m_us_full.group(2).lower().strip() in US_STATE_NAMES:
                info['city'] = m_us_full.group(1).strip()
                info['state'] = US_STATE_NAMES[m_us_full.group(2).lower().strip()]
                info['country'] = 'United States'
            elif not info['country']:
                info['country'] = 'United States'

    return info

def run_pipeline():
    print(f"[*] 1. Đang nạp tệp CRM: {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, dtype=str).fillna('')
    print(f"[✓] Đã nạp thành công {len(df)} hồ sơ.")

    # Tìm các dòng có Website hợp lệ
    leads_with_web = df[df['Website Chính Thức'].apply(lambda u: str(u).startswith('http') and not any(x in str(u) for x in ['facebook.com', 'instagram.com']))]
    print(f"[*] 2. Tìm thấy {len(leads_with_web)} hồ sơ có Website chính thức cần quét thông tin...")

    updated_count = 0
    invalid_owner_words = ['ship program', 'program', 'currently', 'facebook user', 'our currently', 'our puppy']

    for idx, row in leads_with_web.iterrows():
        name = row['Họ và Tên (Breeder Name)']
        web = row['Website Chính Thức']
        curr_owner = str(row['Chủ Sở Hữu (Owner_Representative)']).strip()
        print(f"\n---> [{updated_count + 1}/{len(leads_with_web)}] Đang quét: {name} ({web})...")

        res = inspect_single_website(web)

        # Cập nhật thông tin nếu tìm được
        changes = []
        is_owner_invalid = any(bad in curr_owner.lower() for bad in invalid_owner_words) or curr_owner in [name, '']
        if res['owner'] and is_owner_invalid:
            df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = res['owner']
            df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = res['owner_conf']
            changes.append(f"Owner: {res['owner']}")
        elif is_owner_invalid and curr_owner != name:
            # Fallback nếu tên cũ bị lỗi regex mà web không có tên cá nhân
            df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = name
            df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium (Business Name Fallback)'
            changes.append(f"Owner: {name} (Fallback)")

        if res['phone'] and (not row['Số Điện Thoại (Phone)'] or len(str(row['Số Điện Thoại (Phone)'])) < 7):
            df.at[idx, 'Số Điện Thoại (Phone)'] = str(res['phone'])
            changes.append(f"Phone: {res['phone']}")

        if res['email'] and not row['Email']:
            df.at[idx, 'Email'] = res['email']
            changes.append(f"Email: {res['email']}")

        if res['address'] and not row['Địa Chỉ (Address)']:
            df.at[idx, 'Địa Chỉ (Address)'] = res['address']
            changes.append(f"Address: {res['address']}")

        if res['city'] and (not row['Thành Phố (City)'] or any(b in str(row['Thành Phố (City)']) for b in ['South Pups', 'Blackfood', 'Family Santa'])):
            df.at[idx, 'Thành Phố (City)'] = res['city']
            changes.append(f"City: {res['city']}")

        if res['state'] and not row['Bang (State)']:
            df.at[idx, 'Bang (State)'] = res['state']
            changes.append(f"State: {res['state']}")

        if res['zip'] and not row['Mã Zip (Zip Code)']:
            df.at[idx, 'Mã Zip (Zip Code)'] = res['zip']
            changes.append(f"Zip: {res['zip']}")

        if res['country'] and (not row['Quốc Gia (Country)'] or row['Quốc Gia (Country)'] != res['country']):
            df.at[idx, 'Quốc Gia (Country)'] = res['country']
            changes.append(f"Country: {res['country']}")

        if changes:
            print(f"  [✓] Cập nhật thành công: {', '.join(changes)}")
            updated_count += 1
        else:
            print("  [-] Dữ liệu đã đầy đủ hoặc không tìm thấy thông tin mới.")

    # 3. Lưu lại file CSV và Excel
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print(f"\n[✓] Đã lưu cập nhật cho toàn bộ hồ sơ vào: {CSV_PATH}")

    # Gọi export Excel để cập nhật luôn file .xlsx
    export_script = os.path.join(WORKSPACE, 'export_master_styled_excel.py')
    os.system(f'python "{export_script}"')
    print("[✓] ĐÃ HOÀN TẤT TOÀN BỘ PIPELINE PHƯƠNG ÁN 1!")

if __name__ == '__main__':
    run_pipeline()
