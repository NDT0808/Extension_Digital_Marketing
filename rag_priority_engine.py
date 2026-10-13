import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

EXCEL_PATH = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\priority_list_2026-10-06_v2.xlsx"

class PriorityListRAG:
    def __init__(self, excel_path=EXCEL_PATH):
        self.excel_path = excel_path
        self.df = pd.read_excel(excel_path)
        self.documents = []
        self.doc_texts = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._build_index()
        
    def _build_index(self):
        for idx, row in self.df.iterrows():
            name = str(row.get('Breeder Name', '')).strip()
            web = str(row.get('Website', '')).strip()
            state = str(row.get('Bang/State', '')).strip()
            city = str(row.get('City', '')).strip()
            email = str(row.get('Email', '')).strip()
            phone = str(row.get('Phone', '')).strip()
            amz_link = str(row.get('Amazon Link', '')).strip()
            amz_class = str(row.get('Phân loại Amazon', 'Amazon link not found')).strip()
            has_amz = amz_class != 'Amazon link not found' and amz_link not in ['nan', 'None', '']
            
            score = row.get('Lead Score (marketing_parameter.html)', 0)
            tier = str(row.get('Phân Cấp Khách Hàng (Tier A/B/C/D)', 'B级 (Quy mô trung bình / Tiềm năng)'))
            sales_action = str(row.get('Hành Động Đội Sales (Sales Action)', ''))
            
            doc = {
                'row_no': row.get('NO', idx + 1),
                'master_id': row.get('Master ID', ''),
                'name': name,
                'country': 'United States',
                'state': state,
                'city': city,
                'website': web,
                'email': email,
                'phone': phone,
                'amazon_link': None if amz_link in ['nan', 'None', ''] else amz_link,
                'amazon_classification': amz_class,
                'has_amazon': has_amz,
                'lead_score': int(score) if pd.notna(score) else 0,
                'rank_tier': tier,
                'sales_action': sales_action,
                'rating': row.get('Rating', 0),
                'review': row.get('Review', 0),
            }
            
            # Text chunk for semantic vector search
            text_chunk = f"{name} United States USA {state} {city} {web} {amz_class} {tier} score:{score} {'has amazon seller storefront' if has_amz else 'no amazon'}"
            self.documents.append(doc)
            self.doc_texts.append(text_chunk)
            
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)
        
    def query(self, query_text, top_k=10, only_amazon=False, min_score=None, only_us=True):
        q_vec = self.vectorizer.transform([query_text])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        ranked = np.argsort(-sims)
        
        results = []
        for idx in ranked:
            doc = self.documents[idx]
            if only_us and doc.get('country') != 'United States':
                continue
            if only_amazon and not doc['has_amazon']:
                continue
            if min_score and doc['lead_score'] < min_score:
                continue
            results.append({
                **doc,
                'similarity': round(float(sims[idx]), 4)
            })
            if len(results) >= top_k:
                break
        return results

    def get_amazon_sellers(self):
        return [d for d in self.documents if d['has_amazon'] or d['amazon_classification'] != 'Amazon link not found']

    def get_summary_statistics(self):
        total = len(self.documents)
        amz_rows = self.get_amazon_sellers()
        
        class_counts = {}
        tier_counts = {}
        for d in self.documents:
            c = d['amazon_classification']
            class_counts[c] = class_counts.get(c, 0) + 1
            t = d['rank_tier']
            tier_counts[t] = tier_counts.get(t, 0) + 1
            
        return {
            'total_websites': total,
            'websites_with_amazon': len(amz_rows),
            'pct_with_amazon': round(len(amz_rows) / total * 100, 2),
            'classifications': class_counts,
            'tier_distribution': tier_counts
        }

if __name__ == "__main__":
    rag = PriorityListRAG()
    stats = rag.get_summary_statistics()
    print("=== TỔNG KẾT RAG: HỆ THỐNG THÔNG TIN KHÁCH HÀNG & KÊNH AMAZON ===")
    print(f"Tổng số website trong danh sách trích xuất: {stats['total_websites']}")
    print(f"Số website CÓ BÁN HÀNG TRÊN AMAZON: {stats['websites_with_amazon']} ({stats['pct_with_amazon']}%)")
    print("\nPhân loại Amazon chi tiết:")
    for k, v in stats['classifications'].items():
        print(f" - {k}: {v}")
    print("\nPhân bổ Cấp bậc marketing_parameter.html:")
    for k, v in stats['tier_distribution'].items():
        print(f" - {k}: {v}")
        
    print("\n=== TOP CÁC KHÁCH HÀNG TIỀM NĂNG CÓ GIAN HÀNG AMAZON ===")
    sellers = rag.get_amazon_sellers()
    for s in sellers:
        print(f"[{s['lead_score']}đ | {s['rank_tier'][:2]}] #{s['row_no']} {s['name']} ({s['state']}) | {s['amazon_classification']} | {s['amazon_link']}")
