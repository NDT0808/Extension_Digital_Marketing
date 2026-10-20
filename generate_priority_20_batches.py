import os
import re
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

WORKSPACE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass"
CRM_CSV = os.path.join(WORKSPACE, "GoodDog_Followers_Master_CRM_2026-10-15.csv")
OUT_XLSX = os.path.join(WORKSPACE, "GoodDog_Priority_20_Leads_Batches_2026-10-15.xlsx")
TEMPLATE_XLSX = os.path.join(WORKSPACE, "priority-data-8-20261013.xlsx")

print("[*] 1. Khởi động tạo bộ bảng 20 tên theo chuẩn Sếp...")
df_crm = pd.read_csv(CRM_CSV, encoding='utf-8-sig', dtype=str).fillna('')
df_tpl = pd.read_excel(TEMPLATE_XLSX, nrows=1)
ENTERPRISE_COLS = list(df_tpl.columns)

# Đảm bảo cột cuối là CRM NO. / FB_ID
if 'CRM NO.' in ENTERPRISE_COLS and 'FB_ID' not in ENTERPRISE_COLS:
    ENTERPRISE_COLS[ENTERPRISE_COLS.index('CRM NO.')] = 'CRM NO. (FB_ID Bắt Buộc)'

# Sắp xếp theo Lead Score giảm dần
df_crm['Score_Num'] = pd.to_numeric(df_crm['Tổng Điểm Lead Score (0-100)'], errors='coerce').fillna(0)
df_sorted = df_crm.sort_values(by='Score_Num', ascending=False).reset_index(drop=True)

# Khởi tạo Workbook
wb = openpyxl.Workbook()
wb.remove(wb.active)

# Styles
font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
font_data = Font(name="Segoe UI", size=9.5, color="1E293B")
font_data_bold = Font(name="Segoe UI", size=9.5, bold=True, color="1E293B")
font_data_link = Font(name="Segoe UI", size=9.5, color="2563EB", underline="single")
font_id = Font(name="Consolas", size=9.5, bold=True, color="1E3A8A")

fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Royal Blue
fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
fill_tier_s = PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid")
font_tier_s = Font(name="Segoe UI", size=9.5, bold=True, color="5B21B6")

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

BATCH_SIZE = 20
NUM_BATCHES = 5 # Xuất 5 bảng Top 20 (Tổng 100 Hot Leads VIP nhất)

def map_lead_to_enterprise(r, batch_idx, rank_in_batch):
    full_name = r.get('Chủ Sở Hữu (Owner_Representative)', '').strip()
    first_name = full_name.split()[0] if full_name else ''
    last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
    
    clean_ph = re.sub(r'\D', '', str(r.get('Số Điện Thoại (Phone)', '')))
    phone_num = f"1{clean_ph[-10:]}" if len(clean_ph) >= 10 else clean_ph
    
    remark_str = (
        f"[{r.get('Phương Thức Nhận Diện (Detection Method)', '')}] "
        f"Score: {r.get('Tổng Điểm Lead Score (0-100)', '')}đ | "
        f"{r.get('Ngữ Cảnh Thời Tiết & Gợi Ý Chốt Đơn (Weather Trigger)', '')} | "
        f"Gợi ý: {r.get('Sản Phẩm Đề Xuất', '')}"
    )
    
    row_dict = {
        '邮箱地址': r.get('Email', '').strip(),
        '邮箱地址状态': 'valid' if r.get('Email', '').strip() else '',
        '名字': first_name,
        '姓氏': last_name,
        '全名': full_name,
        '用户社交': r.get('Facebook URL', '').strip(),
        'LinkedIn': '',
        '工作职位': 'Owner / Head Breeder',
        '国家': 'United States',
        '地址': r.get('Địa Chỉ (Address)', '').strip(),
        '行业': 'Dog Breeding & Pet Wholesale',
        '添加日期': '2026-10-15 14:00:00',
        '公司名称': r.get('Họ và Tên (Breeder Name)', '').strip(),
        '公司网址': r.get('Website Chính Thức', '').strip(),
        '公司社交': r.get('Instagram URL', '').strip(),
        '公司规模': '1-10 dogs',
        '公司所处国家': 'United States',
        '公司位置': f"{r.get('Thành Phố (City)', '')}, {r.get('Bang (State)', '')} {r.get('Mã Zip (Zip Code)', '')}".strip(' ,'),
        '州': r.get('Bang (State)', '').strip(),
        '城市': r.get('Thành Phố (City)', '').strip(),
        '公司所在行业': 'Pet Supplies Wholesale',
        '总部电话': phone_num,
        '电话': phone_num,
        '背调链接': r.get('Facebook URL', '').strip(),
        '测试打开次数': 0,
        '客户等级': r.get('Phân Hạng Đối Tác (Tier Rank)', '').strip(),
        '打开网页': r.get('Website Chính Thức', '').strip(),
        '营销更新': r.get('Thời Gian Đăng Bài Gần Nhất', '').strip(),
        '回复次数': r.get('Số Bình Luận', 0),
        '营销打开次数': r.get('Lượt Cảm Xúc', 0),
        '营销邮件次数': 0,
        '营销邮件数量': 0,
        '年级/班级': f"Batch_{batch_idx:02d}_Top20",
        '班级': '20_Hot_Leads_Daily_Batch',
        '休眠原因': '',
        'remark': remark_str,
        'CRM NO. (FB_ID Bắt Buộc)': str(r.get('FB_ID', '')).strip() # Khóa duy nhất chống trùng lặp
    }
    return [row_dict.get(c, '') for c in ENTERPRISE_COLS]

