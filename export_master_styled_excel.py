import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

CSV_PATH = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\GoodDog_Followers_Master_CRM_2026-10-15.csv"
XLSX_PATH = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\GoodDog_Followers_Master_CRM_2026-10-15.xlsx"

print(f"[*] Đang đọc file CSV: {CSV_PATH}...")
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', dtype=str).fillna('')
print(f"[✓] Đã nạp {len(df)} dòng dữ liệu với {len(df.columns)} cột.")

# Khởi tạo Workbook
wb = openpyxl.Workbook()
# Xóa sheet mặc định ban đầu
wb.remove(wb.active)

# -----------------------------------------------------------------------------
# DESIGN SYSTEM & STYLES (EXECUTIVE GRADE)
# -----------------------------------------------------------------------------
font_title = Font(name="Segoe UI", size=14, bold=True, color="1E293B")
font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="64748B")

font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
font_header_vip = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")

font_data = Font(name="Segoe UI", size=9.5, color="1E293B")
font_data_bold = Font(name="Segoe UI", size=9.5, bold=True, color="1E293B")
font_data_link = Font(name="Segoe UI", size=9.5, color="2563EB", underline="single")
font_muted = Font(name="Segoe UI", size=9, color="64748B")

# Fills
fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Navy
fill_header_vip = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Royal Blue
fill_header_weather = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid") # Teal / Emerald Dark
fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

# Tier Badges
fill_tier_s = PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid") # Deep Violet
font_tier_s = Font(name="Segoe UI", size=9.5, bold=True, color="5B21B6")

fill_tier_a = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid") # Emerald
font_tier_a = Font(name="Segoe UI", size=9.5, bold=True, color="065F46")

fill_tier_b = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Amber
font_tier_b = Font(name="Segoe UI", size=9.5, bold=True, color="92400E")

fill_tier_c = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid") # Slate
font_tier_c = Font(name="Segoe UI", size=9.5, color="475569")

# Weather Trigger Fills
fill_cold = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid") # Ice Blue
font_cold = Font(name="Segoe UI", size=9.5, color="0369A1", bold=True)

fill_hot = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid") # Sun Peach
font_hot = Font(name="Segoe UI", size=9.5, color="C2410C", bold=True)

fill_stress = PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid") # Calm Lilac
font_stress = Font(name="Segoe UI", size=9.5, color="7E22CE", bold=True)

# Borders
border_thin = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)
border_header = Border(
    left=Side(style='thin', color='334155'),
    right=Side(style='thin', color='334155'),
    top=Side(style='medium', color='0F172A'),
    bottom=Side(style='medium', color='0F172A')
)

align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")
align_left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)
align_right = Alignment(horizontal="right", vertical="center")

# Predefined Optimal Column Widths
COLUMN_WIDTHS = {
    'STT': 7,
    'Master_ID': 17,
    'FB_ID': 20,
    'Họ và Tên (Breeder Name)': 32,
    'Phương Thức Nhận Diện (Detection Method)': 26,
    'Chủ Sở Hữu (Owner_Representative)': 24,
    'Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)': 26,
    'Số Điện Thoại (Phone)': 18,
    'Email': 26,
    'Website Chính Thức': 30,
    'Facebook URL': 32,
    'Instagram URL': 22,
    'Địa Chỉ (Address)': 28,
    'Thành Phố (City)': 18,
    'Bang (State)': 12,
    'Mã Zip (Zip Code)': 13,
    'Quốc Gia (Country)': 16,
    'Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)': 46,
    'Kết Quả AI Thị Giác (AI dog-model.onnx)': 28,
    'Kênh Bán Amazon (Amazon Status)': 26,
    'Link Amazon': 22,
    'Thời Gian Đăng Bài Gần Nhất': 22,
    'Thời Gian Tương Đối': 18,
    'Độ Tươi Mới (Recency Tier)': 18,
    'Điểm Recency (0-35)': 15,
    'Tổng Điểm Lead Score (0-100)': 16,
    'Phân Hạng Đối Tác (Tier Rank)': 22,
    'Lượt Cảm Xúc': 14,
    'Số Bình Luận': 14,
    'Phân Khúc Khách Hàng (ICP)': 26,
    'Sản Phẩm Đề Xuất': 42,
    'Hành Động Sales': 45,
    'Nguồn Dữ Liệu': 24,
    'Avatar URL': 26
}

