import urllib.parse
import os
import re

input_file = r'c:\Users\ASUS\Downloads\Marketing_Pet&Grass\website_list3_9-10.txt'
output_file = r'c:\Users\ASUS\Downloads\Marketing_Pet&Grass\classified_websites.md'

def clean_url(url):
    url = url.strip()
    if not url: return ""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if 'fbclid' in query:
        del query['fbclid']
    if 'utm_source' in query:
        del query['utm_source']
    if 'utm_medium' in query:
        del query['utm_medium']
    if 'utm_campaign' in query:
        del query['utm_campaign']
    new_query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query)).strip()

def classify(url):
    low = url.lower()
    
    if low.startswith('mailto:'):
        return "Email / Liên hệ (Mailto)"
    
    social_domains = ['tiktok.com', 'youtube.com', 'linktr.ee', 'instabio.cc', 'paypal.me', 'amazon.', 'zalo.me', 'facebook.com', 'instagram.com', 't.me', 'wa.me', 'twitter.com', 'x.com', 'pinterest.com', 'snapchat.com', 'campsite.bio', 'hoobe.com', 'direct.me', 'stan.store', 'giphy.com', 'teaming.net', 'google.com/forms', 'docs.google.com/forms']
    if any(d in low for d in social_domains):
        return "Mạng xã hội & Nền tảng chia sẻ (Social Media/Video)"
         
    rescue_words = ['rescue', 'shelter', 'adopt', 'protectora', 'fundacion', 'foundation', 'save', 'hopefulpaws', 'animalrescue', 'asociacion', 'refugio', 'spca', 'league']
    if any(w in low for w in rescue_words):
        return "Tổ chức cứu hộ, Trạm động vật (Rescue/Shelters)"
        
    store_words = ['store', 'shop', 'supply', 'supplies', 'petco', 'petsmart', 'collar', 'leash', 'apparel', 'gear', 'boutique', 'food', 'nutrition', 'petbrokers', 'amazon']
    if any(w in low for w in store_words):
        return "Cửa hàng vật nuôi & Phụ kiện (Pet Stores/Supplies)"
        
    vet_words = ['vet', 'hospital', 'clinic', 'health', 'medical', 'dental', 'zoetis', 'care', 'cancer', 'healing']
    if any(w in low for w in vet_words):
        return "Thú y & Sức khỏe động vật (Vet/Health)"
        
    train_words = ['train', 'agility', 'groom', 'board', 'daycare', 'camp', 'resort', 'guard', 'obedience', 'k9', 'canine-education', 'canineeducation', 'doglaw', 'educationcanine']
    if any(w in low for w in train_words):
        return "Dịch vụ chăm sóc & Huấn luyện (Grooming/Boarding/Training)"
        
    land_words = ['turf', 'grass', 'lawn', 'landscape']
    if any(w in low for w in land_words):
        return "Công ty cảnh quan / Cỏ nhân tạo (Landscaping/Artificial Turf)"
        
    breeder_words = ['breeder', 'kennel', 'puppy', 'puppies', 'pup', 'doodle', 'retriever', 'bulldog', 'aussie', 'spaniel', 'lab', 'dachshund', 'frenchie', 'schnauzer', 'chiens', 'hound', 'poodle', 'cavalier', 'bichon', 'husky', 'cocker', 'mastiff', 'terrier', 'akc', 'farm', 'ranch']
    if any(w in low for w in breeder_words):
        return "Trại nhân giống & Bán chó (Breeders/Kennels)"
        
    if 'tech' in low or 'firm' in low or 'drama' in low or 'news' in low or 'law' in low:
        return "Khác (Dịch vụ ngoài ngành thú cưng/Chính phủ/BĐS)"
        
    return "Khác / Chưa rõ ràng (Trang cá nhân/Blog/Cần kiểm tra thêm)"

urls = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.split('|')
        for part in parts:
            part = part.strip()
            if part.startswith('http'):
                clean = clean_url(part)
                if clean:
                    urls.append(clean)

urls = list(set(urls))
urls.sort()

categories = {
    "Trại nhân giống & Bán chó (Breeders/Kennels)": [],
    "Khác / Chưa rõ ràng (Trang cá nhân/Blog/Cần kiểm tra thêm)": [],
    "Email / Liên hệ (Mailto)": [],
    "Dịch vụ chăm sóc & Huấn luyện (Grooming/Boarding/Training)": [],
    "Khác (Dịch vụ ngoài ngành thú cưng/Chính phủ/BĐS)": [],
    "Công ty cảnh quan / Cỏ nhân tạo (Landscaping/Artificial Turf)": [],
    "Tổ chức cứu hộ, Trạm động vật (Rescue/Shelters)": [],
    "Mạng xã hội & Nền tảng chia sẻ (Social Media/Video)": [],
    "Cửa hàng vật nuôi & Phụ kiện (Pet Stores/Supplies)": [],
    "Thú y & Sức khỏe động vật (Vet/Health)": []
}

for u in urls:
    cat = classify(u)
    categories[cat].append(u)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"# Phân loại chi tiết danh sách Website\n\n")
    f.write(f"Tổng số URL phân tích: {len(urls)}\n\n")
    
    for cat in categories.keys():
        f.write(f"## {cat} ({len(categories[cat])} URLs)\n")
        for i, u in enumerate(categories[cat], 1):
            f.write(f"{i}. {u}\n")
        f.write("\n")

print(f"File created: {output_file}")