print(f"[*] 2. Đang tạo {NUM_BATCHES} Sheet (Mỗi sheet ĐÚNG {BATCH_SIZE} TÊN)...")

for b_idx in range(1, NUM_BATCHES + 1):
    sheet_title = f"Batch_{b_idx:02d}_Top20"
    ws = wb.create_sheet(title=sheet_title)
    ws.views.sheetView[0].showGridLines = True
    
    # Header Row
    ws.append(ENTERPRISE_COLS)
    ws.row_dimensions[1].height = 28
    for c_idx in range(1, len(ENTERPRISE_COLS) + 1):
        cell = ws.cell(row=1, column=c_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_header

    # Cắt đúng 20 khách hàng
    start_pos = (b_idx - 1) * BATCH_SIZE
    end_pos = start_pos + BATCH_SIZE
    df_batch = df_sorted.iloc[start_pos:end_pos]
    
    for r_idx, (_, r) in enumerate(df_batch.iterrows(), start=2):
        ws.row_dimensions[r_idx].height = 24
        is_even = (r_idx % 2 == 0)
        base_fill = fill_zebra if is_even else fill_white
        
        row_vals = map_lead_to_enterprise(r, b_idx, r_idx - 1)
        for c_idx, val in enumerate(row_vals, start=1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.value = val
            cell.font = font_data
            cell.fill = base_fill
            cell.border = border_thin
            cell.alignment = align_left
            
            c_name = ENTERPRISE_COLS[c_idx - 1]
            if c_name in ['邮箱地址状态', '工作职位', '国家', '添加日期', '州', '城市', '客户等级', '年级/班级', '班级', '测试打开次数', '回复次数', '营销打开次数', '营销邮件次数', '营销邮件数量']:
                cell.alignment = align_center
            elif c_name in ['公司网址', '用户社交', '公司社交', '打开网页', '背调链接'] and str(val).startswith('http'):
                cell.font = font_data_link
            elif c_name in ['全名', '公司名称']:
                cell.font = font_data_bold
            elif c_name == 'CRM NO. (FB_ID Bắt Buộc)':
                cell.alignment = align_center
                cell.font = font_id
                cell.value = str(val) # Giữ chuỗi số nguyên vẹn
                
            if c_name == '客户等级':
                cell.fill = fill_tier_s
                cell.font = font_tier_s

    # AutoFilter & Freeze Panes
    ws.freeze_panes = "F2" # Khóa cố định đến cột 全名 (Full Name)
    ws.auto_filter.ref = ws.dimensions
    
    # Column Widths
    for c_idx, col_name in enumerate(ENTERPRISE_COLS, start=1):
        col_letter = get_column_letter(c_idx)
        if col_name in ['全名', '公司名称', '公司网址', '用户社交']:
            ws.column_dimensions[col_letter].width = 30
        elif col_name in ['邮箱地址', 'CRM NO. (FB_ID Bắt Buộc)', '电话', '总部电话']:
            ws.column_dimensions[col_letter].width = 24
        elif col_name in ['remark']:
            ws.column_dimensions[col_letter].width = 50
        else:
            ws.column_dimensions[col_letter].width = max(len(col_name) * 2 + 2, 14)

print(f"[*] 3. Đang lưu file Excel chuẩn doanh nghiệp: {OUT_XLSX}...")
wb.save(OUT_XLSX)
print(f"[✓] HOÀN TẤT! Đã xuất file {OUT_XLSX} với {NUM_BATCHES} sheet, mỗi sheet chứa đúng {BATCH_SIZE} tên và có cột khóa FB_ID!")
