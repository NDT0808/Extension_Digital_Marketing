---
name: fb-gooddog-follower-funnel-scraper
description: Kỹ năng quét toàn bộ người theo dõi / đang theo dõi từ trang cá nhân Facebook (Personal Profile Followers & Following) & Fanpage, chuyển giao dữ liệu sang Python chạy mô hình AI thị giác YOLOv8-cls (dog-model.onnx 224x224 RGB) kết hợp từ khóa nhận diện chó, bóc tách bộ sưu tập ảnh và tải ảnh đánh số theo FB_ID, xuất kết quả Excel & JSON LEAD-US chuẩn Meta RAG.
---

# Kỹ năng: Facebook Personal Profile Follower Scraper & Python AI Dog Vision Funnel

> [!IMPORTANT]
> **MỤC TIÊU CỐT LÕI & QUY TRÌNH 4 BƯỚC KHÉP KÍN:**
> 1. **Bước 1 - Quét Người theo dõi & Đang theo dõi (Personal Profile Followers & Following)**:
>    - Tiện ích mở rộng `fb_following_scraper` tự động nhận diện và quét mượt mà cả danh sách **Người theo dõi** (`/followers`, `?sk=followers`) và **Đang theo dõi** (`/following`, `?sk=following`) của bất kỳ **Trang cá nhân (Personal Profile)** hoặc Fanpage nào.
>    - Tự động phát hiện vùng cuộn: hỗ trợ cả cuộn toàn trang (`window`) và cuộn hộp thoại popup (`div[role="dialog"]`).
>    - Thu thập toàn diện: Họ tên, Profile URL, Numeric FB_ID, URL Avatar chất lượng cao, Subtitle/Bio, và danh sách link ảnh ban đầu.
> 2. **Bước 2 - Python Pipeline nạp mô hình AI thị giác & Từ khóa thẩm định**:
>    - Tệp Python chuyên trách (`fb_profile_dog_pipeline.py`) nạp trực tiếp `dog-model.onnx` qua `onnxruntime`.
>    - Tiền xử lý ảnh chuẩn `[1, 3, 224, 224]` Float32 RGB, tính toán xác suất Softmax 3 lớp: `adult_dog` (Lớp 0), `non_dog` (Lớp 1), `puppy` (Lớp 2).
>    - Phân tích từ khóa với 200+ giống chó và thuật ngữ breeder theo quy tắc ranh giới từ nguyên (Word Boundary Regex).
> 3. **Bước 3 - Bóc tách bộ sưu tập ảnh & Đánh số lưu trữ theo FB_ID**:
>    - Bóc tách bộ sưu tập ảnh (Photo Collection) của đối tượng được xác định là mục tiêu chó/thú cưng.
>    - Tự động tải và tổ chức thư mục ảnh theo định dạng chuẩn: `downloaded_collections/{FB_ID}/{FB_ID}_01.jpg`, `{FB_ID}_02.jpg`, `{FB_ID}_03.jpg`...
>    - Lưu lại metadata chi tiết của từng ảnh và đường dẫn tệp cục bộ trên máy.
> 4. **Bước 4 - Xuất báo cáo kết quả hoàn chỉnh**:
>    - Xuất file **Excel (.xlsx)** định dạng chuyên nghiệp: FB_ID, Tên, Link Profile, Phương thức nhận diện, Độ tin cậy AI, Danh sách link ảnh bộ sưu tập, Đường dẫn ảnh cục bộ, Phân hạng tiềm năng.
>    - Xuất file **JSON LEAD-US chuẩn Meta RAG** đồng bộ với hệ sinh thái CRM Pet & Grass.

---

## 1. Cơ Chế Nhận Diện & Cuộn Quét Trang Cá Nhân Facebook

### 1.1 Các Định Dạng URL Trang Cá Nhân Được Hỗ Trợ
- Người theo dõi:
  - `https://www.facebook.com/{username}/followers`
  - `https://www.facebook.com/profile.php?id={numeric_id}&sk=followers`
