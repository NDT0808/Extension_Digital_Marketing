import csv
import os

INPUT_CSV = 'scored_leads_final.csv'
OUTPUT_CSV = 'telesale_leads_clean.csv'

def calculate_score(row):
    score = 0
    if row.get('WebsiteActive', '').strip().lower() == 'yes': score += 5
    if row.get('IsPuppySeller', '').strip().lower() == 'yes': score += 10
    if row.get('HasForm', '').strip().lower() == 'yes': score += 10
    if row.get('HasTakeHomeKit', '').strip().lower() == 'yes': score += 10
    if row.get('facebook_url', '').strip(): score += 5
    if row.get('instagram_url', '').strip(): score += 5
    return score

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Không tìm thấy file '{INPUT_CSV}'.")
        return

    print("🚀 Bắt đầu tối ưu hóa và làm gọn file dữ liệu...")
    
    leads = []
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
            
    results = []
    
    for idx, row in enumerate(leads):
        # Tính điểm dựa trên các trường có sẵn
        score = calculate_score(row)
        grade = row.get('AIClass', 'C') # Lấy grade có sẵn
        
        # Chỉ giữ lại các trường cực kỳ cần thiết cho đội Sale/Excel
        final_row = {
            'Name': row.get('name', ''),
            'Website': row.get('websites', ''),
            'City': row.get('city', ''),
            'State': row.get('state', ''),
            'Phones': row.get('phones', ''),
            'Emails': row.get('emails', ''),
            'Facebook': row.get('facebook_url', ''),
            'Instagram': row.get('instagram_url', ''),
            'Ban_Cho': row.get('IsPuppySeller', ''),
            'Co_Form': row.get('HasForm', ''),
            'Take_Home_Kit': row.get('HasTakeHomeKit', ''),
            'Lead_Score': score,
            'Grade': grade
        }
        results.append(final_row)
        
    fieldnames = ['Name', 'Website', 'City', 'State', 'Phones', 'Emails', 'Facebook', 'Instagram', 'Ban_Cho', 'Co_Form', 'Take_Home_Kit', 'Lead_Score', 'Grade']
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"✅ Hoàn tất! Đã rút gọn 80 cột xuống còn {len(fieldnames)} cột tinh gọn.")
    print(f"📂 File kết quả đã lưu tại: {OUTPUT_CSV}. Bạn có thể mở trực tiếp bằng Excel.")

if __name__ == '__main__':
    main()
