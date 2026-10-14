import pandas as pd
import glob

# Read all Outscraper xlsx files
xlsx_files = glob.glob('Outscraper-*.xlsx')
if not xlsx_files:
    print("Không tìm thấy file Excel nào từ Outscraper.")
    exit()

places_list = []
for file in xlsx_files:
    df = pd.read_excel(file)
    places_list.append(df)

df = pd.concat(places_list, ignore_index=True)

# Map Outscraper columns to our standard format
rename_map = {
    'name': 'title',
    'postal_code': 'postalCode',
    'state_code': 'state',
    'country_code': 'countryCode'
}
df = df.rename(columns=rename_map)

# Keep only what we need
cols_to_keep = ['title', 'website', 'phone', 'postalCode', 'city', 'state', 'countryCode']
df = df[[c for c in cols_to_keep if c in df.columns]]

# Drop rows without website
df = df.dropna(subset=['website']).drop_duplicates(subset=['website'])

# Save as dataset_crawler-google-places_outscraper.csv so tong_hop.py picks it up
out_name = 'dataset_crawler-google-places_outscraper.csv'
df.to_csv(out_name, index=False)
print(f"Đã chuyển đổi thành công {len(df)} doanh nghiệp từ file Excel Outscraper sang chuẩn chung!")
