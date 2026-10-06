# Website Intent Detector

Công cụ nhỏ gọn bằng Python giúp cào dữ liệu (crawl) nội dung trên các website để nhận diện nhanh 3 yếu tố quan trọng:
1. **Website có thực sự bán chó không?** (Dựa vào các từ khóa liên quan đến mua bán, cọc, chó con, v.v.)
2. **Website có Form đăng ký không?** (Nhận diện thẻ `<form>` hoặc các từ khóa như Application, Form, v.v.)
3. **Website có cung cấp Home Take Kit / Supplies không?** (Nhận diện các từ khóa về starter kit, blanket, food, v.v.)

## Cài đặt

1. Đảm bảo bạn đã cài đặt Python.
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```

## Cách sử dụng

1. Mở file `urls.txt` (nếu chưa có thì script sẽ tự động tạo) và thêm các URL website bạn muốn kiểm tra (Mỗi dòng 1 URL).
2. (Tùy chọn) Mở file `keywords.json` để thêm hoặc sửa các từ khóa nhận diện cho phù hợp với nhu cầu của bạn.
3. Chạy script:
   ```bash
   python analyzer.py
   ```
4. Kết quả sẽ được in trực tiếp ra màn hình terminal và đồng thời lưu lại chi tiết vào file `analysis_results.json`.