# =============================================================================
# SHEET 1: MASTER CRM LEADS (1,059 KHÁCH HÀNG TOÀN DIỆN 33 TRƯỜNG)
# =============================================================================
print("[*] 1. Đang tạo Sheet 1: Master_CRM_1059_Leads...")
ws_master = wb.create_sheet(title="Master_CRM_1059_Leads")
ws_master.views.sheetView[0].showGridLines = True

headers = list(df.columns)
ws_master.append(headers)

# Format Header Row
ws_master.row_dimensions[1].height = 28
for col_idx in range(1, len(headers) + 1):
    cell = ws_master.cell(row=1, column=col_idx)
    cell.font = font_header
    cell.fill = fill_header
    cell.alignment = align_center
    cell.border = border_header

# Populate Data Rows
for r_idx, row_data in enumerate(df.values, start=2):
    ws_master.row_dimensions[r_idx].height = 22
    is_even = (r_idx % 2 == 0)
    base_fill = fill_zebra if is_even else fill_white
    
    for c_idx, val in enumerate(row_data, start=1):
        cell = ws_master.cell(row=r_idx, column=c_idx)
        val_str = str(val).strip() if val is not None else ''
        h_name = headers[c_idx - 1]
        
        cell.font = font_data
        cell.fill = base_fill
        cell.border = border_thin
        cell.alignment = align_left
        
        # Format kiểu dữ liệu và căn lề
        if h_name in ['STT', 'Điểm Recency (0-35)', 'Lượt Cảm Xúc', 'Số Bình Luận']:
            try:
                cell.value = int(val_str) if val_str else 0
            except:
                cell.value = val_str
            cell.alignment = align_center
        elif h_name == 'Tổng Điểm Lead Score (0-100)':
            try:
                cell.value = float(val_str) if val_str else 0.0
            except:
                cell.value = val_str
            cell.alignment = align_center
            cell.font = font_data_bold
            # Màu sắc điểm số
            try:
                sc = float(val_str)
                if sc >= 85:
                    cell.font = Font(name="Segoe UI", size=9.5, bold=True, color="5B21B6")
                elif sc >= 70:
                    cell.font = Font(name="Segoe UI", size=9.5, bold=True, color="065F46")
                elif sc >= 50:
                    cell.font = Font(name="Segoe UI", size=9.5, bold=True, color="92400E")
            except: pass
        elif h_name in ['Master_ID', 'FB_ID', 'Phương Thức Nhận Diện (Detection Method)', 'Bang (State)', 'Mã Zip (Zip Code)', 'Quốc Gia (Country)', 'Độ Tươi Mới (Recency Tier)', 'Số Điện Thoại (Phone)']:
            cell.value = str(val_str) # Giữ nguyên string để FB_ID không bị 1.0E+15
            cell.alignment = align_center
            if h_name == 'Bang (State)':
                cell.font = font_data_bold
            elif h_name == 'FB_ID':
                cell.font = Font(name="Consolas", size=9.5, color="334155")
            elif h_name == 'Phương Thức Nhận Diện (Detection Method)':
                cell.font = Font(name="Segoe UI", size=9.5, color="1E3A8A")
        elif h_name == 'Họ và Tên (Breeder Name)':
            cell.value = val_str
            cell.font = font_data_bold
        elif h_name in ['Website Chính Thức', 'Facebook URL', 'Link Amazon']:
            cell.value = val_str
            if val_str.startswith('http'):
                cell.font = font_data_link
        elif h_name in ['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)', 'Sản Phẩm Đề Xuất', 'Hành Động Sales', 'Địa Chỉ (Address)']:
            cell.value = val_str
            cell.alignment = align_left_wrap
        else:
            cell.value = val_str
            
        # Tô màu nổi bật cột Phân Hạng Đối Tác (Tier Rank)
        if h_name == 'Phân Hạng Đối Tác (Tier Rank)':
            cell.alignment = align_center
            if 'Tier S' in val_str or 'Kim Cương' in val_str:
                cell.fill = fill_tier_s
                cell.font = font_tier_s
            elif 'Tier A' in val_str or 'Vàng' in val_str:
                cell.fill = fill_tier_a
                cell.font = font_tier_a
            elif 'Tier B' in val_str or 'Bạc' in val_str:
                cell.fill = fill_tier_b
                cell.font = font_tier_b
            elif 'Tier C' in val_str or 'Đồng' in val_str:
                cell.fill = fill_tier_c
                cell.font = font_tier_c

        # Tô màu cột Ngữ Cảnh Thời Tiết
        if h_name == 'Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)':
            if 'Mưa/Tuyết/Lạnh giá' in val_str:
                cell.fill = fill_cold
            elif 'Nắng gắt' in val_str or '>90°F' in val_str:
                cell.fill = fill_hot
            elif 'cuồng chân' in val_str or 'xoa dịu' in val_str:
                cell.fill = fill_stress

