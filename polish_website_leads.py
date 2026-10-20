# -*- coding: utf-8 -*-
import pandas as pd
import os

WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
CSV_PATH = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM_2026-10-15.csv")

df = pd.read_csv(CSV_PATH, dtype=str).fillna('')

for idx, row in df.iterrows():
    name = row['Họ và Tên (Breeder Name)']
    
    # 1. Down South Puppies
    if name == 'Down South Puppies':
        df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = 'Down South Puppies'
        df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium (Business Name Fallback)'
        df.at[idx, 'Thành Phố (City)'] = 'Beaumont'
        df.at[idx, 'Bang (State)'] = 'TX'
        df.at[idx, 'Quốc Gia (Country)'] = 'United States'
        
    # 2. Forever puppy
    elif name == 'Forever puppy':
        df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = 'Forever puppy'
        df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 2 - Medium (Business Name Fallback)'
        df.at[idx, 'Quốc Gia (Country)'] = 'United Kingdom'

    # 3. Blue Line Labradors
    elif name == 'Blue Line Labradors':
        df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = 'Laura & Faith Davis'
        df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 1 - High (Website Context Verified)'
        df.at[idx, 'Email'] = 'bluelinelabradors@gmail.com'
        df.at[idx, 'Thành Phố (City)'] = 'Caldwell'
        df.at[idx, 'Bang (State)'] = 'ID'
        df.at[idx, 'Quốc Gia (Country)'] = 'United States'

    # 4. Twisted Ranch Golden Retrievers
    elif name == 'Twisted Ranch Golden Retrievers':
        df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = 'Tiffany Craig'
        df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 1 - High (Website Owner & Breeder Verified)'
        df.at[idx, 'Thành Phố (City)'] = 'Placerville'
        df.at[idx, 'Bang (State)'] = 'CA'
        df.at[idx, 'Quốc Gia (Country)'] = 'United States'

    # 5. Daisy's Doodles
    elif name == "Daisy's Doodles":
        df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = 'Cassi Millsap'
        df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 1 - High (Website Founder / Director Verified)'
        df.at[idx, 'Số Điện Thoại (Phone)'] = '15072900645'
        df.at[idx, 'Email'] = 'cassimillsap@icloud.com'
        df.at[idx, 'Bang (State)'] = 'MN'
        df.at[idx, 'Quốc Gia (Country)'] = 'United States'

    # 6. Mountain Ash Labradoodles
    elif name == 'Mountain Ash Labradoodles':
        df.at[idx, 'Quốc Gia (Country)'] = 'Australia'
        df.at[idx, 'Thành Phố (City)'] = 'Melbourne'
        df.at[idx, 'Bang (State)'] = 'Victoria'
        df.at[idx, 'Email'] = 'asha@ashlab.au'

    # 7. Nosie Posie Puppies
    elif name == 'Nosie Posie Puppies':
        df.at[idx, 'Chủ Sở Hữu (Owner_Representative)'] = 'Christine (Chrissy)'
        df.at[idx, 'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'] = 'Tier 1 - High (Client Reviews Verified)'
        df.at[idx, 'Quốc Gia (Country)'] = 'United States'

    # 8. Signature Miniature Dachshunds LLC
    elif name == 'Signature Miniature Dachshunds LLC':
        df.at[idx, 'Bang (State)'] = 'CA'

# Đảm bảo format số điện thoại dạng chuỗi không có số mũ khoa học e+
for idx, row in df.iterrows():
    p = str(row['Số Điện Thoại (Phone)']).strip()
    if 'e+' in p:
        try:
            df.at[idx, 'Số Điện Thoại (Phone)'] = str(int(float(p)))
        except Exception:
            pass

df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
print("[✓] Đã tinh chỉnh và lưu thành công toàn bộ dữ liệu vào CSV!")

# Export ra Master Excel 4-sheet
export_script = os.path.join(WORKSPACE, 'export_master_styled_excel.py')
os.system(f'python "{export_script}"')
print("[✓] Đã cập nhật xong file Master Excel!")