- Đang theo dõi:
  - `https://www.facebook.com/{username}/following`
  - `https://www.facebook.com/profile.php?id={numeric_id}&sk=following`
- Bạn bè / Bạn chung (Friends / Mutual Friends):
  - `https://www.facebook.com/{username}/friends`
  - `https://www.facebook.com/{username}/friends_mutual`
- Hộp thoại popup danh sách: Khi nhấp vào số người theo dõi trên trang cá nhân, Facebook hiển thị hộp thoại `div[role="dialog"]`.

### 1.2 Chiến Lược Cuộn & Bóc Tách DOM Trang Cá Nhân
1. **Nhận diện Scroll Container:**
   - Nếu xuất hiện `div[role="dialog"]`: xác định phần tử con có thuộc tính `overflow-y: auto` hoặc `overflow-y: scroll` để thực hiện cuộn trong modal.
   - Nếu đang ở trang tab riêng: thực hiện cuộn mượt `window.scrollBy({ top: 500, behavior: 'smooth' })`.
2. **Bóc tách Thẻ Follower (Follower Card):**
   - Xác định thẻ bao quanh thông qua cây DOM: `div[role="listitem"]` hoặc thẻ cha chứa liên kết profile + ảnh đại diện + nút tương tác (Theo dõi / Nhắn tin / Thêm bạn).
   - Trích xuất:
     - `name`: Tên hiển thị người dùng (loại trừ các chuỗi giao diện Facebook như "Follow", "Thêm bạn bè", "Nhắn tin").
     - `url`: Link Facebook sạch (chuẩn hóa về `https://www.facebook.com/{slug}` hoặc `profile.php?id={id}`).
     - `fb_id`: UID số nguyên (Numeric FB_ID 15 chữ số).
     - `avatar_url`: URL ảnh đại diện chất lượng cao (từ thẻ `img` hoặc `image` trong svg).
     - `subtitle`: Thông tin bổ sung (nghề nghiệp, số bạn chung, quê quán, tiểu sử).

---

## 2. Đặc Tả Kỹ Thuật Mô Hình AI Thị Giác & Từ Khóa Trong Python

### 2.1 Kiến Trúc Mô Hình ONNX (`dog-model.onnx`)
- **Kiến trúc:** YOLOv8n-cls (Image Classification).
- **Kích thước đầu vào:** Tensor `[1, 3, 224, 224]` kiểu `float32`.
- **Chuẩn hóa giá trị Pixel:** Dải `[0.0, 1.0]` (chia giá trị RGB `0 - 255` cho `255.0`).
- **Thứ tự kênh:** RGB (hoặc BGR chuyển sang RGB).
- **Đầu ra:** Tensor `output0` kích thước `[1, 3]`:
  - `Class 0`: `adult_dog` (Chó trưởng thành)
  - `Class 1`: `non_dog` (Không phải chó: người, hoa lá, xe cộ, chữ)
  - `Class 2`: `puppy` (Cún con)

### 2.2 Quy Trình Thẩm Định Đa Tầng (Multi-Stage Gatekeeper v2.4)
Mô hình `dog-model.onnx` xuất trực tiếp vector xác suất Softmax. Để triệt tiêu 100% false positives từ ảnh thumbnail mờ hoặc đồ họa (`TAROT`, `Sono' Studio`, `JII`, `Xuân Hân`) và bảo vệ các trại chó thật (`Cocker Spaniel`, `Boxers`, `Dachshunds`), áp dụng quy trình kiểm soát 6 lớp:

