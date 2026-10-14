import pandas as pd
import glob

# Read all chunks
csv_files = glob.glob('chunk*.csv')
if not csv_files:
    print("Không tìm thấy file chunk nào.")
    exit()

df_list = []
for file in csv_files:
    df = pd.read_csv(file)
    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)

# Map columns
rename_map = {
    '商家名称': 'title',
    '官网': 'website',
    '电话': 'phone',
    '地址': 'street'
}
df = df.rename(columns=rename_map)

# Keep only what we need
cols_to_keep = ['title', 'website', 'phone', 'street']
df = df[[c for c in cols_to_keep if c in df.columns]]

# Drop rows without website
df = df.dropna(subset=['website']).drop_duplicates(subset=['website'])

# Save as dataset_crawler-google-places_chinese.csv so tong_hop.py picks it up
out_name = 'dataset_crawler-google-places_chinese.csv'
df.to_csv(out_name, index=False)
print(f"Đã chuyển đổi thành công {len(df)} doanh nghiệp từ file tiếng Trung sang chuẩn chung!")
