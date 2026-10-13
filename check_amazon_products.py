import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import re
import urllib.parse

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

toy_keywords = [' toy', '-toy', ' toys', ' chew', ' plush ', ' rope ']
potty_keywords = [' grass ', ' potty ', ' toilet', ' pee pad', ' turf', ' litter']

def get_amazon_links_from_url(url):
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'amazon.com' in href.lower() or 'amzn.to' in href.lower():
                links.add(href)
        return links
    except:
        return set()

def check_amazon_products(amz_url):
    try:
        if not amz_url.startswith('http'):
            amz_url = 'https://' + amz_url
        r = requests.get(amz_url, headers=headers, timeout=10, verify=False)
        text = r.text.lower()
        
        has_toy = any(kw in text for kw in toy_keywords)
        has_potty = any(kw in text for kw in potty_keywords)
        return has_toy, has_potty
    except:
        return False, False

print("Đọc ket_qua_amazon.xlsx...")
df_amz = pd.read_excel('ket_qua_amazon.xlsx')
websites = df_amz['Website'].tolist()

results = {}

for w in websites:
    w_clean = w.strip()
    if not w_clean.startswith('http'): w_clean = 'https://' + w_clean
    print(f"Đang xử lý: {w_clean}")
    
    # Get links on the homepage
    amz_links = set()
    try:
        r = requests.get(w_clean, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # find direct amazon links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'amazon' in href.lower() or 'amzn.to' in href.lower():
                # If it's a relative link to internal page
                if href.startswith('/'):
                    internal_url = urllib.parse.urljoin(w_clean, href)
                    internal_links = get_amazon_links_from_url(internal_url)
                    amz_links.update(internal_links)
                elif 'amazon.com' in href.lower() or 'amzn.to' in href.lower():
                    amz_links.add(href)
                else:
                    internal_url = urllib.parse.urljoin(w_clean, href)
                    internal_links = get_amazon_links_from_url(internal_url)
                    amz_links.update(internal_links)
    except Exception as e:
        print(f"Lỗi truy cập {w_clean}: {e}")
        
    print(f"  -> Tìm thấy {len(amz_links)} link Amazon")
    
    found_toy = False
    found_potty = False
    
    for al in amz_links:
        t, p = check_amazon_products(al)
        if t: found_toy = True
        if p: found_potty = True
        if found_toy and found_potty:
            break
            
    note = []
    if found_toy:
        note.append("Đồ chơi thú cưng")
    if found_potty:
        note.append("Cỏ nhân tạo/Nhà vệ sinh (MỤC TIÊU)")
        
    if note:
        results[w] = "Bán: " + " + ".join(note)
    elif amz_links:
        results[w] = "Có link Amazon nhưng không thấy bán đồ chơi hay nhà vệ sinh"
    else:
        results[w] = "Không tìm thấy link Amazon trực tiếp"

print("\nKết quả:")
for k, v in results.items():
    print(f"{k}: {v}")

print("\nCập nhật priority_list_2026-10-06_v2.xlsx...")
df_priority = pd.read_excel('priority_list_2026-10-06_v2.xlsx')
if 'Amazon Check Note' not in df_priority.columns:
    df_priority['Amazon Check Note'] = ""

for i, row in df_priority.iterrows():
    web = str(row['Website']).strip()
    if pd.isna(row['Website']):
        continue
    # Tìm web trong results
    for k, v in results.items():
        if web in k or k in web:
            df_priority.at[i, 'Amazon Check Note'] = v
            break

output_file = 'priority_list_updated.xlsx'
df_priority.to_excel(output_file, index=False)
print(f"Đã lưu kết quả vào {output_file}")