import pandas as pd
import re
import warnings

# Bỏ qua các cảnh báo không cần thiết
warnings.filterwarnings('ignore')

def parse_followers(val):
    if pd.isna(val) or str(val).strip() == '':
        return 0
    # Xử lý chuỗi (ví dụ: '5,5K', '51 triệu', '1.1K')
    val = str(val).strip().replace(',', '.')
    if 'triệu' in val.lower():
        num = float(val.lower().replace('triệu', '').strip())
        return int(num * 1000000)
    if 'k' in val.lower():
        num = float(val.lower().replace('k', '').strip())
        return int(num * 1000)
    try:
        # Xóa dấu chấm phân cách nghìn nếu có
        return int(val.replace('.', ''))
    except:
        return 0

# Đọc file CSV (sử dụng engine python để tránh lỗi quote)
file_path = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\fb_contacts_1791274576538.csv"
try:
    df = pd.read_csv(file_path, on_bad_lines='skip')
except Exception as e:
    print(f"Lỗi đọc file: {e}")
    exit()

# 1. Chuyển đổi cột 'Người theo dõi' sang số
df['Follower_Count'] = df['Người theo dõi'].apply(parse_followers)

# 2. Điều kiện 1: Số lượng Follower từ 2.000 đến 30.000
mask_followers = (df['Follower_Count'] >= 2000) & (df['Follower_Count'] <= 30000)

# 3. Điều kiện 2: Có thông tin liên hệ (Email HOẶC Điện thoại)
# Đảm bảo NaN được xem là rỗng
df['Email'] = df['Email'].fillna('')
df['Điện thoại'] = df['Điện thoại'].fillna('')
mask_contact = (df['Email'].str.strip() != '') | (df['Điện thoại'].str.strip() != '')

# 4. Điều kiện 3: Bio (Giới thiệu) chứa từ khóa ngách
# Tập từ khóa liên quan đến chó/thú cưng
niche_keywords = ['dog', 'puppy', 'puppies', 'kennel', 'breeder', 'retriever', 'spaniel', 'hound', 'doodle', 'dachshund', 'poodle', 'frenchie', 'pet', 'vet']
def has_niche_keyword(bio):
    if pd.isna(bio): return False
    bio_lower = str(bio).lower()
    return any(kw in bio_lower for kw in niche_keywords)

df['Is_Niche'] = df['Giới thiệu'].apply(has_niche_keyword)

# Áp dụng bộ lọc
filtered_df = df[mask_followers & mask_contact]

# Sắp xếp ưu tiên: Niche = True trước, sau đó Follower giảm dần
filtered_df = filtered_df.sort_values(by=['Is_Niche', 'Follower_Count'], ascending=[False, False])

# Lưu ra file mới để bạn tiện sử dụng
output_path = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\seed_A_candidates.csv"
filtered_df.to_csv(output_path, index=False, encoding='utf-8-sig')

# In kết quả báo cáo
print(f"=== KẾT QUẢ LỌC HẠT GIỐNG ===")
print(f"- Tổng số data đầu vào: {len(df)}")
print(f"- Số hạt giống (Seed A) lý tưởng tìm được: {len(filtered_df)}")
print(f"\n[TOP 5 HẠT GIỐNG TỐT NHẤT]")
for index, row in filtered_df.head(5).iterrows():
    print(f"🔗 Link: {row['Link Profile']}")
    print(f"   Followers: {row['Người theo dõi']}")
    contact = []
    if row['Email']: contact.append(row['Email'])
    if row['Điện thoại']: contact.append(row['Điện thoại'])
    print(f"   Liên hệ: {' | '.join(contact)}")
    print(f"   Đúng ngách: {'Có' if row['Is_Niche'] else 'Không'}")
    print(f"   Bio: {str(row['Giới thiệu'])[:80]}...\n")
    
print(f"Đã xuất file kết quả tại: {output_path}")
