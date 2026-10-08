import pandas as pd

file_path = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\fb_following_auto_1791431366633.csv"

# Đọc file CSV (Hỗ trợ BOM \uFEFF)
df = pd.read_csv(file_path, encoding='utf-8-sig')

# Đổi tên cột cho dễ xử lý nếu cần
cols = list(df.columns)
profile_col = cols[2] # Profile URL
name_col = cols[1]    # Họ và Tên
source_col = cols[4]  # Nguồn (Seed A)

# Làm sạch dữ liệu: Bỏ các link rác (l.php là link chuyển hướng của Facebook)
df = df[~df[profile_col].str.contains('l.php', na=False, case=False)]

# 1. Tìm HUBS (Những người được nhiều Seed A theo dõi nhất)
# Nhóm lại và thu thập danh sách những ai đã follow
hubs = df.groupby([profile_col, name_col])[source_col].agg(list).reset_index()
hubs['Mutual_Score'] = hubs[source_col].apply(len)
hubs['Followed_By'] = hubs[source_col].apply(lambda x: ', '.join(set(x))) # Lấy danh sách duy nhất
hubs = hubs.sort_values('Mutual_Score', ascending=False)

# 2. Tìm THEO DÕI CHÉO (Mutual Follows: A -> B và B -> A)
edges = set(zip(df[source_col], df[profile_col]))
mutuals = []
for src, tgt in edges:
    if (tgt, src) in edges and src < tgt: # src < tgt để tránh trùng lặp (A,B) và (B,A)
        mutuals.append((src, tgt))

# 3. Lọc danh sách TRẠI CHÓ / NGƯỜI BÁN (Breeders, Vets, Pets)
keywords = ['kennel', 'frenchie', 'frenchies', 'bulldog', 'bulldogs', 'bullies', 
            'pug', 'pugs', 'farm', 'rescue', 'vet', 'clinic', 'pet', 'dog', 'k9', 
            'care', 'animal', 'puppy', 'puppies', 'hound']

def is_breeder(name):
    name_lower = str(name).lower()
    for kw in keywords:
        if kw in name_lower:
            return True
    return False

breeders = hubs[hubs[name_col].apply(is_breeder)]

# In kết quả
print("=== KẾT QUẢ PHÂN TÍCH ĐỒ THỊ (SOCIAL GRAPH) ===")
print(f"Tổng số mối quan hệ cào được: {len(df):,} dòng")
print(f"Tổng số khách hàng/đối tác duy nhất: {len(hubs):,} người")
print(f"Số cặp theo dõi chéo (Mutual): {len(mutuals):,} cặp\n")

print("--- TOP 10 KHÁCH HÀNG 'VIP' (Được mạng lưới của bạn follow nhiều nhất) ---")
for idx, row in hubs.head(10).iterrows():
    print(f"[{row['Mutual_Score']} lượt liên kết] {row[name_col]} ({row[profile_col]})")

print("\n--- TOP 10 TRẠI CHÓ/NGƯỜI BÁN (Dựa trên nhận diện AI) ---")
for idx, row in breeders.head(10).iterrows():
    print(f"[{row['Mutual_Score']} lượt liên kết] {row[name_col]} ({row[profile_col]})")

print("\n--- CHI TIẾT NGƯỜI THEO DÕI: BlueRidgeVeterinaryImaging ---")
target_url = 'https://www.facebook.com/BlueRidgeVeterinaryImaging'
target_row = hubs[hubs[profile_col] == target_url]
if not target_row.empty:
    followers = target_row.iloc[0]['Followed_By'].split(', ')
    for i, follower in enumerate(followers, 1):
        print(f"{i}. {follower}")
else:
    print("Không tìm thấy dữ liệu!")

# Lưu kết quả ra file mới để tiện theo dõi
# Bỏ cột danh sách mảng thô (source_col) trước khi xuất
export_df = breeders.drop(columns=[source_col])
export_df.to_csv(r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\potential_breeders_list.csv", index=False, encoding='utf-8-sig')
print("\nĐã xuất danh sách Trại Chó tiềm năng ra file: potential_breeders_list.csv")
