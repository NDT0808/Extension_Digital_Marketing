import re
import json
from collections import Counter
from datetime import datetime

HTML_FILE = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Bao_Cao_Phan_Tich_Leads_Pet_Grass_Potty_Toys_2026.html"
OUT_JSON = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Bao_Cao_Phan_Tich_Leads_Pet_Grass_Potty_Toys_2026.json"

print(f"Reading {HTML_FILE}...")
with open(HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Extract rawLeads
m_leads = re.search(r'const rawLeads\s*=\s*(\[.*?\]);', html, re.DOTALL)
if not m_leads:
    raise ValueError("Cannot find rawLeads array in HTML!")

leads = json.loads(m_leads.group(1))
print(f"Extracted {len(leads):,} leads.")

# 2. Extract i18n dictionary if present
m_i18n = re.search(r'const i18n\s*=\s*(\{.*?\n\s*\});', html, re.DOTALL)
i18n_dict = {}
if m_i18n:
    try:
        # Note: JS object might need minor fixing if keys aren't quoted, but here they are quoted JSON-like
        raw_i18n_str = m_i18n.group(1)
        i18n_dict = json.loads(raw_i18n_str)
        print("Extracted i18n dictionary successfully.")
    except Exception as e:
        print(f"Could not directly json.loads i18n: {e}")

# 3. Extract Regional Hubs
m_hubs = re.search(r'regionalHubs\s*=\s*(\[.*?\]);', html, re.DOTALL)
regional_hubs = []
if m_hubs:
    try:
        # In JS: { id: 'pnw', nameVi: ... } -> keys might not be double-quoted.
        # We can extract with regex or eval/node
        hubs_raw = m_hubs.group(1)
        # Convert JS object keys to double quotes
        hubs_fixed = re.sub(r'(\b[a-zA-Z0-9_]+\b)\s*:', r'"\1":', hubs_raw)
        hubs_fixed = hubs_fixed.replace("'", '"')
        regional_hubs = json.loads(hubs_fixed)
        print(f"Extracted {len(regional_hubs)} regional weather hubs.")
    except Exception as e:
        print(f"Hubs regex parsing fallback: {e}")

# 4. Extract Chart datasets from script
chart_data = {
    "tier_distribution": {
        "description": "Phân bổ phân hạng tiềm năng (Tier S, A, B, C, D)",
        "labels": ["Tier S (85-100)", "Tier A (70-84)", "Tier B (50-69)", "Tier C (30-49)", "Tier D (<30)"],
        "values": [102, 3025, 197, 872, 2134],
        "colors": ["#f59e0b", "#6366f1", "#10b981", "#94a3b8", "#f43f5e"]
    },
    "amazon_distribution": {
        "description": "Phân bổ độ phủ & kiểm toán kênh Amazon US",
        "labels": ["TARGET Kép (Cỏ + Đồ chơi)", "Cỏ / Potty TARGET", "Đồ chơi TARGET", "Amazon khác", "Chưa có Amz"],
        "values": [13, 9, 3, 1, 3298],
        "colors": ["#f59e0b", "#10b981", "#6366f1", "#06b6d4", "#475569"]
    },
    "recency_distribution": {
        "description": "Phân bổ thời gian đăng bài / cập nhật gần nhất trên Mạng xã hội",
        "labels": ["Hot (≤ 3 ngày)", "Warm (4-14 ngày)", "Cool (15-30 ngày)", "Cold (> 30 ngày)"],
        "values": [2898, 1043, 480, 1577],
        "colors": ["#f59e0b", "#10b981", "#06b6d4", "#475569"]
    },
    "category_distribution": {
        "description": "Phân bổ theo loại hình tổ chức / ICP Fit",
        "labels": ["Dog Breeder / Commercial Kennel", "Pet Care & Training", "Pet Rescue / Shelter", "Cá nhân / Community"],
        "values": [3242, 45, 37, 0],
        "colors": ["#10b981", "#6366f1", "#06b6d4", "#475569"]
    }
}

# 5. Calculate live statistics across all 3,324 leads
tier_counts = Counter(l.get("rank_tier", "") for l in leads)
cat_counts = Counter(l.get("cat", "") for l in leads)
amz_cat_counts = Counter(l.get("amz_cat", "") for l in leads)
prod_fit_counts = Counter(l.get("product_fit", "") for l in leads)
state_counts = Counter(l.get("state", "Unknown") or "Unknown" for l in leads)
action_counts = Counter(l.get("sales_action", "") for l in leads)

scores = [l.get("score", 0) for l in leads if isinstance(l.get("score"), (int, float))]
has_phone_count = sum(1 for l in leads if l.get("phone"))
has_email_count = sum(1 for l in leads if l.get("email"))
has_website_count = sum(1 for l in leads if l.get("website"))
has_fb_url_count = sum(1 for l in leads if l.get("url"))
has_amz_link_count = sum(1 for l in leads if l.get("amz_link"))

leads_summary_stats = {
    "total_leads_in_dataset": len(leads),
    "contact_coverage": {
        "has_phone": has_phone_count,
        "has_phone_rate": round(has_phone_count / len(leads) * 100, 2),
        "has_email": has_email_count,
        "has_email_rate": round(has_email_count / len(leads) * 100, 2),
        "has_website": has_website_count,
        "has_website_rate": round(has_website_count / len(leads) * 100, 2),
        "has_facebook": has_fb_url_count,
        "has_amazon_store": has_amz_link_count
    },
    "score_metrics": {
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0
    },
    "tier_breakdown": dict(tier_counts.most_common()),
    "category_breakdown": dict(cat_counts.most_common()),
    "amazon_category_breakdown": dict(amz_cat_counts.most_common()),
    "product_fit_breakdown": dict(prod_fit_counts.most_common()),
    "top_states": dict(state_counts.most_common(20)),
    "sales_action_breakdown": dict(action_counts.most_common())
}

# 6. Build the comprehensive JSON master structure
master_json = {
    "report_info": {
        "report_id": "PET_GRASS_POTTY_TOYS_US_2026",
        "title_vi": "Báo Cáo Phân Tích Leads & Sàn Amazon Thị Trường Mỹ 2026",
        "title_zh": "美国本土狗舍潜客与亚马逊渠道营销分析报告",
        "system_badge": "⚡ 美国本土市场专案 - RAG智能向量检索与CRM潜客系统 (Pet & Grass Lead Intelligence CRM)",
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_files": [
            "Bao_Cao_Phan_Tich_Leads_Pet_Grass_Potty_Toys_2026.html",
            "Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx",
            "marketing_parameter.html"
        ],
        "target_market": "United States (100% Nội địa Hoa Kỳ)",
        "core_products": [
            "Cỏ nhân tạo thú cưng (Pet Artificial Grass / Drainage Turf)",
            "Nhà vệ sinh / Khay vệ sinh thú cưng (Pet Potty / Pee Pad Trays)",
            "Đồ chơi cún con / Bộ quà tặng xuất chuồng (Chew Toys / Snuggle Puppies / Puppy Take-Home Starter Kit V2/V3)"
        ]
    },
    "strategic_overview": {
        "vi": {
            "strategy": "Chiến lược Giai đoạn 1: Tập trung 100% thị phần nội địa Hoa Kỳ (United States) với 3.324 Khách Hàng Tiềm Năng Cấp A (Score ≥ 61) chọn lọc từ 14.138 hồ sơ làm sạch. Hệ thống chấm điểm chuẩn theo marketing_parameter.html kết hợp rà soát uy tín gian hàng Amazon US & Tích hợp Radar Thời Tiết Real-Time (OpenWeatherMap API).",
            "scoring_rules": "Điểm tổng hợp = Điểm thông tin cơ bản (Website + Trang bán hàng + Form đăng ký + >10 đánh giá + Đa giống cún) + Điểm sàn Amazon (+15 điểm dual-target) + Điểm hành vi người dùng trên website."
        },
        "zh": {
            "strategy": "第一阶段战略重点：100% 聚焦美国本土市场（United States）。基于 14,138 条清洗线索中严格筛选出的 3,324 条高净值重点潜客（Class A Hot Leads / 分数 ≥ 61）。严格执行 marketing_parameter.html 评分标准，深度集成亚马逊店铺背书，并集成 OpenWeatherMap 全美实时气象雷达。",
            "scoring_rules": "综合评分 = 基础资料 (官网 + 销售页 + 申请表 + 10+评价 + 多犬种) + 亚马逊背书 (+15分 双目标) + 网站浏览行为。"
        }
    },
    "executive_kpis": {
        "total_us_cleaned_leads": 14138,
        "core_profiles_count": 6330,
        "excluded_non_commercial": 3745,
        "commercial_dog_breeders_b2b": 3242,
        "amazon_verified_shops": 26,
        "amazon_dual_target_shops": 13,
        "high_priority_class_a_leads": 3324
    },
    "visual_charts_data": chart_data,
    "leads_summary_statistics": leads_summary_stats,
    "regional_weather_radar_hubs": regional_hubs if regional_hubs else [
        {
            "id": "pnw",
            "name_vi": "Tây Bắc Thái Bình Dương (PNW)",
            "name_zh": "太平洋西北 (WA / OR)",
            "benchmark_city": "Seattle, WA",
            "zip": "98101",
            "default_temp_f": 48,
            "weather_condition": "Rain",
            "sales_trigger_vi": "🌧️ Mưa ẩm triền miên -> Cún ngại ướt chân -> Chốt Cỏ nhân tạo & Khay Potty thoát nước",
            "sales_trigger_zh": "🌧️ 多雨泥泞：力推快排水人造草垫与室内幼犬便盆托盘"
        },
        {
            "id": "midwest",
            "name_vi": "Vùng Trung Tây & Tuyết Rơi",
            "name_zh": "中西部大湖区 (IL / MN / OH)",
            "benchmark_city": "Chicago, IL",
            "zip": "60601",
            "default_temp_f": 32,
            "weather_condition": "Snow",
            "sales_trigger_vi": "❄️ Bão tuyết cấm ra ngoài -> Chốt combo Cỏ + Đồ chơi gặm xoa dịu stress",
            "sales_trigger_zh": "❄️ 严寒暴雪：足不出户排泄，力推防拆益智玩具+室内草坪"
        },
        {
            "id": "east",
            "name_vi": "Bờ Đông & Đô Thị Lớn",
            "name_zh": "东部走廊 (NY / PA / VA)",
            "benchmark_city": "New York, NY",
            "zip": "10001",
            "default_temp_f": 55,
            "weather_condition": "Clouds",
            "sales_trigger_vi": "🏢 Chung cư/Nhà phố hẹp -> Chốt Starter Kit tiện lợi",
            "sales_trigger_zh": "🏢 紧凑公寓生活：极度需要防臭抗菌宠物草坪与便垫"
        },
        {
            "id": "sunbelt",
            "name_vi": "Bờ Nam & Bờ Tây Nắng Nóng",
            "name_zh": "阳光带与西岸 (CA / TX / FL)",
            "benchmark_city": "San Diego, CA",
            "zip": "92114",
            "default_temp_f": 78,
            "weather_condition": "Clear",
            "sales_trigger_vi": "☀️ Sốc nhiệt trưa hè -> Chốt Thảm cỏ râm mát + Đồ chơi cấp nước",
            "sales_trigger_zh": "☀️ 酷暑路面烫脚：力推遮阳抗UV草垫与耐咬洁齿玩具"
        }
    ],
    "sales_playbook_tactics": [
        {
            "id": "opening_pitch",
            "name_vi": "Câu mở đầu tiếp cận chuẩn mực (Cold Call / Email)",
            "name_zh": "经典销售切入话术（邮件 & 电话沟通）",
            "script_en": "Do you currently provide a puppy take-home package for your buyers?",
            "script_vi": "Bên anh/chị hiện tại khi bàn giao cún cưng cho khách hàng có chuẩn bị sẵn Gói quà xuất chuồng Take-Home Kit không ạ?",
            "script_zh": "请问贵犬舍目前在幼犬交付时，是否会为买家准备幼犬回家大礼包 Take-Home Kit ？",
            "note_vi": "Đối với trại đã có shop Amazon: Đề xuất phương án OEM/sỉ in logo thương hiệu độc quyền của trại, giúp giảm chi phí mua lẻ.",
            "note_zh": "针对已拥有亚马逊店铺的客户：直接切入定制化批发方案，强调犬舍专属 Logo 印刷与打包成本优势。"
        },
        {
            "id": "amazon_channel_strategy",
            "name_vi": "Chiến lược tiến công theo phân loại gian hàng Amazon",
            "name_zh": "基于亚马逊渠道的品类进攻策略",
            "points_vi": [
                "Trại đã bán Cỏ / Potty: Giới thiệu cỏ thoát nước chống cắn xé + khay lót chuồng, chiết khấu BOM số lượng lớn.",
                "Trại đã bán Đồ chơi: Giới thiệu Đồ chơi nhịp tim xoa dịu lo âu (Snuggle Puppy) + combo đồ chơi gặm mọc răng.",
                "Trại chưa có kênh TMĐT: Cung cấp giải pháp đóng gói trọn gói Take-Home Kit tăng 15-20% giá trị thương hiệu cho trại."
            ],
            "points_zh": [
                "已推荐草坪/便盆的犬舍：重点推荐快排水、防咬抗撕裂人造草垫与室内幼犬托盘，出示批量订购 BOM 折扣。",
                "已推荐玩具的犬舍：引入安抚幼犬心跳玩具（Snuggle Puppy 同类）与出牙咀嚼玩具包，切入幼犬回家场景。",
                "尚未建立电商渠道的犬舍：提供开箱即用的 Take-Home Starter Kit 现成打包方案，赋能犬舍品牌溢价提升 15-20%。"
            ]
        },
        {
            "id": "weather_contextual_marketing",
            "name_vi": "Đòn bẩy tiếp thị theo ngữ cảnh thời tiết OpenWeatherMap",
            "name_zh": "基于 OpenWeatherMap 天气预报的情境营销杠杆",
            "points_vi": [
                "Thời tiết cực đoan/bão tuyết/nắng gắt (>90°F hoặc <40°F): Cún không thể ra ngoài vệ sinh -> Kích hoạt Cỏ nhân tạo thoát nước + khay lót vệ sinh trong nhà.",
                "Cún bị nhốt lâu trong nhà: Dễ bị căng thẳng và cắn phá đồ đạc -> Chốt Đồ chơi nhịp tim và Đồ chơi gặm bền bỉ.",
                "Định giá linh hoạt & gói cứu trợ khẩn cấp: Thời điểm bão tuyết hoặc mưa dầm, chào bán combo Starter Kit khẩn cấp nâng giá trị đơn hàng AOV lên 20-30%."
            ],
            "points_zh": [
                "恶劣天气/暴雪/酷暑（>90°F / <40°F）：幼犬无法出门排泄，极易受凉中暑 -> 即时触发室内排水人造草垫与专用便盆托盘。",
                "长时间闭门室内：幼犬精力无处释放引发拆家焦虑 -> 精准推送安抚心跳玩具与高耐咬益智磨牙玩具。",
                "动态定价与急迫性捆绑：恶劣天气警报期，力推应急 Starter Kit 礼包，客单价（AOV）可提升 20-30% 且成交率显著提升。"
            ]
        }
    ],
    "i18n_dictionary": i18n_dict,
    "leads_count": len(leads),
    "leads": leads
}

print(f"Writing complete JSON to {OUT_JSON}...")
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(master_json, f, ensure_ascii=False, indent=2)

print("SUCCESS! File size:", f"{len(json.dumps(master_json, ensure_ascii=False)) / 1024 / 1024:.2f} MB")
