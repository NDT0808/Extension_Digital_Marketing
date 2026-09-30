import os
import urllib.request
import time

def auto_download_images():
    print("\n=== TỰ ĐỘNG TẢI LẠI ẢNH 'NON_DOG' (NGƯỜI VÀ PHONG CẢNH) ===")
    base_dir = 'dog_dataset'
    
    # Số lượng ảnh cần tải cho Non-Dog
    limit_train = 1000
    limit_val = 200
    
    for split, limit in [('train', limit_train), ('val', limit_val)]:
        print(f"\n--- ĐANG TẢI DỮ LIỆU CHO THƯ MỤC: {split.upper()} ---")
        
        target_folder = os.path.join(base_dir, split, 'non_dog')
        os.makedirs(target_folder, exist_ok=True)
        
        current_count = len(os.listdir(target_folder))
        if current_count >= limit:
            print(f"✅ Thư mục '{split}/non_dog' đã đủ {limit} ảnh.")
            continue
            
        print(f"\n⏳ Đang tải {limit} ảnh đời sống, con người, phong cảnh (Picsum)...")
        
        for i in range(current_count, limit):
            try:
                # Dùng Picsum Photos: Cung cấp ảnh chụp ngẫu nhiên cực đẹp về người, phong cảnh, đường phố
                # Thêm tham số ngẫu nhiên theo thời gian để ảnh không bị trùng
                img_url = f"https://picsum.photos/400/400?random={i}_{int(time.time())}"
                
                img_path = os.path.join(target_folder, f"bg_{i}.jpg")
                
                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response, open(img_path, 'wb') as out_file:
                    out_file.write(response.read())
                
                if (i + 1) % 50 == 0:
                    print(f"  -> Tải thành công {i + 1}/{limit} ảnh")
                    
                time.sleep(0.1) # Tránh bị chặn
            except Exception as e:
                print(f"  -> Lỗi tải ảnh thứ {i}: {e}")
                    
    print(f"\n✅ Đã chuẩn bị xong toàn bộ ảnh NON_DOG tại '{base_dir}/'. BẠN CÓ THỂ BẮT ĐẦU TRAIN LẠI!")

if __name__ == '__main__':
    auto_download_images()