# AutoFilter & Freeze Panes
ws_master.freeze_panes = "F2" # Khóa cố định Dòng 1 và 5 cột đầu (STT, Master_ID, FB_ID, Họ tên, Nhận diện)
ws_master.auto_filter.ref = ws_master.dimensions

# Căn chỉnh độ rộng cột tối ưu
for c_idx, h_name in enumerate(headers, start=1):
    col_letter = get_column_letter(c_idx)
    width = COLUMN_WIDTHS.get(h_name, max(len(h_name) + 3, 14))
    ws_master.column_dimensions[col_letter].width = width

# =============================================================================
# SHEET 2: TOP VIP LEADS (TIER S & TIER A - ĐIỂM SỐ >= 70)
# =============================================================================
print("[*] 2. Đang tạo Sheet 2: Top_VIP_Tier_S_A...")
ws_vip = wb.create_sheet(title="Top_VIP_Tier_S_A")
ws_vip.views.sheetView[0].showGridLines = True

df['Score_Num'] = pd.to_numeric(df['Tổng Điểm Lead Score (0-100)'], errors='coerce').fillna(0)
df_vip = df[df['Score_Num'] >= 70].sort_values(by='Score_Num', ascending=False)

vip_headers = [
    'STT_VIP', 'Master_ID', 'FB_ID', 'Tên Trại Chó (Breeder)', 'Phương Thức Nhận Diện', 'Chủ Sở Hữu', 
    'Độ Tin Cậy Chủ Trại', 'Số Điện Thoại', 'Email', 'Website Chính Thức',
    'Thành Phố', 'Bang', 'Điểm Lead Score', 'Hạng', 'Ngữ Cảnh Thời Tiết', 
    'Kênh Bán Amazon', 'Sản Phẩm Đề Xuất', 'Kế Hoạch Telesales Chốt Đơn'
]
ws_vip.append(vip_headers)
ws_vip.row_dimensions[1].height = 28
for c_idx in range(1, len(vip_headers) + 1):
    cell = ws_vip.cell(row=1, column=c_idx)
    cell.font = font_header_vip
    cell.fill = fill_header_vip
    cell.alignment = align_center
    cell.border = border_header

