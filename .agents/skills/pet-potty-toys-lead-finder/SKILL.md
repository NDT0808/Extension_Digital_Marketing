---
name: pet-potty-toys-lead-finder
description: Hệ thống định hướng kinh doanh, bộ tiêu chí phân loại hồ sơ (từ marketing_parameter.html), và mô hình theo dõi hành vi chấm điểm khách hàng tiềm năng (từ List_Action_user.xlsx) cho 3 sản phẩm cốt lõi Cỏ nhân tạo (Pet Grass), Nhà vệ sinh thú cưng (Pet Potty) và Đồ chơi (Pet Toys).
---

# Kỹ năng: Pet Grass, Potty & Toys Lead Finder (Định vị, Phân loại & Chấm điểm Khách hàng Tiềm năng)

## 1. Bối cảnh Doanh nghiệp & 3 Dòng Sản phẩm Cốt lõi
Hệ thống / Cửa hàng đang kinh doanh và tìm kiếm đối tác, khách hàng tiềm năng xoay quanh **3 nhóm sản phẩm chính**:

1. **Cỏ nhân tạo cho thú cưng (Artificial Grass / Dog Turf / Grass Patch / Pee Mat):**
   * *Mục đích:* Lót sân vườn cho chó chạy nhảy, lót chuồng trại huấn luyện, thảm cỏ ban công/sân thượng cho cún đi vệ sinh thoát nước nhanh, không bám bẩn.
   * *Từ khóa nhận diện:* `artificial grass`, `dog turf`, `grass patch`, `turf pad`, `real grass`, `dog lawn`, `fresh patch`, `doggie lawn`, `grass mat`.

2. **Nhà vệ sinh & Dụng cụ vệ sinh cho thú cưng (Pet Toilets / Potty / Pee Pads / Litter):**
   * *Mục đích:* Giải pháp đi vệ sinh trong nhà (indoor potty training) cho cún cưng, đặc biệt là cún con mới về nhà mới hoặc sống trong căn hộ chung cư.
   * *Từ khóa nhận diện:* `potty`, `dog toilet`, `pee pad`, `puppy pad`, `wee wee pad`, `potty tray`, `indoor dog potty`, `porch potty`, `litter box`, `potty training`.

3. **Đồ chơi thú cưng (Pet Toys / Chew Toys / Interactive Toys):**
   * *Mục đích:* Đồ chơi ngứa răng cho cún con (teething), đồ chơi xoa dịu stress khi xa mẹ (Snuggle Puppy), đồ chơi gặm sạch răng (dental chew), đồ chơi tương tác (KONG, rope).
   * *Từ khóa nhận diện:* `chew toy`, `dog toy`, `puppy toy`, `plush toy`, `rope toy`, `squeaky toy`, `interactive toy`, `teething`, `kong`, `nylabone`, `snuggle puppy`.
   * *LƯU Ý QUAN TRỌNG:* Loại trừ các từ chỉ giống chó như `Toy Poodle`, `Toy Breed`, `Toy Australian Shepherd` (đây là tên giống chó, KHÔNG PHẢI đồ chơi).

---

## 2. Tiêu chí Thu thập & Điểm Chuẩn Hồ sơ Khách hàng (Từ `marketing_parameter.html`)

> [!IMPORTANT]
> **NGUYÊN TẮC VÀNG VỀ MÔ HÌNH CHẤM ĐIỂM (GROUND-TRUTH SCORING ARCHITECTURE):**
> * **Nguồn chuẩn mực số 1 (Hồ sơ Tĩnh - Baseline Ground Truth):** Được tính trực tiếp trên **Danh sách trích xuất thông tin người dùng** (`List_Info_User.xlsx` / `priority_list_2026-10-06_v2.xlsx`) dựa vào bộ quy chuẩn 13 trường tại Mục 02 và thang điểm Lead Score tại Mục 04 của `Datasets/marketing_parameter.html`. Đây là căn cứ quyết định phân cấp A/B/C/D và tiềm năng mua sỉ dài hạn.
> * **Nguồn bổ trợ số 2 (Hành vi Động - Dynamic Boost):** File `List_Action_user.xlsx` ghi nhận các sự kiện tương tác số (Click, Comment Reels, Web Pixel), chỉ dùng để **cộng điểm thưởng tương tác nóng (Hot Boost) và tính hệ số suy giảm thời gian (Time Decay)**, không thể dùng độc lập để chấm điểm hồ sơ vì thiếu các trường dữ liệu tĩnh nền tảng (Website, Puppy page, Application, Review, Giống chó).

