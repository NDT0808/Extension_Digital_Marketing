import pandas as pd

# Giả lập dữ liệu mà Plugin của bạn trả về sau khi cào
# Dữ liệu này là danh sách những người mà A, B, C ĐANG THEO DÕI (Following)
mock_plugin_data = {
    "A": {"B", "C", "D", "E", "F", "X1", "X2"}, # Khách hàng A theo dõi những người này
    "B": {"C", "D", "E", "M1", "M2"},           # Khách hàng B theo dõi những người này
    "C": {"B", "D", "F", "N1", "N2"},           # Khách hàng C theo dõi những người này
    "Z": {"M1", "M2", "M3", "M4"}               # Khách hàng Z (Một người random, không liên quan tới ngách)
}

# 1. Hàm tính điểm uy tín (Authority Score) dựa trên mạng lưới
def calculate_authority_score(target_user, plugin_data, seed_list):
    """
    Tính điểm uy tín của target_user bằng cách đếm xem có bao nhiêu người
    trong seed_list (những người target_user theo dõi) CŨNG theo dõi lẫn nhau.
    """
    # Lấy danh sách những người target_user đang theo dõi
    following_list = plugin_data.get(target_user, set())
    if not following_list:
        return 0

    score = 0
    mutual_connections = []

    # So sánh vòng lặp (Đưa B, C, D... lên bàn cân)
    for user in following_list:
        if user in plugin_data:
            # Thuật toán Lõi: Phép toán Giao tập hợp (Intersection)
            # Tìm những người mà cả Target User VÀ User(B,C,D...) CÙNG THEO DÕI
            common_following = following_list.intersection(plugin_data[user])
            
            # Nếu có điểm chung, cộng điểm
            if len(common_following) > 0:
                score += len(common_following)
                mutual_connections.append(f"{user} có chung {len(common_following)} liên kết")

    print(f"\n[PHÂN TÍCH] Khách hàng: {target_user}")
    print(f"- Số người theo dõi: {len(following_list)}")
    print(f"- Chi tiết liên kết chéo: {mutual_connections}")
    print(f"=> ĐIỂM UY TÍN (AUTHORITY SCORE): {score} điểm")
    
    return score

# 2. Chạy thử nghiệm thuật toán
print("--- BẮT ĐẦU CHẠY THUẬT TOÁN ĐÁNH GIÁ MẠNG LƯỚI ---")

# Kiểm tra A (Khách hàng tiềm năng thật sự - có liên kết chéo dày đặc)
score_a = calculate_authority_score("A", mock_plugin_data, mock_plugin_data["A"])
if score_a >= 3:
    print(">>> GẮN NHÃN: [VIP - Hạt giống Ngành]")

# Kiểm tra Z (Khách hàng rác/không có liên kết chéo với ai trong ngách)
score_z = calculate_authority_score("Z", mock_plugin_data, mock_plugin_data["Z"])
if score_z < 3:
    print(">>> GẮN NHÃN: [Loại bỏ - Không có liên kết ngách]")

print("\n---------------------------------------------------")
print("Bằng cách này, máy tính đếm hàng triệu dữ liệu chỉ mất chưa tới 1 giây!")
