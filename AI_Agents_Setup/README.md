# Quy trình Hệ thống Multi-Agent (Giai đoạn Tiền Sale - Pre-Sales)

Vì bạn đang phân tách rạch ròi quy trình:
1. **Bạn (Data Team/AI):** Phụ trách thu thập, làm sạch dữ liệu và chấm điểm tiềm năng (Scoring).
2. **Sales Team:** Phụ trách Email Marketing, Website Tracking và Handoff.

Dưới đây là thiết kế Multi-Agent chuẩn hóa phục vụ chính xác cho mục đích của bạn, dựa trên quy trình trong `marketing_parameter.html`, áp dụng cho dữ liệu `2026_10_02_v1_master.csv` và có thể tái sử dụng cho các chiến dịch tương lai:

---

## 1. Kiến trúc Multi-Agent (Pre-Sales Focus)

Thay vì để hệ thống AI làm mọi thứ đến tận khâu chốt đơn, chúng ta giới hạn khu vực hoạt động của AI ở khâu **chuẩn bị "đạn" cho Sales**.

### 🤖 Agent 1: The Cleaner (AI Data Cleansing)
- **Nhiệm vụ:** Nhận file dữ liệu tổng khổng lồ (như `2026_10_02_v1_master.csv`). 
- **Cách hoạt động:** Áp dụng skill `data-cleaning`. Nó sẽ lướt qua hàng nghìn dòng, loại bỏ ngay những trại chó không có phương thức liên lạc (trống Email và Phone), format lại tên trại cho chuẩn để khi Sales gửi email không bị lỗi font hoặc viết thường chữ cái đầu.
- **Đầu ra:** Một file CSV mới siêu sạch.

### 🎯 Agent 2: The Scorer (AI Lead Scoring)
- **Nhiệm vụ:** Nhận tệp CSV siêu sạch và chấm điểm tĩnh (Static Profile Scoring) thay vì điểm hành vi (Behavioral Scoring). Điểm hành vi (click link, mở email) sẽ do phần mềm CRM của team Sales tự tính sau.
- **Cách hoạt động:** Áp dụng skill `lead-scoring`. 
   - Trại chó nào có Website riêng (+15đ), có form đăng ký mua cún `has_puppy_application` (+30đ) -> AI nhận định đây là quy trình rất chuyên nghiệp, chắc chắn sẽ mua bộ hộp quà cao cấp (V2/V3).
- **Đầu ra:** Cột `Lead_Score` và `Sales_Priority` được thêm vào dữ liệu. Dữ liệu được chia thành 3 tệp: **High Priority** (Giao Sales giỏi nhất), **Medium**, **Low**.

---

## 2. Giao tiếp giữa Bạn và Team Sales (Handoff Process)

Khi **Agent 2 (The Scorer)** chạy xong, quy trình bàn giao cho Sales sẽ diễn ra như sau:

1. **Xuất danh sách phân loại:** AI tự động chia file master ban đầu thành các file nhỏ hơn dựa trên `Sales_Priority` và `provides_puppy_take_home_kit` (để Sales biết kịch bản nào cần nói).
2. **Kịch bản Sales được đính kèm:** Dựa theo `marketing_parameter.html`, dữ liệu gửi sang Sales sẽ đi kèm ghi chú rõ ràng:
   - *Nếu khách Priority High & Chữ "Kit" = Unknown:* "Anh/chị có tặng quà cho khách mang cún về không? Xem thử mẫu V2 của bên em nhé."
   - *Nếu khách Priority High & Chữ "Kit" = Yes:* "Em thấy bên anh chị đã có quà tặng. Bên em có thiết kế hộp in logo thương hiệu rất sang trọng, anh chị xem thử bảng giá BOM nhé."

## 3. Khả năng Tái sử dụng (Future Proof)
Khi bạn chạy một sản phẩm khác (ví dụ: *Bán cỏ nhân tạo cho sân chơi chó*), quy trình này vẫn **không thay đổi**.
- **The Cleaner:** Vẫn dọn dẹp data trống.
- **The Scorer:** Vẫn chấm điểm dựa trên Website, Form, Rating. Chỉ cần tinh chỉnh nhẹ Skill: thay vì check `has_puppy_application`, AI sẽ check `has_large_play_area` hoặc `kennel_size` để chấm điểm bán cỏ nhân tạo.
