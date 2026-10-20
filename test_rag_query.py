import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

master_excel = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx"
df = pd.read_excel(master_excel, sheet_name="US_Hot_Leads_Cap_A_61d")
print(f"[*] Nạp RAG với {len(df)} Hot Leads Cấp A từ Master File...")

texts = []
for _, r in df.iterrows():
    name = str(r["Breeder_Name"])
    breeds = str(r["Breeds_Identified"])
    state = str(r["State"]) if pd.notna(r["State"]) else ""
    city = str(r["City"]) if pd.notna(r["City"]) else ""
    prod = str(r["Target_Products"])
    act = str(r["Sales_Action"])
    text = f"{name} {breeds} {city} {state} {prod} {act}"
    texts.append(text)

vec = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
matrix = vec.fit_transform(texts)

queries = [
    "Frenchies and Bernedoodle puppies take home kit Seattle",
    "Dog training turf grass pee pad Florida",
    "Rottweiler kennel puppy starter kit"
]

for q in queries:
    print(f"\n[RAG SEARCH]: '{q}'")
    qv = vec.transform([q])
    sims = cosine_similarity(qv, matrix).flatten()
    top_i = np.argsort(-sims)[:3]
    for i in top_i:
        r = df.iloc[i]
        phone = r["Phone"] if pd.notna(r["Phone"]) else "Chưa có SĐT"
        print(f"  -> ({sims[i]:.2f}) [{r['Total_Lead_Score']}đ | {r['Tier_Rank'][:6]}] {r['Breeder_Name']} ({r['State']}) | Phone: {phone} | Kit: {str(r['Target_Products'])[:40]}...")
