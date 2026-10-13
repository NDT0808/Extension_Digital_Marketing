import csv
import json
import re
import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CSV_FB_PATH = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\FB_PublishTime_1791866762111.csv"
XLSX_PRIO_PATH = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\priority_list_2026-10-06_v2.xlsx"

# ==============================================================================
# 1. BỘ LỌC LOẠI TRỪ (NEGATIVE EXCLUSION FILTER) - KHÔNG PHẢI KHÁCH HÀNG MỤC TIÊU
# ==============================================================================
NON_CUSTOMER_PATTERNS = [
    # 1. Hiệp hội phả hệ, CLB quốc gia (AKC, UKC, Westminster - không mua kit cún con)
    r'american\s*kennel\s*club', r'\bakc\b', r'westminster\s*kennel\s*club', r'national\s*purebred',
    r'\bukc\b', r'canadian\s*kennel\s*club', r'the\s*kennel\s*club', r'\bfci\b',
    r'collie\s*club\s*of\s*america', r'golden\s*retriever\s*club', r'breed\s*club',
    
    # 2. Tập đoàn bán lẻ khổng lồ
    r'\bpetsmart\b', r'\bpetco\b', r'\bchewy\b', r'pet\s*supplies\s*plus',
    
    # 3. Kênh truyền thông, tin tức, giải trí & meme
    r'\bweratedogs\b', r'dogs\s*naturally', r'american\s*dog\s*fancier', r'\bmagazine\b',
    r'\bnews\b', r'the\s*dodo\b', r'\bdogster\b', r'\bpugloulou\b', r'magnusthetherapydog',
    r'things\s*dog\s*handlers\s*say', r'pure\s*dog\s*talk',
    
    # 4. Công ty công nghệ DNA, y tế, thú y
    r'\bembark\b', r'revival\s*animal', r'fear\s*free\b', r'\bzoetis\b',
    r'blue\s*ridge\s*veterinary\s*imaging', r'impact\s*dog\s*crates',
    
    # 5. Profile chung chung / rác
    r'^facebook\s*user$', r'^deleted\s*account$', r'^user\s*\d+$'
]

HIGH_VALUE_BREEDS = [
    'frenchie', 'frenchies', 'french bulldog', 'bulldog', 'bulldogs', 'doodle', 'doodles',
    'goldendoodle', 'bernedoodle', 'cavapoo', 'labradoodle', 'corgi', 'poodle',
    'shepherd', 'malinois', 'retriever', 'labrador', 'rottweiler', 'bullies', 'bully'
]

BREEDER_KEYWORDS = [
    'kennel', 'kennels', 'breeder', 'breeders', 'puppy', 'puppies', 'doodles', 
    'bulldog', 'bulldogs', 'retriever', 'shepherd', 'poodle', 'frenchie', 'frenchies', 
    'k9', 'farm', 'hound', 'terrier', 'mastiff', 'corgi', 'pom', 'collie', 'spaniel', 
    'labrador', 'rottweiler', 'dachshund', 'husky', 'goldendoodle', 'bernedoodle',
    'cavapoo', 'bullies', 'malinois', 'pitbull', 'aussie'
]

SERVICE_KEYWORDS = [
    'training', 'trainer', 'academy', 'k9 academy', 'dog training', 'canine educator',
    'daycare', 'boarding', 'grooming', 'pet care', 'dog hotel', 'pet resort', 'dog spa'
]

RESCUE_KEYWORDS = [
    'rescue', 'shelter', 'adoption', 'sanctuary', 'stray', 'humane society', 'animal rescue'
]

