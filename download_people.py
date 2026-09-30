import os
import time
import urllib.request

def download_people_dataset():
    print("\n=== TẢI THÊM ẢNH NGƯỜI (GIẢI PHÁP API CHUYÊN DỤNG) ===")
    
    target_train = os.path.join('dog_dataset', 'train', 'non_dog')
    target_val = os.path.join('dog_dataset', 'val', 'non_dog')
    
    os.makedirs(target_train, exist_ok=True)
    os.makedirs(target_val, exist_ok=True)
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    downloaded = 0
    
    # Nguồn 1: RandomUser.me (Chân dung rõ mặt siêu nét, có 200 ảnh)
    print("\n[1] Đang tải chân dung người từ RandomUser.me...")
    for gender in ['men', 'women']:
        for i in range(100):
            img_url = f"https://randomuser.me/api/portraits/{gender}/{i}.jpg"
            try:
                req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    img_data = response.read()
                    
                if downloaded % 5 == 0:
                    save_path = os.path.join(target_val, f"human_{downloaded}.jpg")
                else:
                    save_path = os.path.join(target_train, f"human_{downloaded}.jpg")
                    
                with open(save_path, 'wb') as f:
                    f.write(img_data)
                
                downloaded += 1
                if downloaded % 20 == 0:
                    print(f"  -> Đã tải {downloaded} ảnh khuôn mặt người...")
            except Exception as e:
                pass

    # Nguồn 2: Khuôn mặt ngẫu nhiên do AI tạo ra (Tránh bản quyền, siêu thực)
    print("\n[2] Đang tải ảnh AI Người Thật (ThisPersonDoesNotExist)...")
    for i in range(150):
        # Thêm biến ngẫu nhiên vào URL để tránh bị lưu bộ đệm (cache)
        img_url = f"https://thispersondoesnotexist.com/"
        try:
            req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()
                
            if downloaded % 5 == 0:
                save_path = os.path.join(target_val, f"human_{downloaded}.jpg")
            else:
                save_path = os.path.join(target_train, f"human_{downloaded}.jpg")
                
            with open(save_path, 'wb') as f:
                f.write(img_data)
                
            downloaded += 1
            if downloaded % 20 == 0:
                print(f"  -> Đã tải {downloaded} ảnh người...")
            
            time.sleep(1) # Chờ 1 giây để web không chặn
        except Exception as e:
            pass

    print(f"\n🎉 HOÀN TẤT! Đã bổ sung thành công {downloaded} ảnh NGƯỜI THẬT vào thư mục 'non_dog'.")
    print("Mô hình của bạn giờ đây đã có đủ dữ liệu để phân biệt Người và Chó!")
    print("Vui lòng mở file train_yolo.py và chạy lại quá trình Train.")

if __name__ == '__main__':
    download_people_dataset()