### 2.1. 13 Trường Dữ liệu Thu thập Quan trọng (Data Structure)
Mỗi khi trích xuất hoặc hoàn thiện hồ sơ đối tác/breeder, ưu tiên bám sát 13 trường chuẩn:
1. **Breeder Name** (Tên trại chó / người nhân giống) - ★★★★★
2. **Website** (Website chính thức) - ★★★★★
3. **Email** (Email kinh doanh/giao dịch) - ★★★★★
4. **Phone** (Số điện thoại) - ★★★★☆
5. **State / City** (Bang / Thành phố tại Mỹ) - ★★★★☆
6. **Breed** (Các giống chó đang nhân giống) - ★★★★★
7. **Facebook** (Trang Facebook / Profile hoạt động) - ★★★★☆
8. **Instagram** (Tài khoản Instagram) - ★★★★☆
9. **Puppy Page** (Có trang bán cún con riêng biệt hay không) - ★★★★★
10. **Online Application** (Có form đăng ký mua cún online hay không) - ★★★★★
11. **Reviews** (Số lượng & điểm đánh giá Google/Facebook) - ★★★☆☆
12. **Online Store** (Có cửa hàng bán phụ kiện/đồ dùng online hoặc Amazon) - ★★★★☆
13. **Current Kit** (Hiện tại có cung cấp gói quà Take-Home Kit cho khách nhận cún không) - ★★★★★

### 2.2. Phân loại Cấp bậc Đối tác (A - B - C - D) & Hành động của Đội Sales (Mục 03)
* **Cấp A (A级: Điểm $\ge$ 61 - Trọng điểm Sales / Ưu tiên Cao nhất):**
  * *Tiêu chuẩn:* Có website chuẩn + trang bán puppy riêng + mạng xã hội hoạt động tích cực + nhân giống nhiều giống chó/quy mô lớn + có kênh bán hàng online/Amazon.
  * *Hành động Sales:* Đội sales ưu tiên liên hệ trực tiếp bằng điện thoại trong ngày, chào gói quà tặng Puppy Kit V2/V3 (có in logo thương hiệu của trại).
* **Cấp B (B级: Điểm 45 - 60 - Quy mô Trung bình / Tiềm năng):**
  * *Tiêu chuẩn:* Có website và thông tin liên hệ đầy đủ, quy mô vừa phải.
  * *Hành động Sales:* Tiếp cận tự động qua chuỗi email marketing + chăm sóc bổ sung bằng telesale.
* **Cấp C (C级: Điểm 30 - 44 - Tiềm năng Tầm trung / Chi phí thấp):**
  * *Tiêu chuẩn:* Chỉ có trang Facebook hoặc định vị Google Maps, chưa có website riêng hoàn chỉnh.
  * *Hành động Sales:* Nhắn tin trực tiếp chi phí thấp qua Fanpage Facebook/Instagram.
* **Cấp D (D级: Điểm < 30 - Tạm hoãn / Đóng băng):**
  * *Tiêu chuẩn:* Thông tin không đầy đủ, website bị hỏng (dead link) hoặc nhiều năm không hoạt động.
  * *Hành động Sales:* Tạm thời lưu trữ, không tốn tài nguyên bán hàng.

### 2.3. Bảng Điểm Chuẩn Hồ sơ Khách hàng (Mục 04 của `marketing_parameter.html`)
* Có Website chính thức (有官方网站): **+5 điểm**
* Có trang bán Puppy (`Puppy Page` - 有Puppy销售页面): **+10 điểm**
* Có Form đăng ký mua cún (`Online Application` - 是否在线申请购买): **+10 điểm** *(kinh doanh bài bản, mức độ thương mại hóa cao)*
* Facebook hoạt động đều đặn (Facebook活跃): **+5 điểm**
* Instagram hoạt động đều đặn (Instagram活跃): **+5 điểm**
* Đạt từ 10+ đánh giá trở lên (10+评价): **+5 điểm**
* Nhân giống nhiều giống chó / Giống cao cấp (多个犬种): **+5 điểm**
* Có Online Store / Gian hàng Amazon (是否销售宠物用品): **+10 đến +15 điểm**
* Hiện tại cung cấp Take-Home Kit (Current Kit): **+10 điểm**
* Tương tác trang web (Web Tracking Events):
  * Xem sản phẩm Puppy Kit: **+10 điểm**
  * Xem bảng giá (View Pricing / BOM): **+15 điểm**
  * Gửi form liên hệ (Inquiry): **+30 điểm**
  * Yêu cầu gửi mẫu thử (Sample Kit): **+50 điểm**
  * Nhận báo giá thương mại (Quote): **+60 điểm**

