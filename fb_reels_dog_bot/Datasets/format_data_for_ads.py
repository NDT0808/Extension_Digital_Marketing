import csv
import os

source_file = r'c:\Users\ASUS\Downloads\plugin_marketing\fb_reels_dog_bot\Datasets\fb_pages_1790945055646.csv'
target_file = r'c:\Users\ASUS\Downloads\plugin_marketing\fb_reels_dog_bot\Datasets\fb_pages_adv_format.csv'

with open(source_file, 'r', encoding='utf-8-sig') as f_in, open(target_file, 'w', encoding='utf-8', newline='') as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    
    header = ['email','email','email','phone','phone','phone','madid','fn','ln','zip','ct','st','country','dob','doby','gen','age','uid','value']
    writer.writerow(header)
    
    count = 0
    for row in reader:
        email = row.get('Email', '').strip()
        phone = row.get('Điện thoại', '').strip()
        name = row.get('Tên', '').strip()
        
        # Lọc ra nếu có email hoặc số điện thoại
        if email or phone:
            fn = ''
            ln = ''
            if name:
                parts = name.split(' ', 1)
                fn = parts[0]
                if len(parts) > 1:
                    ln = parts[1]
            
            out_row = [email, '', '', phone, '', '', '', fn, ln, '', '', '', '', '', '', '', '', '', '']
            writer.writerow(out_row)
            count += 1

print(f"Đã trích xuất {count} bản ghi có chứa Email hoặc Số điện thoại vào file fb_pages_adv_format.csv")
