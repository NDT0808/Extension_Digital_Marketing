import os
import re
import pandas as pd
from urllib.parse import urlparse

WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
MASTER_EXCEL = os.path.join(WORKSPACE, "Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx")

OUT_FULL_XLSX = os.path.join(WORKSPACE, "US_Leads_Websites_For_Amazon_Pipeline_Full.xlsx")
OUT_HOT_XLSX = os.path.join(WORKSPACE, "US_Hot_Leads_Websites_For_Amazon_Pipeline.xlsx")
OUT_CSV = os.path.join(WORKSPACE, "US_Customer_Websites_Cleaned.csv")
OUT_TXT = os.path.join(WORKSPACE, "US_Customer_Websites_List.txt")

print("--- 1. ĐỌC DỮ LIỆU TỪ MASTER EXCEL 2026 ---")
df_all = pd.read_excel(MASTER_EXCEL, sheet_name='All_US_Valid_Leads')
print(f"Tổng số hồ sơ nội địa Mỹ: {len(df_all)}")

# Hàm làm sạch và bóc tách website thực
junk_domains = ['bing.com', 'google.com', 'maps.google.com', 'waze.com', 'apple.com', 'mailto:']
social_domains = ['facebook.com', 'instagram.com', 'youtube.com', 'tiktok.com', 'twitter.com', 'x.com']

def clean_and_extract_website(raw_val):
    if not raw_val or pd.isna(raw_val):
        return ""
    
    parts = [p.strip() for p in str(raw_val).split('|') if p.strip()]
    candidates = []
    
    for p in parts:
        if any(j in p.lower() for j in junk_domains):
            continue
        try:
            if not p.startswith(('http://', 'https://')):
                p = 'https://' + p
            parsed = urlparse(p)
            netloc = parsed.netloc.lower()
            if not netloc or '.' not in netloc:
                continue
            # Bỏ tracking params (fbclid, utm...)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
            if not clean.endswith(('http:/', 'https:/')):
                candidates.append(clean)
        except:
            continue
            
    if not candidates:
        return ""
        
    # Ưu tiên domain độc lập trước, nếu không có mới lấy link mxh
    for c in candidates:
        if not any(s in c.lower() for s in social_domains):
            return c
    return candidates[0]

def extract_domain(url):
    try:
        p = urlparse(url)
        d = p.netloc.lower()
        if d.startswith('www.'):
            d = d[4:]
        return d
    except:
        return ""

print("--- 2. LÀM SẠCH VÀ LỌC CÁC WEBSITE KHÁCH HÀNG MỸ ---")
df_all['Clean_Website'] = df_all['Website'].apply(clean_and_extract_website)
df_has_web = df_all[df_all['Clean_Website'] != ''].copy()
df_has_web['Domain'] = df_has_web['Clean_Website'].apply(extract_domain)

# Chuẩn bị DataFrame cho Pipeline (Khớp đúng tên cột mà check_amazon_sales_pipeline.py cần)
df_pipeline = pd.DataFrame({
    'Master_ID': df_has_web['Master_ID'],
    'Breeder Name': df_has_web['Breeder_Name'],
    'Website': df_has_web['Clean_Website'],
    'Domain': df_has_web['Domain'],
    'City': df_has_web['City'],
    'State': df_has_web['State'],
    'Zip_Code': df_has_web['Zip_Code'],
    'Phone': df_has_web['Phone'],
    'Email': df_has_web['Email'],
    'Tier_Rank': df_has_web['Tier_Rank'],
    'Total_Lead_Score': df_has_web['Total_Lead_Score'],
    'ICP_Segment': df_has_web['ICP_Segment'],
    'Target_Products': df_has_web['Target_Products'],
    'Amazon Link': df_has_web['Amazon_Link'],
    'Phân loại Amazon': df_has_web['Amazon_Status']
})

print(f"[✓] Tổng số khách hàng Mỹ có Website hợp lệ: {len(df_pipeline)} (Số domain độc nhất: {df_pipeline['Domain'].nunique()})")

# 1. Xuất file đầy đủ 6.330 leads
df_pipeline.to_excel(OUT_FULL_XLSX, sheet_name='US_Leads_Websites', index=False)
print(f"[✓] Đã tạo file quét Amazon đầy đủ: {OUT_FULL_XLSX}")

# 2. Xuất file Hot Leads Cấp A (Điểm >= 61) - 1.388 leads
df_hot_web = df_pipeline[df_pipeline['Total_Lead_Score'] >= 61].copy()
df_hot_web.to_excel(OUT_HOT_XLSX, sheet_name='US_Hot_Leads_Websites', index=False)
print(f"[✓] Đã tạo file quét Hot Leads Cấp A (Khuyên dùng chạy trước): {OUT_HOT_XLSX} ({len(df_hot_web)} leads)")

# 3. Xuất file CSV & TXT danh sách URL
df_urls = df_pipeline[['Master_ID', 'Breeder Name', 'Website', 'Domain', 'State', 'Total_Lead_Score']].drop_duplicates(subset=['Website'])
df_urls.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')
print(f"[✓] Đã tạo file CSV danh sách Website: {OUT_CSV}")

with open(OUT_TXT, 'w', encoding='utf-8') as f:
    for u in df_urls['Website'].unique():
        f.write(f"{u}\n")
print(f"[✓] Đã tạo file TXT danh sách URL thuần: {OUT_TXT} ({len(df_urls)} URLs)")

print("\n" + "=" * 80)
print("HOÀN TẤT BÓC TÁCH WEBSITE KHÁCH HÀNG NỘI ĐỊA HOA KỲ!")
print(f" 1. File đầy đủ (6.330 khách hàng Mỹ): {OUT_FULL_XLSX}")
print(f" 2. File Hot Leads ưu tiên (1.388 khách hàng Cấp A): {OUT_HOT_XLSX}")
print(f" 3. File CSV: {OUT_CSV}")
print(f" 4. File TXT: {OUT_TXT}")
print("=" * 80)
