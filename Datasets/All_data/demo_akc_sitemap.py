import requests
from bs4 import BeautifulSoup

# 1. Truy cập vào bản đồ trang web (Sitemap) ẩn của AKC
sitemap_url = "https://marketplace.akc.org/sitemap.xml"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print("1. Đang tải sơ đồ trang web từ máy chủ AKC...")
response = requests.get(sitemap_url, headers=headers)

if response.status_code == 200:
    # 2. Phân tích mã XML
    soup = BeautifulSoup(response.content, 'xml')
    links = soup.find_all('loc')
    
    # 3. Lọc ra chỉ những đường link dẫn đến hồ sơ người dùng (Breeder)
    breeder_links = []
    for link in links:
        if '/breeder/' in link.text:
            breeder_links.append(link.text)
            
    print(f"Thành công! Tìm thấy {len(breeder_links)} nhà nhân giống (Breeders) ẩn trong hệ thống.")
    print("Dưới đây là 5 tài khoản đầu tiên:")
    for l in breeder_links[:5]:
        print("-", l)
        
    print("\n[HƯỚNG DẪN TIẾP THEO]")
    print("Người lập trình sẽ lưu danh sách hàng ngàn link này lại.")
    print("Sau đó cho con Bot truy cập vào từng link một để lấy Số điện thoại & Email.")
else:
    print(f"Thất bại. AKC đã phát hiện Bot và chặn (Mã lỗi: {response.status_code})")
