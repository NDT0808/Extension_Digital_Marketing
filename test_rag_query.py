import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

excel_path = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Datasets\Thong_Ke_Leads_FB_PublishTime_2026.xlsx"
df = pd.read_excel(excel_path, sheet_name="Tier_S_A_Hot_Leads_US")
print(f"[*] Nạp RAG với {len(df)} Hot Leads B2B US từ file thống kê chuẩn...")

doc_texts = []
docs = []
for idx, r in df.iterrows():
    name = str(r["Tên"])
    icp = str(r["Phân Loại ICP"])
    details = str(r["Chi Tiết Phân Loại"])
    prod = str(r["Sản Phẩm Mục Tiêu"])
    city = str(r["Thành Phố"]) if pd.notna(r["Thành Phố"]) else ""
    state = str(r["Bang / State"]) if pd.notna(r["Bang / State"]) else ""
    score = r["Total_Score"]
    tier = r["Phân Hạng (Tier)"]
    phone = str(r["Điện Thoại"]) if pd.notna(r["Điện Thoại"]) else "N/A"
    action = str(r["Hành Động Đội Sales"])
    
    text = f"{name} {icp} {details} {prod} {city} {state} {tier} {action}"
    doc_texts.append(text)
    docs.append({
        "name": name, "icp": icp, "score": score, "tier": tier,
        "prod": prod, "phone": phone, "action": action, "location": f"{city}, {state}".strip(", ")
    })

vec = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
tfidf = vec.fit_transform(doc_texts)

queries = [
    "French bulldog breeder take home kit puppy",
    "Golden retriever grass pee pad potty training",
    "Dog training academy artificial turf lawn field"
]

for q in queries:
    print(f"\n[RAG QUERY]: '{q}'")
    q_v = vec.transform([q])
    sims = cosine_similarity(q_v, tfidf).flatten()
    top_idx = np.argsort(-sims)[:3]
    for i in top_idx:
        d = docs[i]
        sim = sims[i]
        print(f"  -> ({sim:.2f}) [{d['score']}đ | {d['tier']}] {d['name']} | Phone: {d['phone']} | {d['prod'][:45]}...")