0. **Lớp 0 - Chuẩn Hóa Avatar HD & Loại Bỏ Header Trang Nguồn:**
   - Tự động bóc tách và loại bỏ tham số thumbnail `ctp=[sp]\d+x\d+` từ URL Facebook CDN để kéo ảnh gốc HD (720x720, 960x960, 2048x2048).
   - Loại trừ hoàn toàn các thẻ Header/Trang Chủ nguồn (như `Good Dog` #100063922191947) và chuỗi đếm số lượng người theo dõi (`191K người theo dõi`).
1. **Lớp 1 - Blacklist Ranh Giới Từ & Miễn Nhiễm Giống Chó (Dog Breed Immunity):**
   - Áp dụng ranh giới từ `\b` cho mọi từ khóa ngắn (`\bspa\b`, `\bxe\b`, `\bhr\b`, `\bcat\b`).
   - **Quy tắc Miễn Nhiễm:** Nếu hồ sơ chứa giống chó chính thức (`Spaniel`, `Boxers`, `Dachshund`, `Puppy`, `Kennel`...), các từ khóa phụ như `spa`, `xe`, `hr` tuyệt đối không được phép loại bỏ!
2. **Lớp 2 - Phát hiện khuôn mặt người trên ảnh HD (Haar Dual Face Cascade - Avatar Ground Truth):**
   - Chạy song song `haarcascade_frontalface_default.xml` (ảnh thật) và `haarcascade_frontalface_alt2.xml` (tranh vẽ/anime) trên ảnh HD nguyên bản. Nếu phát hiện khuôn mặt người $\rightarrow$ **LOẠI BỎ 100%**, tuyệt đối không để bất kỳ từ khóa nào đè lên.
3. **Lớp 3 - Loại trừ họ mèo (Feline Suppression):**
   - Quét `haarcascade_frontalcatface.xml` và từ khóa mèo $\rightarrow$ Loại bỏ.
4. **Lớp 4 - Lọc sắc thái hoa lá & phong cảnh (Flora HSV Guard):**
   - Phân tích màu HSV (tím/xanh lá thực vật > 35%) $\rightarrow$ Loại bỏ ảnh cỏ cây, phong cảnh.
5. **Lớp 5 - Thẩm định mô hình YOLOv8-cls ONNX trên ảnh HD (Lanczos Antialiasing):**
   - Ảnh HD được tiền xử lý giảm kích thước xuống 224x224 bằng bộ lọc chống răng cưa cao cấp `Image.Resampling.LANCZOS`, triệt tiêu hoàn toàn nhiễu hạt nén JPEG.
   - Nếu có từ khóa chó/breeder: Yêu cầu $P_{\text{dog}} \ge 0.60$ và $P_{\text{non\_dog}} < 0.40$.
   - Nếu không có từ khóa: Yêu cầu thị giác vượt trội $P_{\text{adult}} \ge 0.65, P_{\text{non\_dog}} < 0.20$ HOẶC $P_{\text{puppy}} \ge 0.95, P_{\text{non\_dog}} < 0.05$. Đồ họa, bài tarot, logo không có từ khóa cún cưng tự động có $P_{\text{non\_dog}} = 1.00$ và bị loại bỏ ngay.

### 2.3 Công Cụ Kiểm Soát Terminal & Live Web Console
- **Terminal Runner:** `run_step1_interactive.py` và `1_CHAY_LOC_ANH_STEP1.bat` cung cấp giao diện dòng lệnh với mã màu ANSI trực quan (`[✓ PHÊ DUYỆT CHÓ]`, `[❌ BỎ QUA]`), cho phép người dùng tùy chọn tốc độ chạy (0.15s/hồ sơ để quan sát hoặc Enter từng người).
- **Live Terminal Console Web UI:** Bảng điều khiển màu đen công nghệ trên Web Dashboard hiển thị luồng log thời gian thực, cho phép quản trị viên theo dõi lý do duyệt/bỏ từng hồ sơ song song khi quét.

## 3. Quy Trình Thu Thập Bộ Sưu Tập Ảnh & Đánh Tên Theo ID

Mỗi đối tượng tiềm năng sau khi được phát hiện sẽ được bóc tách bộ ảnh:
1. **Ảnh đại diện chính thức (Avatar HQ):** Ảnh kích thước lớn nhất được giải mã từ CDN Facebook.
2. **Ảnh từ bộ sưu tập / bài viết:** Các ảnh chụp chó, đàn con, cơ sở vật chất từ trang cá nhân.
3. **Cấu trúc lưu trữ tệp trên đĩa cứng:**
   ```
   downloaded_collections/
   └── {FB_ID}/
       ├── {FB_ID}_01.jpg   <-- Ảnh đại diện chính (Avatar)
       ├── {FB_ID}_02.jpg   <-- Ảnh bộ sưu tập 1
       ├── {FB_ID}_03.jpg   <-- Ảnh bộ sưu tập 2
       └── ...
   ```
4. **Metadata lưu kèm:** File JSON và Excel ghi nhận:
   - `FB_ID`: UID của đối tượng.
   - `Photo_Count`: Số lượng ảnh trong bộ sưu tập đã tải.
   - `Image_Urls`: Danh sách link ảnh gốc.
   - `Local_Image_Paths`: Danh sách đường dẫn file đã lưu trên máy.

---

## 4. Cấu Trúc Báo Cáo Xuất Kết Quả

### 4.1 Bảng Excel Chuẩn Doanh Nghiệp (`result_dog_leads_{timestamp}.xlsx`)
| STT | FB_ID | Họ và Tên | Link Facebook | Phương Thức Nhận Diện | Kết Quả AI Thị Giác | Từ Khóa Khớp | Số Ảnh Đã Tải | Đường Dẫn Bộ Sưu Tập Ảnh | Gợi Ý Sản Phẩm (Pet Grass/Potty/Toys) |
| :-: | :---: | :--- | :--- | :--- | :--- | :--- | :-: | :--- | :--- |

### 4.2 Tệp JSON LEAD-US Chuẩn Meta RAG (`result_dog_leads_{timestamp}.json`)
Đồng bộ 100% với cấu trúc 28 trường dữ liệu của hệ sinh thái `Marketing_Pet&Grass`, bao gồm các trường:
`stt`, `name`, `fb_id`, `url`, `avatar_url`, `photo_collection`, `detection_method`, `ai_vision_result`, `matched_keywords`, `score`, `rank_tier`, `product_fit`.

---

## 5. Hướng Dẫn Vận Hành Từng Bước Cho Người Dùng

### Bước 1: Quét Follower / Following bằng Extension
1. Mở trang cá nhân Facebook cần quét, chuyển sang tab **Người theo dõi (Followers)** hoặc **Đang theo dõi (Following)**:
   - Ví dụ: `https://www.facebook.com/username/followers` hoặc mở popup danh sách người theo dõi.
2. Nhấp biểu tượng tiện ích **FB Following Scraper**:
   - Chọn chế độ: **"Cào tất cả người theo dõi / đang theo dõi"** (để thu thập trọn bộ tệp và đẩy sang Python phân tích sâu) hoặc **"Lọc thông minh trực tiếp trên trình duyệt"**.
   - Bấm **"▶ Bắt đầu cào"**. Tiện ích tự động cuộn trang và thu thập thông tin.
3. Khi cuộn xong hoặc bấm dừng, nhấp nút **"📥 Xuất dữ liệu cho Python Pipeline (JSON/CSV)"**. Tệp sẽ được lưu vào thư mục tải về.

### Bước 2: Chạy Python Pipeline Thẩm Định AI & Tải Bộ Sưu Tập Ảnh Theo ID
1. Mở dòng lệnh (Terminal/PowerShell) tại thư mục dự án:
   ```bash
   python fb_following_scraper/fb_profile_dog_pipeline.py --input "path/to/exported_file.json"
   ```
2. Python pipeline tự động:
   - Khởi động `dog-model.onnx` trên ONNX Runtime.
   - Tải và thẩm định từng ảnh đại diện/bộ sưu tập ảnh kết hợp kiểm tra từ khóa.
   - Tự động tải toàn bộ ảnh của các đối tượng khớp vào thư mục `downloaded_collections/{FB_ID}/` đánh số `{FB_ID}_01.jpg`, `{FB_ID}_02.jpg`...
   - Xuất file báo cáo Excel và JSON hoàn chỉnh.
