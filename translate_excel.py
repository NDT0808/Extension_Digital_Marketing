import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from copy import copy

# ============================================================
# BẢN ĐỒ DỊCH THUẬT: Trung -> Việt
# ============================================================
TRANSLATE = {
    # Tên sheet
    'Config': 'Cấu Hình',
    'Rules': 'Quy Tắc Chấm Điểm',
    'Leads': 'Danh Sách Tiềm Năng',

    # Config sheet - headers
    'code': 'Mã Nguồn',
    'channel': 'Kênh',
    'axis': 'Phân Loại Trục',
    'tier': 'Hạng',
    'baseScore': 'Điểm Gốc',
    'decay': 'Giảm Dần Theo Thời Gian',
    'audienceName': 'Tên Tệp Đối Tượng',
    'audienceAction': 'Hành Động Tương Ứng',
    'audiencePriority': 'Mức Độ Ưu Tiên',

    # Config - axis values
    'customer': 'Khách Hàng',
    'engagement': 'Tương Tác',
    'ai': 'AI Phân Loại',

    # Config - audienceName values (Chinese -> VN)
    'LAL 相似受众': 'Tệp Tương Tự (Lookalike)',
    'A3 互动者再营销': 'A3 Retarget Người Đã Tương Tác',
    '爆款截流自定义受众': 'Tệp Bài Viral Tùy Chỉnh',
    'AI 高相关自定义受众': 'Tệp AI Độ Liên Quan Cao',
    '广向/兴趣拓展受众': 'Tệp Mở Rộng Theo Sở Thích',

    # Config - audienceAction values
    '生成种子受众扩量': 'Tạo Seed Audience Mở Rộng',
    '最高优先级人工跟进+再营销': 'Ưu Tiên Cao Nhất: Chăm Sóc Thủ Công + Retarget',
    '自定义受众+反哺选题': 'Custom Audience + Phản Hồi Chọn Chủ Đề',
    '复核后打标签清洗入库': 'Xác Nhận Rồi Gán Nhãn Vào Kho',
    '漏斗顶层扩面': 'Mở Rộng Đỉnh Phễu (ToFu)',

    # Rules sheet - keys
    'key': 'Khóa Cấu Hình',
    'value': 'Giá Trị',
    'multiTagThreshold': 'Ngưỡng Đa Nhãn (Số Nguồn Tối Thiểu)',
    'multiTagBonus': 'Điểm Thưởng Đa Nhãn',
    'tierA': 'Ngưỡng Điểm Hạng A (VIP)',
    'tierB': 'Ngưỡng Điểm Hạng B (Tiềm Năng)',
    'fullWeightDays': 'Số Ngày Tính Điểm Đầy Đủ',
    'zeroWeightDays': 'Số Ngày Điểm Bằng 0 (Không Hoạt Động)',

    # Leads sheet - headers
    '序号': 'STT',
    'prospectId': 'Mã Khách Hàng Tiềm Năng',
    'lastActiveDays': 'Số Ngày Không Hoạt Động',
    'score': 'Điểm',
    'tier': 'Hạng (S/A/B)',
    'primaryAudience': 'Tệp Đối Tượng Chính',
    '公司名': 'Tên Công Ty / Trại Chó',
    '公司网址': 'Website',
    '公司性质': 'Loại Hình Kinh Doanh',
    '电话': 'Số Điện Thoại',
    '邮件': 'Email',
    '地址': 'Địa Chỉ',
    '联系人': 'Người Liên Hệ',
    '备注': 'Ghi Chú',
}

def translate(val):
    """Dịch một giá trị từ Trung -> Việt nếu có trong từ điển"""
    if val is None:
        return val
    s = str(val).strip()
    return TRANSLATE.get(s, val)

# ============================================================
# ĐỌC FILE GỐC
# ============================================================
src_path = r'c:\Users\ASUS\Downloads\Marketing_Pet&Grass\潜客统计月表.xlsx'
dst_path = r'c:\Users\ASUS\Downloads\Marketing_Pet&Grass\bang_thong_ke_tiem_nang_khach_hang.xlsx'

wb_src = openpyxl.load_workbook(src_path, data_only=True)
wb_dst = openpyxl.Workbook()
wb_dst.remove(wb_dst.active)  # Xóa sheet mặc định

sheet_name_map = {
    'Config': 'Cấu Hình',
    'Rules': 'Quy Tắc Chấm Điểm',
    'Leads': 'Danh Sách Tiềm Năng',
}

for src_name in wb_src.sheetnames:
    ws_src = wb_src[src_name]
    dst_name = sheet_name_map.get(src_name, src_name)
    ws_dst = wb_dst.create_sheet(title=dst_name)

    # Copy column widths
    for col_letter, col_dim in ws_src.column_dimensions.items():
        ws_dst.column_dimensions[col_letter].width = col_dim.width if col_dim.width else 15

    # Copy row heights
    for row_idx, row_dim in ws_src.row_dimensions.items():
        ws_dst.row_dimensions[row_idx].height = row_dim.height

    for row in ws_src.iter_rows():
        for cell in row:
            dst_cell = ws_dst.cell(row=cell.row, column=cell.column)

            # Dịch giá trị
            dst_cell.value = translate(cell.value)

            # Copy style
            if cell.has_style:
                try:
                    dst_cell.font = copy(cell.font)
                    dst_cell.fill = copy(cell.fill)
                    dst_cell.border = copy(cell.border)
                    dst_cell.alignment = copy(cell.alignment)
                    dst_cell.number_format = cell.number_format
                except:
                    pass

    # Copy merged cells
    for merged_range in ws_src.merged_cells.ranges:
        ws_dst.merge_cells(str(merged_range))

print("=== KẾT QUẢ DỊCH THUẬT ===")
for src_name, dst_name in sheet_name_map.items():
    ws = wb_src[src_name]
    print(f"  Sheet '{src_name}' -> '{dst_name}': {ws.max_row} dòng x {ws.max_column} cột")

wb_dst.save(dst_path)
print(f"\n✅ Đã lưu file tiếng Việt: bang_thong_ke_tiem_nang_khach_hang.xlsx")
print("\n📋 CHÚ THÍCH CẤU TRÚC FILE:")
print("  Sheet 1 'Cấu Hình'    : Định nghĩa từng nguồn dữ liệu (AKC, Reels...),")
print("                           điểm gốc, tệp đối tượng tương ứng.")
print("  Sheet 2 'Quy Tắc'     : Ngưỡng để xếp hạng A/B/S, thưởng đa nguồn,")
print("                           và quy tắc giảm điểm theo thời gian.")
print("  Sheet 3 'Tiềm Năng'   : Danh sách 501 khách hàng tiềm năng, ghi lại")
print("                           ngày tương tác trong tháng (cột 1-31),")
print("                           điểm, hạng, và thông tin liên hệ.")
