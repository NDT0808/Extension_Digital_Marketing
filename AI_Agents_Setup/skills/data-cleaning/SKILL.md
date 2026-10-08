---
name: data-cleaning
description: Kỹ năng dọn dẹp và chuẩn hóa dữ liệu khách hàng thô (Breeder/Kennel) từ file CSV
---

# Kỹ năng: Data Cleaning (Dọn dẹp dữ liệu)

## Mục tiêu
Bạn đóng vai trò là **Data Cleaning Agent**. Nhiệm vụ của bạn là nhận dữ liệu thô (ví dụ từ Google Maps, AKC), loại bỏ dữ liệu rác, và chuẩn hóa thành một danh sách khách hàng tiềm năng chất lượng cao trước khi chuyển sang bước chấm điểm.

## Đầu vào (Input)
Dữ liệu khách hàng định dạng CSV/JSON với các trường cơ bản:
- Tên (Name/Kennel Name)
- Liên hệ (Phones, Emails, Websites, Facebook URL)
- Phân loại (Dog Breeds, has_puppy_sales_page, has_puppy_application)

## Quy tắc xử lý (Rules)
1. **Loại bỏ dữ liệu thiếu liên hệ:** Bỏ qua các dòng KHÔNG có CẢ `emails` VÀ `phones`. Nếu không có cách nào liên lạc, dữ liệu đó vô giá trị với Sales.
2. **Chuẩn hóa Tên (Name):** Xóa các ký tự đặc biệt thừa, viết hoa chữ cái đầu.
3. **Gộp trùng lặp (Deduplication):** Nếu 2 dòng có cùng `emails` hoặc `websites`, hãy gộp chúng lại làm một.
4. **Phân loại trạng thái Website/Facebook:** Đánh dấu những trang web bị lỗi (ví dụ: HTTP 404, error page) là `Invalid_Website`.

## Đầu ra (Output)
Trả về danh sách dữ liệu đã được làm sạch với trạng thái `Cleaned = True`, sẵn sàng để chuyển sang cho **Lead Scoring Agent**.
