import pandas as pd
import requests
import re
import concurrent.futures
import glob
import os

# 1. Read all apify datasets in the directory
csv_files = glob.glob('dataset_crawler-google-places_*.csv')
places_list = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        if not df.empty:
            places_list.append(df)
    except pd.errors.EmptyDataError:
        print(f"Bỏ qua file rỗng: {file}")

if not places_list:
    print("No datasets found.")
    exit()

places_df = pd.concat(places_list, ignore_index=True)

# Keep necessary columns
cols_to_keep = ['title', 'website', 'phone', 'postalCode', 'city', 'state', 'countryCode']
places_df = places_df[[c for c in cols_to_keep if c in places_df.columns]]
places_df = places_df.dropna(subset=['website']).drop_duplicates(subset=['website'])

urls = places_df['website'].tolist()
print(f"Tổng số website cần quét: {len(urls)}")

# 2. Extract emails
def extract_emails(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text))
        return url, list(emails)
    except:
        return url, []

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    for url, emails in executor.map(extract_emails, urls):
        if emails:
            results.append({"Website": url, "Emails": ", ".join(emails)})

emails_df = pd.DataFrame(results)

# 3. Merge and process for FB custom audience
merged_df = pd.merge(places_df, emails_df, left_on='website', right_on='Website', how='inner')

out_data = []

def is_valid_email(e):
    e = e.strip().lower()
    if not e: return False
    if 'sentry.io' in e or 'sentry.wixpress.com' in e or 'sentry-next' in e: return False
    if 'example.com' in e or 'domain.com' in e or 'your@email.com' in e or 'email.com' == e.split('@')[-1]: return False
    if e.endswith('.png') or e.endswith('.jpg') or e.endswith('.gif') or e.endswith('.webp'): return False
    return True

cities_count = {}
states_count = {}

for _, row in merged_df.iterrows():
    raw_emails = str(row.get('Emails', '')).split(',')
    valid_emails = [e.strip() for e in raw_emails if is_valid_email(e)]
    
    if not valid_emails:
        continue
    
    email1 = valid_emails[0] if len(valid_emails) > 0 else ''
    email2 = valid_emails[1] if len(valid_emails) > 1 else ''
    email3 = valid_emails[2] if len(valid_emails) > 2 else ''
    
    phone = str(row.get('phone', '')).strip()
    if phone == 'nan': phone = ''
    
    zip_code = str(row.get('postalCode', '')).strip()
    if zip_code.endswith('.0'): zip_code = zip_code[:-2]
    if zip_code == 'nan': zip_code = ''
    
    city = str(row.get('city', '')).strip()
    if city == 'nan': city = 'Unknown'
    
    state = str(row.get('state', '')).strip()
    if state == 'nan': state = 'Unknown'
    
    country = str(row.get('countryCode', '')).strip()
    if country == 'nan': country = ''
    
    out_data.append({
        'email': email1,
        'email_2': email2,
        'email_3': email3,
        'phone': phone,
        'phone_2': '',
        'phone_3': '',
        'madid': '',
        'fn': '',
        'ln': '',
        'zip': zip_code,
        'ct': city,
        'st': state,
        'country': country,
        'dob': '',
        'doby': '',
        'gen': '',
        'age': '',
        'uid': '',
        'value': ''
    })
    
    cities_count[city] = cities_count.get(city, 0) + 1
    states_count[state] = states_count.get(state, 0) + 1

out_df = pd.DataFrame(out_data)
if len(out_df) > 0:
    out_df.columns = ['email', 'email', 'email', 'phone', 'phone', 'phone', 'madid', 'fn', 'ln', 'zip', 'ct', 'st', 'country', 'dob', 'doby', 'gen', 'age', 'uid', 'value']

out_file = 'danh_sach_chay_quang_cao_tong_hop.csv'
out_df.to_csv(out_file, index=False)
print(f"Đã lưu {len(out_df)} khách hàng vào {out_file}")

# 4. Generate Markdown Report
top_cities = sorted(cities_count.items(), key=lambda x: x[1], reverse=True)[:5]
top_states = sorted(states_count.items(), key=lambda x: x[1], reverse=True)[:5]

report = f"""# Báo cáo Thu thập Dữ liệu Khách hàng (Thú cưng)
**Ngày báo cáo:** 29/09/2026

## 1. Tổng quan chiến dịch
- **Nguồn dữ liệu:** Google Maps (qua Apify)
- **Tổng số file dữ liệu gốc đã tải:** {len(csv_files)} file
- **Tổng số doanh nghiệp quét được:** {len(places_df)} doanh nghiệp (đã lọc trùng lặp)

## 2. Kết quả trích xuất Email & Số điện thoại
- **Tổng số website đã quét email:** {len(urls)} website
- **Số lượng khách hàng hợp lệ (có email/sđt):** {len(out_df)} khách hàng
- **Tỷ lệ chuyển đổi dữ liệu thành công:** {round(len(out_df)/len(places_df)*100, 2)}%

## 3. Phân bổ khu vực (Top)
### Top 5 Thành phố:
"""
for c, count in top_cities:
    report += f"- {c}: {count} cơ sở\n"

report += "\n### Top 5 Tiểu bang:\n"
for s, count in top_states:
    report += f"- {s}: {count} cơ sở\n"

report += f"""
## 4. File bàn giao
Dữ liệu đã được làm sạch, định dạng chuẩn Facebook Ads Custom Audience (bao gồm các trường: email, phone, zip, ct, st, country) và lưu tại file: `{out_file}`.
"""

with open('Bao_Cao_Tong_Hop.md', 'w', encoding='utf-8') as f:
    f.write(report)
print("Đã tạo báo cáo Bao_Cao_Tong_Hop.md")
