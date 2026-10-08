import csv
import re
import urllib.parse
import sys

def is_us_location(intro, website):
    # Keywords indicating USA
    us_keywords = ["united states", "usa", "hoa kỳ", "new york", "california", "texas", "florida", 
                   "washington", "illinois", "ohio", "michigan", "pennsylvania", "georgia", 
                   "north carolina", "south carolina", "virginia", "colorado", "arizona", "tennessee", 
                   "maryland", "massachusetts", "wisconsin", "oregon", "alaska"]
    
    text_to_search = (str(intro) + " " + urllib.parse.unquote(str(website))).lower()
    
    for kw in us_keywords:
        if kw in text_to_search:
            return True
    return False

def clean_phone(phone_str):
    # Split by '|' if multiple phones
    phones = [p.strip() for p in str(phone_str).split('|') if p.strip()]
    cleaned_phones = []
    for p in phones:
        # Keep only digits and '+'
        cleaned = re.sub(r'[^\d+]', '', p)
        if cleaned:
            # If it's a US number and doesn't start with +, maybe add +1, but let's just keep digits for now
            cleaned_phones.append(cleaned)
    return cleaned_phones

def extract_emails(email_str):
    return [e.strip() for e in str(email_str).split('|') if e.strip() and '@' in e]

def process_file(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                header = ['email','email','email','phone','phone','phone','madid','fn','ln','zip','ct','st','country','dob','doby','gen','age','uid','value']
                writer = csv.writer(outfile)
                writer.writerow(header)
                
                count = 0
                for row in reader:
                    intro = row.get('Giới thiệu', '')
                    website = row.get('Website', '')
                    
                    if is_us_location(intro, website):
                        emails = extract_emails(row.get('Email', ''))
                        phones = clean_phone(row.get('Điện thoại', ''))
                        
                        # We need at least one email or phone to make it useful
                        if emails or phones:
                            # Pad emails and phones to 3 columns each
                            em_cols = (emails + ['', '', ''])[:3]
                            ph_cols = (phones + ['', '', ''])[:3]
                            
                            # Construct the row according to the format
                            out_row = [
                                em_cols[0], em_cols[1], em_cols[2],
                                ph_cols[0], ph_cols[1], ph_cols[2],
                                '', '', '', '', '', '', 'US', '', '', '', '', '', ''
                            ]
                            writer.writerow(out_row)
                            count += 1
                            
        print(f"Đã xử lý xong! Lọc được {count} dòng dữ liệu khách hàng ở Mỹ và lưu vào {output_file}")
    except FileNotFoundError:
        print(f"Không tìm thấy file: {input_file}. Vui lòng kiểm tra lại tên file.")
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    # Thay đổi tên file đầu vào và đầu ra tại đây nếu cần
    input_csv = 'fb_pages_17909450.csv'
    output_csv = 'us_audience_filtered.csv'
    
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]
        
    process_file(input_csv, output_csv)
