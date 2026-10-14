import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import concurrent.futures

# 1. Đọc file CSV bạn vừa tải về
df = pd.read_csv('dataset_crawler-google-places_2026-09-29_07-02-49-388.csv')
urls = df['website'].dropna().unique()

def extract_emails(url):
    try:
        # Giả lập trình duyệt để không bị chặn
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        # Dùng Biểu thức chính quy (Regex) để quét toàn bộ email trên web
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text))
        return url, list(emails)
    except:
        return url, []

# 2. Chạy tự động nhiều luồng để web cào nhanh hơn
results = []
print(f"Bắt đầu quét {len(urls)} website để lấy Email...")

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    for url, emails in executor.map(extract_emails, urls):
        if emails:
            print(f"Tìm thấy: {url} -> {emails}")
            results.append({"Website": url, "Emails": ", ".join(emails)})

# 3. Xuất ra file Excel hoàn chỉnh
output_df = pd.DataFrame(results)
output_df.to_csv('danh_sach_email_khach_hang.csv', index=False)
print("Hoàn tất! Đã lưu vào danh_sach_email_khach_hang.csv")