---

## 3. Theo dõi Hành động & Mô hình Tính điểm Động (Từ `List_Action_user.xlsx`)

### 3.1. 6 Mã Kênh Tương tác & Trọng số Điểm Gốc (Base Score)
Hệ thống theo dõi khách hàng qua 6 kênh hành vi để phân loại tệp đối tượng (Audience):

| Mã Code (`code`) | Kênh (`channel`) | Trục (`axis`) | Base Score | Suy giảm (`decay`) | Tier mặc định | Tệp Đối tượng (`audienceName`) | Hành động Tiếp thị (`audienceAction`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **`Own_Reels_Comment`** | 2 | engagement | **40** | **Có (True)** | **S** | **A3 Tương tác Trực tiếp** | **Ưu tiên cao nhất: Gọi điện Sales ngay + Remarketing** |
| **`Site_Pixel_Behavior`** | 6 | website | **30** | **Có (True)** | Dynamic | **A4/A5 Hành vi Website** | **Theo dõi CPL/ROAS, remarketing sâu theo trang đã xem** |
| **`AKC_Breeder_List`** | 1 | customer | **25** | Không (False) | **S** | **LAL Đối tượng Tương đồng** | Tạo tệp Seed mở rộng quy mô |
| **`Visual_High_Relevance`** | 4 | ai | **25** | **Có (True)** | **A** | **AI Thị giác Nhận diện Cao** | Đã phát hiện ảnh sân cỏ/chó con qua avatar, cover |
| **`Viral_Post_Engaged`** | 3 | engagement | **20** | **Có (True)** | **A** | **Tương tác Bài viết Viral** | Custom Audience + lấy ý tưởng làm nội dung kéo khách |
| **`Social_Network_L2`** | 5 | customer | **10** | Không (False) | Dynamic | **Tệp Mở rộng Sở thích L2** | Tầng đỉnh phễu (Top of Funnel) |

#   * `zeroWeightDays = 30`: Nếu quá **30 ngày** không có bất kỳ tương tác hoặc không đăng bài mới, điểm tương tác suy giảm về **0**.

### 3.4. Thuật toán Chống Bão hòa Điểm (Anti-Saturation Dynamic Scoring Engine)
Để tránh tình trạng "cào bằng" 100 điểm cho toàn bộ khách hàng, hệ thống bắt buộc sử dụng công thức tổng hợp đa tầng (5 trục đánh giá độc lập), phân bổ điểm số theo thang chuẩn:
$$\text{Total Score} = \text{Recency} (0-35) + \text{ICP Fit} (10-30) + \text{Breed Commercial Value} (0-15) + \text{Business Infrastructure} (0-10) + \text{Amazon Credibility} (0-15)$$

* **Trục 1 - Độ tươi mới tương tác (Action Recency: 0 - 35 điểm):**
  * Đăng bài / tương tác $\le 3$ giờ qua: **35 điểm**
  * Trong vòng 4 - 24 giờ qua: **32 điểm**
  * Trong vòng 1 - 3 ngày qua: **28 điểm**
  * Trong vòng 4 - 7 ngày qua: **20 điểm**
  * Trong vòng 8 - 14 ngày qua: **15 điểm**
  * Trong vòng 15 - 30 ngày qua: **8 điểm**
  * Quá 30 ngày: **0 điểm** (hết hạn tương tác)
* **Trục 2 - Mức độ phù hợp ICP (ICP Fit: 10 - 30 điểm):**
  * Dog Breeder / Trại chó chuyên nghiệp: **28 - 30 điểm** (Khách mua kit số lượng lớn)
  * Pet Boarding / Huấn luyện chó K9: **20 - 22 điểm** (Khách mua cỏ sân chơi & đồ chơi nhai)
  * Pet Rescue / Trạm cứu trợ: **14 - 16 điểm** (Khách mua tã lót & khay vệ sinh)
  * Pet Owner / Người nuôi cá nhân: **10 điểm**
* **Trục 3 - Giá trị Thương mại của Giống chó (Breed Commercial Value: 0 - 15 điểm):**
  * Giống chó thương mại phân khúc cao (French Bulldog, English Bulldog, Bernedoodle, Goldendoodle, Cavapoo, Corgi, Malinois, German Shepherd, Labrador, Golden Retriever, Rottweiler, Bully):
    * Sở hữu từ 2 giống giá trị cao trở lên: **+15 điểm**
    * Sở hữu 1 giống giá trị cao: **+10 điểm**
  * Các giống cún cảnh phổ thông: **+5 điểm**
  * Không rõ giống: **0 điểm**
* **Trục 4 - Hạ tầng & Pháp nhân Doanh nghiệp (Business Infrastructure: 0 - 10 điểm):**
  * Có Website chính thức / Cửa hàng trực tuyến: **+5 điểm**
  * Có pháp nhân kinh doanh (Kennel, Farm, LLC, LTD) hoặc có Application Form: **+5 điểm**
* **Trục 5 - Tín nhiệm & Độ sẵn sàng Sàn Amazon (Amazon Credibility: 0 - 15 điểm):** Xem chi tiết tại Mục 4.

* **Phân tầng Hạng Khách hàng (Standard Tier Distribution):**
  * **Tier S (Kim Cương: 85 - 100 điểm):** Trại chó thương mại lớn, cực kỳ tích cực $\le 24$h, có uy tín Amazon và bán giống giá trị cao $\rightarrow$ **Gọi điện chốt hợp đồng ngay trong ngày**.
  * **Tier A (Vàng: 70 - 84 điểm):** Trại chó hoặc học viện huấn luyện hoạt động tích cực $\le 3$ ngày $\rightarrow$ **Email cá nhân hóa + Telesale**.
  * **Tier B (Bạc: 50 - 69 điểm):** Trại chó hoặc cơ sở chăm sóc hoạt động trong 4 - 14 ngày $\rightarrow$ **Chuỗi email marketing tự động**.
  * **Tier C (Đồng: 30 - 49 điểm):** Hoạt động thưa thớt (15 - 30 ngày) hoặc trạm cứu trợ $\rightarrow$ **Nuôi dưỡng nội dung mạng xã hội**.
  * **Tier D (Đóng băng: < 30 điểm):** Quá 30 ngày không hoạt động hoặc hồ sơ thiếu $\rightarrow$ **Lưu trữ chờ kích hoạt lại**.

---

## 4. Bảng Nhãn Phân loại Sàn Amazon & Điểm Tín nhiệm (Amazon Credibility Proof)

Sự hiện diện của gian hàng hoặc Wishlist Amazon là bằng chứng rõ nhất chứng minh đối tác **đang chi tiền hoặc giới thiệu sản phẩm cho khách hàng của họ**, giúp tăng độ tin cậy và tỷ lệ chốt deal:

| Nhãn Phân loại Amazon (`Phân loại Amazon`) | Điểm Tín nhiệm | Ý nghĩa Kinh doanh | Hành động của Team Sales |
| :--- | :---: | :--- | :--- |
| **`Selling pet toys + Artificial grass/Pet toilets (TARGET)`** | **+15** | Đối tác đang bán/khuyên dùng **cả 2 nhóm sản phẩm mục tiêu** (Đồ chơi + Cỏ/Khay vệ sinh). Tệp khách hàng hoàn hảo nhất! | Ưu tiên số 1: Giới thiệu trọn gói Take-Home Kit in logo độc quyền của trại. |
| **`Selling artificial grass/pet toilets (TARGET)`** | **+10** | Đang bán/khuyên dùng **Cỏ nhân tạo hoặc Khay/Nhà vệ sinh/Pee Pad**. | Chào thảm cỏ thoát nước và khay potty giá sỉ/BOM chiết khấu. |
| **`Selling pet toys`** | **+7** | Đang bán/khuyên dùng **Đồ chơi thú cưng** (KONG, gặm ngứa răng, Snuggle Puppy). | Chào combo đồ chơi huấn luyện và đồ chơi xoa dịu cún con. |
| **`There's an Amazon link, but no target sales.`** | **+3** | Có liên kết Amazon nhưng bán thức ăn, thuốc thú y, lồng chuồng thông thường. | Mời hợp tác mở rộng danh mục sang kit quà tặng cún con. |
| **`Amazon link not found`** | **0** | Chưa tìm thấy liên kết Amazon trên trang của đối tác. | Đặt câu hỏi mở đầu về việc chuẩn bị Take-Home Kit. |

---

## 5. Bộ lọc Âm tính (Negative Exclusion Filters) - Tuyệt đối Không đưa vào CRM

Hệ thống RAG và phân loại phải loại bỏ các tổ chức phi khách hàng (False Positives) trước khi chấm điểm:
1. **Hiệp hội phả hệ, CLB quốc gia phi lợi nhuận:** `American Kennel Club` (AKC), `Westminster Kennel Club`, `United Kennel Club` (UKC), `Canadian Kennel Club`, `FCI`, `Breed Clubs`. *(Lý do: Đây là cơ quan đăng kiểm/tổ chức cuộc thi, không phải nhà nhân giống bán cún con).*
2. **Chuỗi siêu thị bán lẻ thú cưng khổng lồ:** `PetSmart`, `Petco`, `Chewy`, `Pet Supplies Plus`.
3. **Kênh tin tức, tạp chí, truyền thông giải trí & meme:** `WeRateDogs`, `The Dodo`, `Dogster`, `Dogs Naturally Magazine`, `American Dog Fancier`, `Things Dog Handlers Say`.
4. **Công ty xét nghiệm gen DNA & tập đoàn thú y:** `Embark Vet`, `Zoetis`, `Revival Animal Health`, `Fear Free Pets`.

---

## 6. Kịch bản Tiếp cận & Thông điệp Bán hàng (Sales Angle)

* **Câu hỏi mở đầu kinh điển (Email & Telesale):**
  > *"Do you currently provide a puppy take-home package for your buyers?"*  
  > *(Hiện tại trại của anh/chị có chuẩn bị bộ quà tặng Take-Home Kit cho khách hàng khi họ đón cún con về nhà mới không?)*
* **Nếu khách trả lời CÓ (YES):**
  * Hỏi thành phần và chi phí hiện tại của họ $\rightarrow$ Đề xuất bản nâng cấp V2/V3 chuyên nghiệp hơn, bổ sung thảm cỏ nhân tạo tập đi vệ sinh và đồ chơi gặm ngứa răng có in logo trại.
* **Nếu khách trả lời CHƯA (NO):**
  * Giới thiệu giải pháp Take-Home Starter Kit trọn gói: Giúp nâng tầm thương hiệu trại chó, tăng sự an tâm cho người mua cún, hạn chế cún đi bậy trong nhà mới.

---

## 7. Chỉ thị Vận hành cho AI & Hệ thống RAG (Prompt & System Operating Rules)

1. **Tuân thủ Thuật toán Chống Bão hòa Điểm:** Tuyệt đối không cho ra danh sách mà tất cả khách hàng đều 100 điểm. Phải áp dụng công thức 5 trục độc lập tại Mục 3.4.
2. **Bắt buộc hiển thị Trường Amazon:** Trong mọi báo cáo phân tích và kết quả truy vấn RAG, phải có cột `Amazon Status / Trạng thái Amazon` để chứng minh độ uy tín.
3. **Ưu tiên Hiển thị Đa dạng Cấp bậc:** Bảng kết quả phải hiển thị cả các tầng Tier S, Tier A, Tier B cùng các giống chó khác nhau để đội ngũ tiếp thị có cái nhìn tổng quan toàn diện.
4. **Luôn xuất ra các cột rõ ràng:** Tên, URL, Website, Ngày hoạt động gần nhất (`lastActiveDays`), Điểm số chuẩn (`Lead Score`), Phân hạng (`Tier A/B/C/D`), Kênh Amazon (`Amazon Link` & `Amazon Status`), và Phân loại nhu cầu sản phẩm (Cỏ nhân tạo / Nhà vệ sinh / Đồ chơi).
5. **Hành động Sales Cụ thể:** Chỉ ra rõ trong danh sách khách nào là **Hot Lead (Hạng A/S, điểm ≥ 61)** để Sales xử lý ngay lập tức theo kịch bản Take-Home Kit V2/V3.
6. **Quy tắc Vận Hành RAG:** Hệ thống RAG khi truy vấn phải trích xuất trực tiếp từ danh sách thông tin người dùng đã xác minh (Ground Truth), ưu tiên lọc các đối tác có gian hàng Amazon bán cả 2 dòng sản phẩm mục tiêu (Đồ chơi + Cỏ/Potty) để cung cấp báo giá sỉ độc quyền.