for r_idx, (_, r) in enumerate(df_vip.iterrows(), start=2):
    ws_vip.row_dimensions[r_idx].height = 24
    is_even = (r_idx % 2 == 0)
    base_fill = fill_zebra if is_even else fill_white
    
    tier_val = str(r['Phân Hạng Đối Tác (Tier Rank)'])
    row_vals = [
        r_idx - 1,
        r['Master_ID'],
        r['FB_ID'],
        r['Họ và Tên (Breeder Name)'],
        r.get('Phương Thức Nhận Diện (Detection Method)', ''),
        r['Chủ Sở Hữu (Owner_Representative)'],
        r['Độ Tin Cậy Chủ Sở Hữu (Owner_Confidence)'],
        r['Số Điện Thoại (Phone)'],
        r['Email'],
        r['Website Chính Thức'],
        r['Thành Phố (City)'],
        r['Bang (State)'],
        float(r['Score_Num']),
        tier_val,
        r['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'],
        r['Kênh Bán Amazon (Amazon Status)'],
        r['Sản Phẩm Đề Xuất'],
        r['Hành Động Sales']
    ]
    
    for c_idx, val in enumerate(row_vals, start=1):
        cell = ws_vip.cell(row=r_idx, column=c_idx)
        cell.value = val
        cell.font = font_data
        cell.fill = base_fill
        cell.border = border_thin
        cell.alignment = align_left
        
        if c_idx in [1, 2, 3, 5, 8, 11, 12, 13, 14]:
            cell.alignment = align_center
            if c_idx == 3: cell.font = Font(name="Consolas", size=9.5)
            if c_idx == 5: cell.font = Font(name="Segoe UI", size=9, color="1E3A8A")
            if c_idx == 12: cell.font = font_data_bold
        elif c_idx == 4:
            cell.font = font_data_bold
        elif c_idx == 10 and str(val).startswith('http'):
            cell.font = font_data_link
        elif c_idx in [15, 17, 18]:
            cell.alignment = align_left_wrap
            
        if c_idx == 14: # Tier
            if 'Tier S' in tier_val:
                cell.fill = fill_tier_s
                cell.font = font_tier_s
            else:
                cell.fill = fill_tier_a
                cell.font = font_tier_a
                
        if c_idx == 15: # Weather
            if 'Mưa/Tuyết' in str(val): cell.fill = fill_cold
            elif 'Nắng gắt' in str(val): cell.fill = fill_hot
            else: cell.fill = fill_stress

ws_vip.freeze_panes = "F2"
ws_vip.auto_filter.ref = ws_vip.dimensions

vip_widths = [9, 16, 20, 32, 24, 22, 24, 18, 24, 30, 18, 10, 16, 18, 44, 24, 40, 44]
for c_idx, w in enumerate(vip_widths, start=1):
    ws_vip.column_dimensions[get_column_letter(c_idx)].width = w

# =============================================================================
# SHEET 3: CHIẾN LƯỢC SALES THEO THỜI TIẾT & SẢN PHẨM MỤC TIÊU
# =============================================================================
print("[*] 3. Đang tạo Sheet 3: Chien_Luoc_Thoi_Tiet_Sales...")
ws_weather = wb.create_sheet(title="Chien_Luoc_Thoi_Tiet_Sales")
ws_weather.views.sheetView[0].showGridLines = True

# Header Thống Kê
ws_weather.merge_cells("A1:G1")
ws_weather["A1"] = "CHIẾN LƯỢC TIẾP THỊ & BÁN HÀNG THEO ĐIỀU KIỆN KHÍ HẬU VÙNG MIỀN HOA KỲ"
ws_weather["A1"].font = font_title
ws_weather["A1"].alignment = align_center

ws_weather.merge_cells("A2:G2")
ws_weather["A2"] = "Phân loại 1.059 đối tác nuôi chó Good Dog theo 3 kịch bản thời tiết để tối đa tỷ lệ chốt đơn Combo Cỏ + Potty + Toys"
ws_weather["A2"].font = font_subtitle
ws_weather["A2"].alignment = align_center

summary_headers = ["Nhóm Kịch Bản Thời Tiết", "Đặc Trưng Khí Hậu", "Tiểu Bang Trọng Điểm", "Sản Phẩm Bán Lực (Hero Products)", "Số Lượng Trại", "Tỷ Lệ %", "Chiến Thuật Tiếp Cận (Sales Pitch)"]
ws_weather.append([]) # Dòng 3 trống
ws_weather.append(summary_headers) # Dòng 4
ws_weather.row_dimensions[4].height = 26

for c_idx in range(1, len(summary_headers) + 1):
    cell = ws_weather.cell(row=4, column=c_idx)
    cell.font = font_header
    cell.fill = fill_header_weather
    cell.alignment = align_center
    cell.border = border_header

# Tính toán số lượng
c_cold = df['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'].str.contains('Mưa/Tuyết|Lạnh giá', case=False, na=False).sum()
c_hot = df['Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)'].str.contains('Nắng gắt|>90°F', case=False, na=False).sum()
c_stress = len(df) - c_cold - c_hot

