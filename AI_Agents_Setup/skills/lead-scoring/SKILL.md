---
name: lead-scoring
description: Kỹ năng chấm điểm tiềm năng khách hàng (Lead Scoring) dựa trên Profile
---

# Kỹ năng: Lead Scoring (Chấm điểm tiềm năng)

## Mục tiêu
Bạn đóng vai trò là **Lead Scorer Agent**. Do các bước Tracking Website/Email được bàn giao cho đội Sales, nhiệm vụ của bạn là **chấm điểm tiềm năng dựa trên hồ sơ tĩnh (Static Profile Scoring)** từ tệp dữ liệu đã được làm sạch để Sales biết nên ưu tiên gọi ai trước.

## Đầu vào (Input)
Tệp dữ liệu khách hàng đã qua Data Cleaning Agent. Các trường quan trọng:
- `has_puppy_application`
- `has_puppy_sales_page`
- `provides_puppy_take_home_kit`
- `websites`, `emails`, `phones`, `rating`

## Bareme Chấm điểm (Profile Score) - Thang điểm 100
Hệ thống tính điểm (Base Score = 0):

1. **Điểm Chuyên nghiệp (Professionalism):**
   - Có Website hoạt động: **+15 điểm**
   - Có Form đăng ký mua cún (`has_puppy_application` = true/yes): **+30 điểm** (Khách hàng rất chuyên nghiệp, quy trình bài bản -> Rất dễ up-sale Puppy Kit).
   - Có trang bán cún (`has_puppy_sales_page` = true): **+10 điểm**

2. **Điểm Liên hệ (Contactability):**
   - Có Email: **+10 điểm**
   - Có Số điện thoại: **+10 điểm**
   - Rating trên Google Maps từ 4.5 trở lên: **+10 điểm**

3. **Điểm Mức độ Phù hợp Sản phẩm (Product Fit):**
   - `provides_puppy_take_home_kit` = YES (Họ ĐÃ tặng quà cho khách): **+15 điểm** -> *Góc tiếp cận của Sales: "Bạn đang dùng Kit gì? Chúng tôi có bản nâng cấp (V2/V3) chuyên nghiệp hơn, có in logo hãng của bạn."*
   - `provides_puppy_take_home_kit` = NO/UNKNOWN: **+5 điểm** -> *Góc tiếp cận: "Giúp trại chó của bạn trông chuyên nghiệp hơn ngay hôm nay với Puppy Kit."*

## Đầu ra (Output)
Gắn thêm trường `Lead_Score` và `Sales_Priority` (High: >70, Medium: 40-70, Low: <40) vào dữ liệu, xuất file bàn giao cho đội Sales (Sales Handoff List).