class UnifiedLeadRAGSystem:
    def __init__(self):
        self.documents = []
        self.doc_texts = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.amz_map = {}
        
    def load_and_index(self, csv_fb=CSV_FB_PATH, xlsx_prio=XLSX_PRIO_PATH):
        print(f"[*] Bắt đầu khởi tạo hệ thống RAG đa kênh...")
        self.documents = []
        self.doc_texts = []
        self.amz_map = {}
        
        # 1. Nạp và lập bản đồ Priority List (Website & Amazon)
        if os.path.exists(xlsx_prio):
            print(f"[*] Đang đọc danh sách ưu tiên thẩm định: {xlsx_prio}")
            prio_df = pd.read_excel(xlsx_prio)
            for idx, r in prio_df.iterrows():
                bname = str(r['Breeder Name']).strip()
                bname_l = bname.lower()
                if any(re.search(p, bname_l) for p in NON_CUSTOMER_PATTERNS):
                    continue
                web = str(r['Website']) if pd.notna(r['Website']) else ''
                fb_url = str(r['Facebook URL']) if pd.notna(r['Facebook URL']) else ''
                amz_link = str(r['Amazon Link']) if pd.notna(r['Amazon Link']) else ''
                amz_cat = str(r['Phân loại Amazon']) if pd.notna(r['Phân loại Amazon']) else 'Amazon link not found'
                rating = float(r['Rating']) if pd.notna(r['Rating']) else 0.0
                reviews = int(r['Review']) if pd.notna(r['Review']) else 0
                phone = str(r['Phone']) if pd.notna(r['Phone']) else ''
                email = str(r['Email']) if pd.notna(r['Email']) else ''
                city = str(r['City']) if pd.notna(r['City']) else ''
                state = str(r['Bang/State']) if pd.notna(r['Bang/State']) else ''
                
                entry = {
                    'bname': bname,
                    'website': web,
                    'fb_url': fb_url,
                    'amz_link': amz_link,
                    'amz_cat': amz_cat,
                    'rating': rating,
                    'reviews': reviews,
                    'phone': phone,
                    'email': email,
                    'location': f"{city}, {state}".strip(", ")
                }
                
                for u in fb_url.split(';'):
                    u_c = u.strip().lower().rstrip('/')
                    if 'facebook.com' in u_c:
                        self.amz_map[u_c] = entry
                self.amz_map['name:' + bname.lower()] = entry
                
                # Chấm điểm Priority List lead
                recency_score = 30
                icp_score = 30
                breed_matches = [b for b in HIGH_VALUE_BREEDS if b in bname_l]
                breed_score = 15 if len(breed_matches) >= 2 else (10 if len(breed_matches) == 1 else 5)
                web_score = 5 + (5 if reviews >= 10 else 2)
                
                amz_score = 0
                if 'Selling pet toys + Artificial grass' in amz_cat:
                    amz_score = 15
                elif 'Selling artificial grass' in amz_cat:
                    amz_score = 10
                elif 'Selling pet toys' in amz_cat:
                    amz_score = 7
                elif 'target sales' in amz_cat:
                    amz_score = 3
                    
                total_score = min(100, recency_score + icp_score + breed_score + web_score + amz_score)
                rank_tier = 'Tier S' if total_score >= 85 else ('Tier A' if total_score >= 70 else ('Tier B' if total_score >= 50 else 'Tier C'))
                
                doc = {
                    'stt': f"PRIO-{idx+1}",
                    'name': bname,
                    'url': fb_url.split(';')[0].strip() if fb_url else web,
                    'website': web,
                    'pub_time': 'Đã thẩm định website',
                    'rel_time': 'Đang hoạt động',
                    'recency_tier': 'Hot (Xác minh)',
                    'recency_code': 'hot',
                    'business_type': 'Dog Breeder / Commercial Kennel',
                    'type_code': 'breeder',
                    'product_fit': 'Puppy Kit V3 (Cỏ + Potty + Đồ chơi)',
                    'amz_cat': amz_cat,
                    'amz_link': amz_link,
                    'score': total_score,
                    'lead_tier': rank_tier,
                    'is_prio': True,
                    'phone': phone,
                    'email': email,
                    'location': entry['location']
                }
                self.documents.append(doc)
                self.doc_texts.append(f"{bname} Dog Breeder Puppy Kit {amz_cat} {entry['location']}")
                
        # 2. Nạp và xử lý tập dữ liệu Facebook Scraped
        total_fb = 0
        excluded_fb = 0
        if os.path.exists(csv_fb):
            print(f"[*] Đang đọc dữ liệu Facebook cào: {csv_fb}")
            with open(csv_fb, mode='r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                next(reader, None)
                for r in reader:
                    if len(r) < 6:
                        continue
                    total_fb += 1
                    stt, url, name, pub_time, ts, rel = r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip(), r[5].strip()
                    name_l = name.lower()
                    
                    if any(re.search(p, name_l) for p in NON_CUSTOMER_PATTERNS):
                        excluded_fb += 1
                        continue
                        
                    u_clean = url.lower().rstrip('/')
                    n_clean = 'name:' + name_l
                    prio_info = self.amz_map.get(u_clean) or self.amz_map.get(n_clean)
                    
                    # 1. Recency
                    rel_l = rel.lower()
                    if any(x in rel_l for x in ['phút', 'vừa xong']) or ('1 giờ' in rel_l) or ('2 giờ' in rel_l) or ('3 giờ' in rel_l):
                        recency_score = 35
                        rec_tier = 'Hot (≤ 3 giờ)'
                        rec_code = 'hot'
                    elif any(f'{h} giờ' in rel_l for h in range(4, 25)):
                        recency_score = 32
                        rec_tier = 'Hot (4 - 24 giờ)'
                        rec_code = 'hot'
                    elif any(x in rel_l for x in ['1 ngày', '2 ngày', '3 ngày']):
                        recency_score = 28
                        rec_tier = 'Hot (1 - 3 ngày)'
                        rec_code = 'hot'
                    elif any(f'{d} ngày' in rel_l for d in range(4, 8)) or ('1 tuần' in rel_l):
                        recency_score = 20
                        rec_tier = 'Warm (4 - 7 ngày)'
                        rec_code = 'warm'
                    elif any(f'{d} ngày' in rel_l for d in range(8, 15)) or ('2 tuần' in rel_l):
                        recency_score = 15
                        rec_tier = 'Warm (8 - 14 ngày)'
                        rec_code = 'warm'
                    elif any(f'{d} ngày' in rel_l for d in range(15, 31)) or ('3 tuần' in rel_l) or ('4 tuần' in rel_l) or ('1 tháng' in rel_l):
                        recency_score = 8
                        rec_tier = 'Cool (15 - 30 ngày)'
                        rec_code = 'cool'
                    else:
                        recency_score = 0
                        rec_tier = 'Cold (> 30 ngày)'
                        rec_code = 'cold'
                        
                    # 2. Category
                    if any(k in name_l for k in BREEDER_KEYWORDS):
                        icp_score = 28
                        business_type = 'Dog Breeder / Kennel'
                        type_code = 'breeder'
                        product_fit = 'Puppy Kit (Cỏ + Potty + Đồ chơi)'
                    elif any(k in name_l for k in SERVICE_KEYWORDS):
                        icp_score = 20
                        business_type = 'Pet Care & Training'
                        type_code = 'service'
                        product_fit = 'Cỏ nhân tạo sân chơi / Đồ chơi K9'
                    elif any(k in name_l for k in RESCUE_KEYWORDS):
                        icp_score = 14
                        business_type = 'Pet Rescue / Shelter'
                        type_code = 'rescue'
                        product_fit = 'Tã lót Pee Pad / Đồ chơi xoa dịu'
                    else:
                        icp_score = 10
                        business_type = 'Pet Community / Owner'
                        type_code = 'individual'
                        product_fit = 'Khay vệ sinh căn hộ / Đồ chơi'
                        
                    # 3. High value breed
                    breed_matches = [b for b in HIGH_VALUE_BREEDS if b in name_l]
                    if len(breed_matches) >= 2:
                        breed_score = 15
                    elif len(breed_matches) == 1:
                        breed_score = 10
                    elif any(k in name_l for k in ['puppy', 'puppies', 'kennel', 'farm']):
                        breed_score = 5
                    else:
                        breed_score = 0
                        
                    # 4. Web & infrastructure
                    web_score = (5 if prio_info and prio_info.get('website') else 0) + (5 if any(w in name_l for w in ['farm', 'kennel', 'llc', 'ltd']) else 0)
                    
                    # 5. Amazon
                    amz_score = 0
                    amz_cat = 'Amazon link not found'
                    amz_link = ''
                    if prio_info:
                        amz_cat = prio_info['amz_cat']
                        amz_link = prio_info['amz_link']
                        if 'Selling pet toys + Artificial grass' in amz_cat:
                            amz_score = 15
                        elif 'Selling artificial grass' in amz_cat:
                            amz_score = 10
                        elif 'Selling pet toys' in amz_cat:
                            amz_score = 7
                        elif 'target sales' in amz_cat:
                            amz_score = 3
                            
                    total_score = min(100, recency_score + icp_score + breed_score + web_score + amz_score)
                    rank_tier = 'Tier S' if total_score >= 80 else ('Tier A' if total_score >= 65 else ('Tier B' if total_score >= 50 else ('Tier C' if total_score >= 30 else 'Tier D')))
                    
                    doc = {
                        'stt': stt,
                        'name': name,
                        'url': url,
                        'website': prio_info.get('website', '') if prio_info else '',
                        'pub_time': pub_time,
                        'rel_time': rel,
                        'recency_tier': rec_tier,
                        'recency_code': rec_code,
                        'business_type': business_type,
                        'type_code': type_code,
                        'product_fit': product_fit,
                        'amz_cat': amz_cat,
                        'amz_link': amz_link,
                        'score': total_score,
                        'lead_tier': rank_tier,
                        'is_prio': bool(prio_info),
                        'phone': prio_info.get('phone', '') if prio_info else '',
                        'email': prio_info.get('email', '') if prio_info else '',
                        'location': prio_info.get('location', '') if prio_info else ''
                    }
                    self.documents.append(doc)
                    self.doc_texts.append(f"{name} {business_type} {product_fit} {amz_cat} {rec_tier}")

        print(f"[✓] Tổng số khách hàng trong cơ sở dữ liệu RAG: {len(self.documents)}")
        print(f"[!] Đã lọc bỏ {excluded_fb} đơn vị phi mục tiêu (AKC, UKC, PetSmart, Tin tức, Meme)")
        
        # Xây dựng TF-IDF Vector Space
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)
        print("[✓] Đã lập chỉ mục Vector TF-IDF thành công!")

    def query(self, query_text, top_k=10, filter_type=None, filter_recency=None, filter_amazon=False):
        """
        Truy vấn Vector kết hợp bộ lọc đa tiêu chí
        """
        if not self.vectorizer or self.tfidf_matrix is None:
            raise ValueError("Hệ thống RAG chưa được nạp. Hãy gọi load_and_index() trước.")
            
        q_vec = self.vectorizer.transform([query_text])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        ranked_indices = np.argsort(-sims)
        
        results = []
        for idx in ranked_indices:
            doc = self.documents[idx]
            sim_score = float(sims[idx])
            
            if filter_type and doc['type_code'] != filter_type:
                continue
            if filter_recency and doc['recency_code'] != filter_recency:
                continue
            if filter_amazon and doc['amz_cat'] == 'Amazon link not found':
                continue
                
            results.append({
                **doc,
                'similarity': round(sim_score, 4)
            })
            
            if len(results) >= top_k:
                break
                
        return results

if __name__ == "__main__":
    rag = UnifiedLeadRAGSystem()
    rag.load_and_index()
    
    print("\n=== KIỂM TRA TRUY VẤN RAG ĐA TIÊU CHÍ (KÈM KÊNH AMAZON) ===")
    queries = [
        "French bulldog puppy take home kit with Amazon store",
        "Golden retriever breeder grass pee pad toilet",
        "Dog training academy artificial turf field"
    ]
    
    for q in queries:
        print(f"\n[QUERY]: '{q}'")
        res = rag.query(q, top_k=4)
        for r in res:
            amz_tag = f" | AMZ: {r['amz_cat']}" if r['amz_cat'] != 'Amazon link not found' else ""
            print(f"  -> [{r['score']}đ - {r['lead_tier']}] {r['name']} ({r['business_type']}) | {r['rel_time']}{amz_tag}")
