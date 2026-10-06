import pandas as pd
import re

# Read the places dataset
places_df = pd.read_csv('dataset_crawler-google-places_2026-09-29_07-02-49-388.csv')
# Keep only necessary columns from places to save memory
cols_to_keep = ['website', 'phone', 'postalCode', 'city', 'state', 'countryCode']
places_df = places_df[[c for c in cols_to_keep if c in places_df.columns]]
places_df = places_df.dropna(subset=['website']).drop_duplicates(subset=['website'])

# Read the emails dataset
emails_df = pd.read_csv('danh_sach_email_khach_hang.csv')
emails_df = emails_df.dropna(subset=['Website']).drop_duplicates(subset=['Website'])

# Merge datasets
merged_df = pd.merge(places_df, emails_df, left_on='website', right_on='Website', how='inner')

# Required columns for the output CSV
# email,email,email,phone,phone,phone,madid,fn,ln,zip,ct,st,country,dob,doby,gen,age,uid,value

out_data = []

# Sentry / dummy email filter
def is_valid_email(e):
    e = e.strip().lower()
    if not e: return False
    if 'sentry.io' in e or 'sentry.wixpress.com' in e or 'sentry-next' in e: return False
    if 'example.com' in e or 'domain.com' in e or 'your@email.com' in e or 'email.com' == e.split('@')[-1]: return False
    if e.endswith('.png') or e.endswith('.jpg'): return False
    return True

for _, row in merged_df.iterrows():
    raw_emails = str(row.get('Emails', '')).split(',')
    valid_emails = [e.strip() for e in raw_emails if is_valid_email(e)]
    
    if not valid_emails:
        # We need at least one valid email to be useful in a custom audience in most cases
        continue
    
    email1 = valid_emails[0] if len(valid_emails) > 0 else ''
    email2 = valid_emails[1] if len(valid_emails) > 1 else ''
    email3 = valid_emails[2] if len(valid_emails) > 2 else ''
    
    phone = str(row.get('phone', '')).strip()
    if phone == 'nan': phone = ''
    
    zip_code = str(row.get('postalCode', '')).strip()
    if zip_code.endswith('.0'):
        zip_code = zip_code[:-2]
    if zip_code == 'nan': zip_code = ''
    
    city = str(row.get('city', '')).strip()
    if city == 'nan': city = ''
    
    state = str(row.get('state', '')).strip()
    if state == 'nan': state = ''
    
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

out_df = pd.DataFrame(out_data)
# Rename columns back to duplicate names as required by the template
out_df.columns = ['email', 'email', 'email', 'phone', 'phone', 'phone', 'madid', 'fn', 'ln', 'zip', 'ct', 'st', 'country', 'dob', 'doby', 'gen', 'age', 'uid', 'value']

out_file = 'danh_sach_chay_quang_cao.csv'
out_df.to_csv(out_file, index=False)
print(f"Hoàn tất! Đã lưu {len(out_df)} khách hàng vào {out_file}")