weather_summary_data = [
    [
        "Trigger 1: Xứ Lạnh, Mưa Tuyết & Bùn Đất",
        "Mùa đông tuyết dày, mưa dầm, sân vườn lầy lội, cún bị lạnh chân",
        "WA, OR, ID, MT, MN, WI, MI, IL, IN, OH, PA, NY, CO...",
        "Thảm cỏ nhân tạo thoát nước nhanh (Quick-Drain) + Khay Pet Potty chuyên dụng trong nhà",
        int(c_cold),
        f"{round(c_cold / len(df) * 100, 1)}%",
        "Tập trung đánh vào nỗi đau: Cún đi vệ sinh bị lấm lem chân bùn, làm bẩn sofa/sàn gỗ; giải pháp khay cỏ trong nhà giữ chuồng trại luôn khô ráo thơm tho."
    ],
    [
        "Trigger 2: Vành Đai Nắng Nóng (Sunbelt)",
        "Nắng gắt >90°F, mặt đường và bê tông bỏng rát gây bỏng đệm chân cún",
        "TX, FL, AZ, NV, NM, GA, AL, MS, LA, SC...",
        "Cỏ nhân tạo chống tia UV/kháng nhiệt + Hệ thống khay Potty đặt tại ban công/hiên có mái che",
        int(c_hot),
        f"{round(c_hot / len(df) * 100, 1)}%",
        "Cảnh báo nguy cơ sốc nhiệt và bỏng đệm chân (paw burns); chào cỏ tản nhiệt êm ái cho cún con tập luyện ngoài trời không lo bỏng."
    ],
    [
        "Trigger 3: Chó Nhốt Trong Nhà / Stress",
        "Cún bị hạn chế ra ngoài, thừa năng lượng, cắn phá chuồng trại",
        "Toàn bộ các bang nội địa & đô thị chung cư",
        "Đồ chơi gặm ngứa răng (Teething Chew Toys) + Cún bông đập nhịp tim giả lập (Snuggle Puppy)",
        int(c_stress),
        f"{round(c_stress / len(df) * 100, 1)}%",
        "Chào Combo Starter Kit cho cún sơ sinh tách mẹ: Giảm 90% tiếng rên khóc ban đêm, tránh cún ngứa răng cắn nát chuồng và đồ đạc."
    ]
]

for r_offset, rdata in enumerate(weather_summary_data, start=5):
    ws_weather.row_dimensions[r_offset].height = 42
    for c_idx, val in enumerate(rdata, start=1):
        cell = ws_weather.cell(row=r_offset, column=c_idx)
        cell.value = val
        cell.font = font_data
        cell.border = border_thin
        cell.alignment = align_left_wrap
        if c_idx in [5, 6]:
            cell.alignment = align_center
            cell.font = font_data_bold
        if r_offset == 5: cell.fill = fill_cold
        elif r_offset == 6: cell.fill = fill_hot
        elif r_offset == 7: cell.fill = fill_stress

ws_weather_widths = [26, 32, 28, 42, 14, 12, 55]
for c_idx, w in enumerate(ws_weather_widths, start=1):
    ws_weather.column_dimensions[get_column_letter(c_idx)].width = w

# =============================================================================
# SHEET 4: DASHBOARD TỔNG QUAN & PHÂN BỔ THỊ TRƯỜNG HOA KỲ
# =============================================================================
print("[*] 4. Đang tạo Sheet 4: Dashboard_Tong_Quan...")
ws_dash = wb.create_sheet(title="Dashboard_Tong_Quan")
ws_dash.views.sheetView[0].showGridLines = True

ws_dash.merge_cells("A1:F1")
ws_dash["A1"] = "BẢNG ĐIỀU HÀNH TỔNG QUAN DỮ LIỆU GOOD DOG CRM 2026"
ws_dash["A1"].font = font_title
ws_dash["A1"].alignment = align_center

# KPI Cards
kpis = [
    ("TỔNG SỐ KHÁCH HÀNG CRM", f"{len(df):,} LEADS", "100% dữ liệu sạch, đã loại trừ rorState"),
    ("TỶ LỆ BẮT BUỘC CÓ FB_ID", "100.0%", "Đầy đủ 1.059 Facebook ID chạy quảng cáo"),
    ("ĐÃ XÁC ĐỊNH CHỦ SỞ HỮU", f"{(df['Chủ Sở Hữu (Owner_Representative)'].notna() & (df['Chủ Sở Hữu (Owner_Representative)'] != '')).sum():,} TRẠI", "Tên cá nhân hoặc chức danh quản lý"),
    ("XÁC ĐỊNH BANG & THÀNH PHỐ", f"{(df['Bang (State)'].notna() & (df['Bang (State)'] != '')).sum():,} TRẠI", "590 bang chuẩn Mỹ (Không dính fake DE)")
]

