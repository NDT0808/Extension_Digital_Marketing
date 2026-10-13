import pandas as pd
import requests
from bs4 import BeautifulSoup

file_path = "priority_list_2026-10-06_v2.xlsx"
df = pd.read_excel(file_path, sheet_name="Priority List")

# Lọc danh sách website hợp lệ
websites = df["Website"].dropna().unique().tolist()
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
}

results = []
print(f"Bắt đầu quét {len(websites)} trang web...\n")

for idx, raw_url in enumerate(websites, 1):
    url = raw_url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text().lower()
            links = [
                a.get("href", "").lower() for a in soup.find_all("a", href=True)
            ]

            # Kiểm tra keyword trong văn bản hoặc đường dẫn liên kết
            has_amazon_text = "amazon" in text
            has_amazon_link = any("amazon" in href for href in links)

            if has_amazon_text or has_amazon_link:
                results.append(
                    {
                        "Website": raw_url,
                        "Status": "Có chứa Amazon",
                        "In_Text": has_amazon_text,
                        "In_Links": has_amazon_link,
                    }
                )
                print(f"[{idx}/{len(websites)}] [PHÁT HIỆN]: {raw_url}")
            else:
                print(f"[{idx}/{len(websites)}] Không có: {raw_url}")
        else:
            print(
                f"[{idx}/{len(websites)}] Lỗi HTTP {response.status_code}: {raw_url}"
            )
    except Exception as e:
        print(f"[{idx}/{len(websites)}] Lỗi kết nối: {raw_url}")

# Lưu kết quả ra file mới
output_df = pd.DataFrame(results)
output_df.to_excel("ket_qua_amazon.xlsx", index=False)
print(f"\nHoàn tất! Đã lưu kết quả vào 'ket_qua_amazon.xlsx'.")