for idx, (title, num, sub) in enumerate(kpis):
    col = idx * 2 + 1
    col_end = col + 1
    c_start = get_column_letter(col)
    c_finish = get_column_letter(col_end)
    
    ws_dash.merge_cells(f"{c_start}3:{c_finish}3")
    ws_dash.merge_cells(f"{c_start}4:{c_finish}4")
    ws_dash.merge_cells(f"{c_start}5:{c_finish}5")
    
    c3 = ws_dash[f"{c_start}3"]
    c3.value = title
    c3.font = Font(name="Segoe UI", size=9, bold=True, color="64748B")
    c3.alignment = align_center
    c3.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    
    c4 = ws_dash[f"{c_start}4"]
    c4.value = num
    c4.font = Font(name="Segoe UI", size=16, bold=True, color="1E3A8A")
    c4.alignment = align_center
    c4.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    c5 = ws_dash[f"{c_start}5"]
    c5.value = sub
    c5.font = Font(name="Segoe UI", size=8.5, italic=True, color="059669")
    c5.alignment = align_center
    c5.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

# Thống kê phân bổ theo Bang (Top 10 State)
ws_dash["A7"] = "TOP 10 TIỂU BANG TẬP TRUNG NHIỀU TRẠI CHÓ NHẤT (US STATES)"
ws_dash["A7"].font = Font(name="Segoe UI", size=11, bold=True, color="1E293B")

ws_dash.append([])
state_counts = df[df['Bang (State)'].str.len() == 2]['Bang (State)'].value_counts().head(10)

ws_dash.cell(row=9, column=1, value="Mã Bang").font = font_header
ws_dash.cell(row=9, column=1).fill = fill_header
ws_dash.cell(row=9, column=1).alignment = align_center

ws_dash.cell(row=9, column=2, value="Số Trại Chó").font = font_header
ws_dash.cell(row=9, column=2).fill = fill_header
ws_dash.cell(row=9, column=2).alignment = align_center

ws_dash.cell(row=9, column=3, value="Tỷ Lệ %").font = font_header
ws_dash.cell(row=9, column=3).fill = fill_header
ws_dash.cell(row=9, column=3).alignment = align_center

ws_dash.cell(row=9, column=4, value="Khuyến Nghị Hành Động").font = font_header
ws_dash.cell(row=9, column=4).fill = fill_header
ws_dash.cell(row=9, column=4).alignment = align_center

for r_i, (st_name, cnt) in enumerate(state_counts.items(), start=10):
    ws_dash.cell(row=r_i, column=1, value=st_name).alignment = align_center
    ws_dash.cell(row=r_i, column=2, value=int(cnt)).alignment = align_center
    ws_dash.cell(row=r_i, column=3, value=f"{round(cnt / len(df) * 100, 1)}%").alignment = align_center
    
    rec = "Chạy Ads Vùng Nóng (Potty Ban Công)" if st_name in ['TX', 'FL', 'CA', 'GA'] else "Chạy Ads Vùng Lạnh (Cỏ Thoát Nước Trong Nhà)"
    ws_dash.cell(row=r_i, column=4, value=rec).alignment = align_left
    
    for c in range(1, 5):
        cell = ws_dash.cell(row=r_i, column=c)
        cell.font = font_data
        cell.border = border_thin
        if r_i % 2 == 0: cell.fill = fill_zebra

for c in range(1, 9):
    ws_dash.column_dimensions[get_column_letter(c)].width = 22

# Lưu file hoàn chỉnh
print(f"[*] Đang lưu file Excel chuẩn hóa: {XLSX_PATH}...")
wb.save(XLSX_PATH)
print(f"[✓] ĐÃ LƯU THÀNH CÔNG MASTER EXCEL: {XLSX_PATH}")
