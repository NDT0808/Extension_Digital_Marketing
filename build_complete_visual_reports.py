import openpyxl, json, re, os

print("Starting generation of comprehensive visual dashboards with per-user details...")

# 1. Load Master Excel
wb = openpyxl.load_workbook('Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx', read_only=True)
ws = wb['US_Hot_Leads_Cap_A_61d']
rows = list(ws.iter_rows(values_only=True))
headers = rows[0]
print(f"Loaded {len(rows)-1} rows from US_Hot_Leads_Cap_A_61d")
owner_col_in_master = headers.index('Owner_Representative') if 'Owner_Representative' in headers else -1

# 2. Load Extracted Owners from US_Hot_Leads_With_Owner_Representative.xlsx if present
owner_map = {}
if os.path.exists('US_Hot_Leads_With_Owner_Representative.xlsx'):
    wb_own = openpyxl.load_workbook('US_Hot_Leads_With_Owner_Representative.xlsx', data_only=True)
    ws_own = wb_own.active
    h_own = [c for c in next(ws_own.iter_rows(min_row=1, max_row=1, values_only=True))]
    o_idx = h_own.index('Owner_Representative') if 'Owner_Representative' in h_own else 28
    for r in ws_own.iter_rows(min_row=2, values_only=True):
        if r[0] and len(r) > o_idx and r[o_idx] and str(r[o_idx]).strip() != '' and 'Chưa' not in str(r[o_idx]):
            owner_map[str(r[0])] = str(r[o_idx])
    print(f"Loaded {len(owner_map)} pre-extracted owners from US_Hot_Leads_With_Owner_Representative.xlsx")

# Known person first names for heuristic
COMMON_FIRST_NAMES = {
    'jason', 'sarah', 'kristin', 'dapheney', 'holly', 'julian', 'nate', 'amy', 'sally', 'regina',
    'brian', 'josh', 'jeff', 'tasha', 'hannah', 'karen', 'craig', 'erin', 'jim', 'margie', 
    'melissa', 'emma', 'javin', 'tanya', 'curtis', 'patricia', 'daria', 'lori', 'abby', 'denise',
    'paula', 'sharon', 'dave', 'david', 'mark', 'lisa', 'john', 'mike', 'michael', 'chris',
    'amanda', 'steve', 'steven', 'tom', 'katie', 'jessica', 'ashley', 'brittany', 'rachel', 'laura',
    'megan', 'dan', 'daniel', 'kevin', 'eric', 'adam', 'justin', 'bob', 'robert', 'mary', 'james',
    'richard', 'charles', 'paul', 'anthony', 'trina', 'tim', 'pete', 'matt', 'matthew', 'sam',
    'samantha', 'alex', 'alexa', 'andrea', 'andrew', 'angela', 'anna', 'barbara', 'ben', 'benjamin',
    'bill', 'billy', 'brad', 'brandon', 'brenda', 'bruce', 'cameron', 'carl', 'carol', 'carolyn',
    'catherine', 'chad', 'charlotte', 'chelsea', 'chloe', 'cody', 'colin', 'connie', 'corey', 'cory',
    'crystal', 'cynthia', 'dale', 'dana', 'debbie', 'deborah', 'dennis', 'derek', 'diane', 'donald',
    'donna', 'dorothy', 'doug', 'douglas', 'dylan', 'eddie', 'edward', 'elizabeth', 'emily', 'frank',
    'gary', 'george', 'glen', 'glenn', 'gloria', 'grace', 'greg', 'gregory', 'heather', 'helen',
    'henry', 'ian', 'jack', 'jackson', 'jacob', 'jacqueline', 'jake', 'james', 'jamie', 'jane',
    'janet', 'janice', 'jared', 'jean', 'jeffrey', 'jennifer', 'jeremy', 'jerry', 'jesse', 'jill',
    'jimmy', 'joan', 'joanne', 'joe', 'joel', 'johnny', 'jon', 'jonathan', 'jordan', 'joseph',
    'joshua', 'joyce', 'judith', 'judy', 'julia', 'julie', 'justin', 'katelyn', 'katherine', 'kathleen',
    'kathryn', 'kathy', 'kayla', 'keith', 'kelly', 'kelsey', 'ken', 'kendra', 'kenneth', 'kerry',
    'kim', 'kimberly', 'kristen', 'kristina', 'kyle', 'lance', 'larry', 'leah', 'lee', 'leslie',
    'linda', 'lindsay', 'lindsey', 'logan', 'lori', 'louis', 'lucas', 'luke', 'lynn', 'madison',
    'mallory', 'marcus', 'margaret', 'maria', 'marian', 'marie', 'marilyn', 'marion', 'marissa',
    'martha', 'martin', 'marvin', 'mary', 'mason', 'maureen', 'max', 'megan', 'melanie', 'melissa',
    'meredith', 'micah', 'michele', 'michelle', 'mitchell', 'molly', 'monica', 'morgan', 'nancy',
    'natalie', 'nathan', 'nathaniel', 'neil', 'nicholas', 'nick', 'nicole', 'noah', 'norma', 'olivia',
    'paige', 'pam', 'pamela', 'pat', 'patricia', 'patrick', 'paul', 'paula', 'pauline', 'peggy',
    'perry', 'peter', 'philip', 'phillip', 'phyllis', 'priscilla', 'rachel', 'ralph', 'randall',
    'randy', 'ray', 'raymond', 'rebecca', 'rhonda', 'richard', 'rick', 'ricky', 'rita', 'rob',
    'robbie', 'robert', 'roberta', 'robin', 'rodney', 'roger', 'ron', 'ronald', 'ronnie', 'rose',
    'rosemary', 'ross', 'roxanne', 'roy', 'russell', 'ruth', 'ryan', 'sam', 'sammy', 'samuel',
    'sandra', 'sandy', 'sara', 'sarah', 'scott', 'sean', 'seth', 'shana', 'shane', 'shannon',
    'shari', 'sharon', 'shaun', 'shawna', 'sheila', 'shelby', 'shelly', 'sherri', 'sherry',
    'sheryl', 'shirley', 'sidney', 'sierra', 'sonia', 'sonya', 'spencer', 'stacey', 'stacy',
    'stanley', 'stephanie', 'stephen', 'steve', 'steven', 'sue', 'susan', 'suzanne', 'tamara',
    'tammy', 'tanya', 'tara', 'tasha', 'ted', 'teresa', 'terri', 'terry', 'theresa', 'thomas',
    'tiffany', 'tim', 'timothy', 'tina', 'todd', 'tom', 'tommy', 'tony', 'tracey', 'traci',
    'tracie', 'tracy', 'travis', 'trent', 'trevor', 'trina', 'tyler', 'valerie', 'vanessa',
    'vicki', 'vickie', 'vicky', 'victor', 'victoria', 'vincent', 'virginia', 'wade', 'walter',
    'wanda', 'warren', 'wayne', 'wendy', 'wesley', 'whitney', 'william', 'willie', 'zachary'
}

def resolve_owner(mid, name, email, url, cat='Dog Breeder'):
    if mid in owner_map and owner_map[mid]:
        return owner_map[mid]
        
    name_str = str(name or '')
    email_str = str(email or '').strip()
    url_str = str(url or '')
    
    # Priority specifics
    if 'Walnut Valley' in name_str: return 'Javin & David (Đồng sáng lập)'
    if 'NW Frenchies' in name_str: return 'Tanya Kharus (Chủ sở hữu)'
    if 'High Desert' in name_str: return 'Mama Bryner (Chủ trại)'
    if 'Suncrest' in name_str: return 'Lori Drew (Sáng lập)'
    if 'My Golden Guardians' in name_str: return 'Sarah (Chủ trại)'
    if 'Curlytail' in name_str: return 'Liana (Breeder chính)'
    if 'Golden Ticket' in name_str: return 'Golden Ticket Family (Đại diện)'
    if 'Daisey\'s Doodles' in name_str: return 'Trina Palosaari (Chủ sáng lập)'
    if 'Windsong' in name_str: return 'Windsong Team (Đại diện)'
    if 'Bark Avenue Dog' in name_str: return 'Bark Avenue Team (Quản lý)'
    if 'Seattle Humane' in name_str: return 'Shelter Operations Director'
    
    # 1. Look for 'Family' in name
    fam_m = re.search(r'([A-Z][a-z]+)\s+Family', name_str)
    if fam_m and fam_m.group(1).lower() not in {'happy', 'sweet', 'royal', 'first', 'great', 'our', 'my'}:
        return f'{fam_m.group(1)} Family (Đại diện gia đình)'
        
    # 2. Look for 'owners X and Y'
    m_own = re.search(r'(?:owners?|owned by|proprietor|breeder)\s+([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+|\s+[A-Z][a-z]+)?)', name_str, re.I)
    if m_own:
        return m_own.group(1).strip() + ' (Chủ sở hữu)'
        
    # 3. Look for 'Name - Dog Trainer / Kennels'
    m_hyphen = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-–—|]\s*(?:dog\s+trainer|kennels?|breeder|farms?|state\s+farm|pet)', name_str, re.I)
    if m_hyphen:
        return m_hyphen.group(1).strip() + ' (Chủ cơ sở)'
        
    # 4. Look for possessive 'X\'s Kennel/Farm/Dogs'
    m_pos = re.search(r'^([A-Z][a-z]+)\'s\s+(?:Kennels?|Farm|Dog|Puppies|Pups|Frenchies|Bulldogs?|Pet|Doodles)', name_str)
    if m_pos:
        first = m_pos.group(1)
        if first.lower() in COMMON_FIRST_NAMES:
            return f'{first} (Chủ sở hữu/Sáng lập)'
            
    # 5. Look inside Email
    if email_str and '@' in email_str:
        prefix = email_str.split('@')[0].lower().strip()
        if '.' in prefix:
            parts = prefix.split('.')
            if len(parts) == 2 and parts[0] in COMMON_FIRST_NAMES and len(parts[1]) > 2:
                return f'{parts[0].capitalize()} {parts[1].capitalize()} (Người đại diện email)'
        clean_p = re.sub(r'[\d._+-]+', '', prefix)
        if clean_p in COMMON_FIRST_NAMES:
            return f'{clean_p.capitalize()} (Đại diện phụ trách)'
            
    # 6. Look inside Facebook URL slug
    if 'facebook.com/' in url_str:
        slug = url_str.split('facebook.com/')[-1].split('/')[0].split('?')[0].lower()
        clean_s = re.sub(r'[\d._+-]+', '', slug)
        for fn in COMMON_FIRST_NAMES:
            if fn in clean_s and len(fn) >= 4 and not any(k in slug for k in ['french', 'bulldog', 'rescue', 'shelter', 'kennel', 'farm', 'doodle', 'puppy', 'hound']):
                return f'{fn.capitalize()} (Đại diện trang Facebook)'

    cat_lower = str(cat or '').lower()
    if 'rescue' in cat_lower or 'shelter' in cat_lower:
        return 'Giám đốc Tiếp nhận / Điều phối Cứu trợ (Shelter Intake Director)'
    elif 'care' in cat_lower or 'training' in cat_lower or 'service' in cat_lower:
        return 'Huấn luyện viên trưởng / Quản lý cơ sở (Head Trainer / Facility Director)'
    else:
        return 'Chủ trại / Quản lý chuồng trại (Breeder Owner / Kennel Manager)'

# Build rawLeads list
raw_leads = []
for r in rows[1:]:
    mid = str(r[0] or '')
    name = str(r[1] or '')
    web = str(r[2] or '')
    phone = str(r[3] or '')
    email = str(r[4] or '')
    fb = str(r[5] or '')
    addr = str(r[6] or '')
    city = str(r[7] or '')
    state = str(r[8] or '')
    zip_code = str(r[9] or '')
    country = str(r[10] or 'United States')
    cat = str(r[12] or 'Dog Breeder')
    amz_status = str(r[13] or 'Amazon link not found')
    amz_link = str(r[14] or '')
    score = int(r[21] or 70)
    tier_raw = str(r[22] or 'Tier A')
    prod = str(r[24] or 'Puppy Kit V3 (Cỏ + Potty + Đồ chơi)')
    action = str(r[25] or 'Telesale follow-up')
    
    tier = 'Tier A'
    if 'Tier S' in tier_raw or score >= 85: tier = 'Tier S'
    elif 'Tier B' in tier_raw and score < 70: tier = 'Tier B'
    elif 'Tier C' in tier_raw: tier = 'Tier C'
    elif 'Tier D' in tier_raw: tier = 'Tier D'
    
    owner = ''
    if mid in owner_map and owner_map[mid]:
        owner = owner_map[mid]
    elif owner_col_in_master != -1 and len(r) > owner_col_in_master and r[owner_col_in_master] and str(r[owner_col_in_master]).strip() != '':
        owner = str(r[owner_col_in_master])
    else:
        owner = resolve_owner(mid, name, email, fb or web, cat)
    
    cat_code = 'breeder'
    if 'Care' in cat or 'Training' in cat or 'Service' in cat:
        cat_code = 'service'
    elif 'Rescue' in cat or 'Shelter' in cat:
        cat_code = 'rescue'
    elif 'Owner' in cat or 'Community' in cat:
        cat_code = 'individual'

    raw_leads.append({
        'stt': mid,
        'name': name,
        'owner': owner,
        'url': fb or web,
        'website': web,
        'phone': phone,
        'email': email,
        'address': addr,
        'city': city,
        'state': state,
        'zip': zip_code,
        'country': country,
        'cat': cat,
        'cat_code': cat_code,
        'amz_cat': amz_status,
        'amz_link': amz_link,
        'product_fit': prod,
        'score': score,
        'rank_tier': tier,
        'is_prio': (score >= 85 or 'PRIO' in mid),
        'sales_action': action
    })

# Sort: Tier S first, then descending score
raw_leads.sort(key=lambda x: (0 if x['rank_tier'] == 'Tier S' else (1 if x['rank_tier'] == 'Tier A' else 2), -x['score']))
print(f"Total processed and sorted leads: {len(raw_leads)}")

# Generate JSON payload
raw_leads_json = json.dumps(raw_leads, ensure_ascii=False)

def generate_dashboard_html(default_lang='vi'):
    is_vi_default = (default_lang == 'vi')
    btn_vi_class = "lang-btn active" if is_vi_default else "lang-btn"
    btn_zh_class = "lang-btn" if is_vi_default else "lang-btn active"

    return f"""<!DOCTYPE html>
<html lang="{default_lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pet & Grass 潜客智能CRM系统 - 美国本土市场专案</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Noto+Sans+SC:wght@400;500;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- SheetJS for Native Styled Excel Export -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <style>
        :root {{
            --bg-body: #0a0e17;
            --bg-card: rgba(18, 26, 42, 0.75);
            --bg-card-hover: rgba(26, 38, 64, 0.9);
            --border-card: rgba(255, 255, 255, 0.08);
            --border-highlight: rgba(99, 102, 241, 0.35);
            --primary: #6366f1;
            --primary-light: #818cf8;
            --emerald: #10b981;
            --amber: #f59e0b;
            --rose: #f43f5e;
            --cyan: #06b6d4;
            --sky: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font-main: 'Plus Jakarta Sans', 'Noto Sans SC', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-body);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.14) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(6, 182, 212, 0.05) 0px, transparent 60%);
            background-attachment: fixed;
            color: var(--text-main);
            font-family: var(--font-main);
            line-height: 1.6;
            padding: 1.5rem 1.25rem 4rem;
        }}

        .container {{
            max-width: 1440px;
            margin: 0 auto;
        }}

        /* Header */
        header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1.5rem;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-card);
        }}

        .brand-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: var(--primary-light);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            letter-spacing: 0.05em;
        }}

        h1 {{
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .header-desc {{
            color: var(--text-muted);
            max-width: 900px;
            font-size: 0.95rem;
        }}

        .header-controls {{
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex-wrap: wrap;
        }}

        /* In-Page Language Toggle */
        .lang-switcher {{
            display: inline-flex;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-card);
            border-radius: 0.5rem;
            padding: 0.25rem;
            gap: 0.25rem;
        }}

        .lang-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.45rem 0.85rem;
            border-radius: 0.35rem;
            font-size: 0.825rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .lang-btn.active {{
            background: var(--primary);
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.35);
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 1.15rem;
            border-radius: 0.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
            text-decoration: none;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, #6366f1, #4f46e5);
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
        }}
        .btn-primary:hover {{
            background: linear-gradient(135deg, #4f46e5, #4338ca);
            transform: translateY(-1px);
        }}

        .btn-sky {{
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        }}
        .btn-sky:hover {{
            background: linear-gradient(135deg, #0369a1, #075985);
            transform: translateY(-1px);
        }}

        /* Live Radar Section */
        .radar-section {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(14, 116, 144, 0.15));
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 1rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(16px);
        }}

        .radar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 0.75rem;
        }}

        .radar-title-group {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }}

        .radar-title {{
            font-size: 1.05rem;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: 0.02em;
        }}

        .pulse-dot {{
            width: 9px;
            height: 9px;
            background: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            animation: pulse 1.8s infinite;
        }}

        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}

        .radar-cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1rem;
        }}

        .radar-card {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 0.75rem;
            padding: 1rem;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        .radar-card:hover {{
            border-color: rgba(56, 189, 248, 0.4);
            transform: translateY(-2px);
            background: rgba(22, 33, 56, 0.85);
        }}

        .radar-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .radar-region {{
            font-size: 0.75rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .radar-city {{
            font-weight: 700;
            color: #ffffff;
            font-size: 0.95rem;
        }}

        .radar-weather-display {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.5rem 0;
        }}

        .radar-temp {{
            font-size: 1.8rem;
            font-weight: 800;
            font-family: var(--font-mono);
            line-height: 1;
            color: #f8fafc;
        }}

        .radar-desc-text {{
            font-size: 0.8rem;
            color: #cbd5e1;
        }}

        .radar-trigger-pill {{
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: #7dd3fc;
            padding: 0.35rem 0.6rem;
            border-radius: 0.4rem;
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1.3;
            margin-top: 0.5rem;
        }}

        /* Alert Box */
        .alert-box {{
            background: rgba(15, 23, 42, 0.7);
            border-left: 4px solid var(--amber);
            border-radius: 0.5rem;
            padding: 1rem 1.25rem;
            margin-bottom: 2rem;
            font-size: 0.875rem;
            line-height: 1.6;
        }}

        .alert-title {{
            font-weight: 700;
            color: #fbbf24;
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .formula-pill {{
            display: inline-block;
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: #fde68a;
            padding: 0.25rem 0.65rem;
            border-radius: 0.35rem;
            font-family: var(--font-mono);
            font-size: 0.775rem;
            margin: 0.35rem 0;
        }}

        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 0.75rem;
            padding: 1.25rem;
            transition: all 0.2s ease;
            backdrop-filter: blur(12px);
        }}
        .kpi-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--border-highlight);
            transform: translateY(-2px);
        }}

        .kpi-label {{
            font-size: 0.825rem;
            color: var(--text-muted);
            font-weight: 600;
            margin-bottom: 0.4rem;
        }}

        .kpi-value {{
            font-size: 2rem;
            font-weight: 800;
            font-family: var(--font-mono);
            line-height: 1.1;
            margin-bottom: 0.4rem;
        }}

        .kpi-sub {{
            font-size: 0.775rem;
            color: var(--text-muted);
        }}

        .val-primary {{ color: var(--primary-light); }}
        .val-emerald {{ color: var(--emerald); }}
        .val-amber {{ color: var(--amber); }}
        .val-rose {{ color: var(--rose); }}
        .val-cyan {{ color: var(--cyan); }}

        /* Charts Grid */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}

        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 0.75rem;
            padding: 1.25rem;
            backdrop-filter: blur(16px);
        }}

        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .chart-title {{
            font-weight: 700;
            font-size: 0.95rem;
            color: #ffffff;
        }}

        .chart-container {{
            position: relative;
            height: 230px;
            width: 100%;
        }}

        /* Table Section */
        .table-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin-bottom: 2.5rem;
            backdrop-filter: blur(16px);
        }}

        .table-toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}

        .filter-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
        }}

        .search-box {{
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-card);
            color: #ffffff;
            padding: 0.55rem 0.85rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            width: 280px;
            outline: none;
            transition: all 0.2s;
        }}
        .search-box:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }}

        .select-filter {{
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-card);
            color: #ffffff;
            padding: 0.55rem 0.85rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
            outline: none;
            cursor: pointer;
        }}
        .select-filter:focus {{
            border-color: var(--primary);
        }}

        .table-responsive {{
            overflow-x: auto;
            border-radius: 0.5rem;
            border: 1px solid var(--border-card);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            text-align: left;
        }}

        th {{
            background: rgba(15, 23, 42, 0.95);
            padding: 0.85rem 0.9rem;
            font-weight: 700;
            color: #e2e8f0;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border-card);
            white-space: nowrap;
        }}

        td {{
            padding: 0.8rem 0.9rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            vertical-align: middle;
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .lead-name {{
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.2rem;
        }}

        .lead-link {{
            color: #ffffff;
            text-decoration: none;
            transition: color 0.2s;
        }}
        .lead-link:hover {{
            color: var(--primary-light);
            text-decoration: underline;
        }}

        .lead-contact {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem 0.8rem;
            font-size: 0.775rem;
            color: var(--text-muted);
            margin-top: 0.35rem;
        }}

        .lead-contact-item a {{
            color: var(--cyan);
            text-decoration: none;
        }}
        .lead-contact-item a:hover {{
            text-decoration: underline;
        }}

        /* Badges */
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.25rem 0.6rem;
            border-radius: 0.35rem;
            font-size: 0.75rem;
            font-weight: 700;
            white-space: nowrap;
        }}

        .badge-s {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-a {{ background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); }}
        .badge-b {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-c {{ background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }}
        .badge-d {{ background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }}

        .badge-amz-target {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(234, 88, 12, 0.2));
            color: #fde047;
            border: 1px solid rgba(245, 158, 11, 0.4);
            font-weight: 800;
        }}

        .badge-amz-grass {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge-amz-toys {{
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }}

        .badge-amz-none {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        /* Live Weather Cell Badge */
        .weather-cell-badge {{
            display: inline-flex;
            flex-direction: column;
            gap: 0.2rem;
            padding: 0.35rem 0.65rem;
            border-radius: 0.45rem;
            cursor: pointer;
            transition: all 0.2s ease;
            max-width: 210px;
        }}
        .weather-cell-badge:hover {{
            transform: scale(1.02);
            filter: brightness(1.15);
        }}

        .weather-badge-cold {{
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: #bae6fd;
        }}
        .weather-badge-rain {{
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.35);
            color: #c7d2fe;
        }}
        .weather-badge-hot {{
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #fde68a;
        }}
        .weather-badge-mild {{
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #a7f3d0;
        }}

        .weather-temp-row {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.8rem;
            font-weight: 700;
            font-family: var(--font-mono);
        }}

        .weather-trigger-text {{
            font-size: 0.7rem;
            line-height: 1.25;
            opacity: 0.9;
        }}

        .score-pill {{
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 0.95rem;
            color: #ffffff;
        }}

        /* Pagination */
        .pagination {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1.25rem;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .page-btn {{
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-card);
            color: #ffffff;
            padding: 0.45rem 0.9rem;
            border-radius: 0.35rem;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .page-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}

        /* Playbook Grid */
        .playbook-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .playbook-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 0.75rem;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
        }}

        .playbook-title {{
            font-weight: 700;
            font-size: 1.05rem;
            color: #ffffff;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .playbook-quote {{
            background: rgba(15, 23, 42, 0.7);
            border-left: 3px solid var(--primary-light);
            padding: 0.75rem 1rem;
            border-radius: 0 0.5rem 0.5rem 0;
            font-style: italic;
            color: #e2e8f0;
            font-size: 0.9rem;
            margin: 0.5rem 0;
        }}

        /* Modal Popup */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(6px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            padding: 1rem;
        }}

        .modal-box {{
            background: #0f172a;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 1rem;
            max-width: 620px;
            width: 100%;
            padding: 1.75rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
            position: relative;
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid var(--border-card);
            padding-bottom: 0.75rem;
        }}

        .modal-close-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.4rem;
            cursor: pointer;
            line-height: 1;
        }}
        .modal-close-btn:hover {{ color: #ffffff; }}

        footer {{
            text-align: center;
            padding-top: 2rem;
            border-top: 1px solid var(--border-card);
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div>
                <div class="brand-badge" id="lblBrandBadge">⚡ 美国本土市场专案 - RAG智能向量检索与CRM潜客系统</div>
                <h1 id="lblTitle">美国本土狗舍潜客与亚马逊渠道营销分析报告</h1>
                <p class="header-desc" id="lblDesc">
                    第一阶段战略重点：<b>100% 聚焦美国本土市场（United States）</b>。基于 14,138 条清洗线索中严格筛选出的 <b>3,324 条高净值重点潜客（Class A Hot Leads / 分数 ≥ 61）</b>。严格执行 marketing_parameter.html 评分标准，深度集成亚马逊店铺背书，并<b>集成 OpenWeatherMap 全美实时气象雷达</b>，精准锚定三大核心品类：<b>宠物人造草坪</b>、<b>室内便盆/尿垫</b>以及<b>幼犬益智玩具</b>。
                </p>
            </div>
            <div class="header-controls">
                <!-- In-Page Language Toggle -->
                <div class="lang-switcher">
                    <button id="langBtnVi" class="{btn_vi_class}" onclick="setLanguage('vi')">🇻🇳 Tiếng Việt</button>
                    <button id="langBtnZh" class="{btn_zh_class}" onclick="setLanguage('zh')">🇨🇳 简体中文</button>
                </div>
                <button class="btn btn-primary" onclick="exportSalesData()" id="btnExport">📥 导出销售表格 (.XLSX Excel)</button>
            </div>
        </header>

        <!-- Live Real-Time Weather Radar Section -->
        <div class="radar-section">
            <div class="radar-header">
                <div>
                    <div class="radar-title-group">
                        <span class="pulse-dot"></span>
                        <span class="radar-title" id="lblRadarTitle">🛰️ 全美实时气象雷达与情境营销指挥中心 (OPENWEATHERMAP LIVE)</span>
                    </div>
                    <div style="font-size: 0.825rem; color: var(--text-muted); margin-top: 0.25rem;" id="lblRadarDesc">直连 OpenWeatherMap API 接口，按客户所在州、城市与5位邮编即时测算实时气温与雨雪状况。恶劣气候与降雨直接催化宠物室内排泄及益智防拆玩具的刚性采购需求。</div>
                </div>
                <div style="display: flex; gap: 0.75rem; align-items: center;">
                    <span style="font-size: 0.775rem; color: #10b981; font-weight: 600;" id="lblRadarStatus">🟢 直连 OpenWeatherMap API 实时在线</span>
                    <button class="btn btn-sky" style="padding: 0.4rem 0.85rem; font-size: 0.8rem;" onclick="refreshLiveRadar()" id="btnRefreshRadar">🔄 重新扫描全美雷达</button>
                </div>
            </div>

            <!-- Regional Monitor Hubs (WA/OR, IL/Midwest, NY/East, CA/Sunbelt) -->
            <div class="radar-cards-grid" id="radarHubsGrid">
                <!-- Dynamically populated -->
            </div>
        </div>

        <!-- Anti-Saturation Scoring Alert -->
        <div class="alert-box">
            <div class="alert-title">
                <span>🛡️</span>
                <span id="lblAlertTitle">标准打分模型与亚马逊渠道公信力</span>
            </div>
            <div class="alert-content" id="lblAlertContent">
                系统严格遵循 <b>marketing_parameter.html 客户评分标准</b>，基于客户资料库进行精准打分，彻底杜绝满分饱和：
        <br><div class="formula-pill">综合评分 = 基础资料 (官网 + 销售页 + 申请表 + 10+评价 + 多犬种) + 亚马逊背书 (+15分 双目标) + 网站浏览行为</div><br>
        • <b>A 级（重点销售 / 分数 ≥ 61）：</b> 规模化商业繁育犬舍，联系方式完整，拥有亚马逊目标店铺 &rarr; <i>销售团队当天电话直联</i>。<br>
        • <b>B 级（次优潜力 / 分数 45-60）：</b> 商业繁育犬舍 &rarr; <i>自动化培育邮件序列 + 电话跟进</i>。<br>
        • <b>C/D 级（分数 < 45）：</b> 一般潜力或救助机构 &rarr; <i>社交媒体内容长期沉淀</i>。<br>
        • <b>战略地理范围：</b> <i>100% 聚焦美国本土客户（北美区号 +1、全美50州及5位邮编 Zip Code）。海外客户归入未来拓展储备池。</i>
            </div>
        </div>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label" id="kpiLabelTotal">有效清洗全美线索总量</div>
                <div class="kpi-value val-primary">14,138</div>
                <div class="kpi-sub" id="kpiSubTotal">100% 美国本土有效客户（6,330 核心档案）</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label" id="kpiLabelExcluded">负向过滤非商业机构</div>
                <div class="kpi-value val-rose">3,745</div>
                <div class="kpi-sub" id="kpiSubExcluded">AKC、UKC协会、PetSmart、Chewy等</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label" id="kpiLabelBreeders">商业繁育犬舍 (Breeder)</div>
                <div class="kpi-value val-emerald">3,242</div>
                <div class="kpi-sub" id="kpiSubBreeders">幼犬回家礼包（Take-Home Kit）主力买家</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label" id="kpiLabelAmazon">已审计亚马逊渠道店铺</div>
                <div class="kpi-value val-amber">26</div>
                <div class="kpi-sub" id="kpiSubAmazon"><b>13</b> 家同时销售草坪便盆 + 玩具（双目标）</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label" id="kpiLabelPriority">高优先级成交客群 (S & A)</div>
                <div class="kpi-value val-cyan">3,324</div>
                <div class="kpi-sub" id="kpiSubPriority">销售团队优先电话与邮件联络客群</div>
            </div>
        </div>

        <!-- Charts Grid -->
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title" id="chartTitleTier">潜客评级分布梯队 (Tier S / A / B / C / D)</span>
                </div>
                <div class="chart-container">
                    <canvas id="tierChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title" id="chartTitleAmazon">亚马逊渠道分布与商业公信力</span>
                </div>
                <div class="chart-container">
                    <canvas id="amzChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title" id="chartTitleRecency">社媒发布时间新鲜度衰减分布 (Recency)</span>
                </div>
                <div class="chart-container">
                    <canvas id="recencyChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title" id="chartTitleCat">机构业务类型构成 (ICP Fit)</span>
                </div>
                <div class="chart-container">
                    <canvas id="catChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Table Section -->
        <div class="table-section">
            <div class="table-toolbar">
                <div class="filter-group">
                    <input type="text" id="searchInput" class="search-box" placeholder="🔍 搜索犬舍名称、所有者、电话、邮箱、城市、州、邮编..." oninput="onFilterChange()">
                    <select id="amzFilter" class="select-filter" onchange="onFilterChange()">
                        <option value="">🛒 亚马逊状态：全部</option>
                        <option value="both_target">★ 目标玩具 + 草坪便盆（双目标最高信誉）</option>
                        <option value="grass_target">销售草坪 / 便盆（TARGET）</option>
                        <option value="toys_target">销售玩具（TARGET）</option>
                        <option value="has_amz">已发现亚马逊链接（任意）</option>
                        <option value="no_amz">暂无亚马逊链接</option>
                    </select>
                    <select id="tierFilter" class="select-filter" onchange="onFilterChange()">
                        <option value="">🏆 评级筛选：全部</option>
                        <option value="Tier S">S 级（85 - 100 分）</option>
                        <option value="Tier A">A 级（70 - 84 分）</option>
                        <option value="Tier B">B 级（50 - 69 分）</option>
                        <option value="Tier C">C 级（30 - 49 分）</option>
                    </select>
                    <select id="catFilter" class="select-filter" onchange="onFilterChange()">
                        <option value="">🏢 业务类型：全部</option>
                        <option value="Dog Breeder">商业繁育犬舍 (Breeder)</option>
                        <option value="Pet Care">训犬与寄宿机构 (Training)</option>
                        <option value="Pet Rescue">动物救助站 (Rescue)</option>
                    </select>
                    <select id="weatherFilter" class="select-filter" onchange="onFilterChange()">
                        <option value="">🌦️ 实时天气触发：全部</option>
                        <option value="cold">❄️ 严寒暴雪 (<45°F) - 触发室内便盆托盘与防拆玩具</option>
                        <option value="rain">🌧️ 阴雨多雨 - 触发快排水人造草坪</option>
                        <option value="hot">☀️ 高温酷暑 (>80°F) - 触发遮阳草垫与安抚咀嚼玩具</option>
                        <option value="mild">🌤️ 舒适温和 (45-80°F) - 触发幼犬回家大礼包 Take-Home Kit</option>
                    </select>
                </div>
                <div id="recordCount" style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;"></div>
            </div>

            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th id="thCode">序号</th>
                            <th id="thName">客户/犬舍名称 & 联系方式</th>
                            <th id="thLocation">地理位置 (City / State / Zip)</th>
                            <th id="thWeather">实时天气与话术触发</th>
                            <th id="thCategory">业务分类</th>
                            <th id="thAmazon">亚马逊渠道与公信力</th>
                            <th id="thProduct">推荐匹配产品</th>
                            <th id="thScore">综合评分</th>
                            <th id="thTier">评级</th>
                        </tr>
                    </thead>
                    <tbody id="leadsTableBody"></tbody>
                </table>
            </div>

            <div class="pagination">
                <div><span id="lblPage">页码</span> <span id="currentPage" style="font-weight: 700; color: #ffffff;">1</span> / <span id="totalPages">1</span></div>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="page-btn" id="prevBtn" onclick="changePage(-1)" disabled>← 上一页</button>
                    <button class="page-btn" id="nextBtn" onclick="changePage(1)">下一页 →</button>
                </div>
            </div>
        </div>

        <!-- Sales Strategy Playbook Grid (3 Pillars including Weather Contextual Marketing) -->
        <div class="playbook-grid">
            <div class="playbook-card">
                <div class="playbook-title">
                    <span>🎯</span>
                    <span id="pbTitle1">经典销售切入话术（邮件 & 电话沟通）</span>
                </div>
                <div class="playbook-quote" id="pbQuote1">
                    "Do you currently provide a puppy take-home package for your buyers?"<br>（请问贵犬舍目前在幼犬交付时，是否会为买家准备幼犬回家大礼包 Take-Home Kit ？）
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.6;" id="pbNote1">
                    <b>针对已拥有亚马逊店铺的客户：</b> 直接切入定制化批发方案，强调犬舍专属 Logo 印刷与打包成本优势，降低犬舍自采琐碎成本。
                </p>
            </div>

            <div class="playbook-card">
                <div class="playbook-title">
                    <span>💡</span>
                    <span id="pbTitle2">基于亚马逊渠道的品类进攻策略</span>
                </div>
                <ul style="font-size: 0.85rem; color: var(--text-muted); padding-left: 1.25rem; line-height: 1.6;" id="pbList2">
                    <li><b>已推荐草坪/便盆的犬舍：</b> 重点推荐快排水、防咬抗撕裂人造草垫与室内幼犬托盘，出示批量订购 BOM 折扣。</li>
                    <li><b>已推荐玩具的犬舍：</b> 引入安抚幼犬心跳玩具（Snuggle Puppy 同类）与出牙咀嚼玩具包，切入幼犬回家场景。</li>
                    <li><b>尚未建立电商渠道的犬舍：</b> 提供开箱即用的 Take-Home Starter Kit 现成打包方案，赋能犬舍品牌溢价提升 15-20%。</li>
                </ul>
            </div>

            <div class="playbook-card">
                <div class="playbook-title">
                    <span>🌦️</span>
                    <span id="pbTitle3">基于 OpenWeatherMap 天气预报的情境营销杠杆 (Contextual Marketing)</span>
                </div>
                <div class="playbook-quote" id="pbQuote3">
                    "天气数据（源自 天气预报.html）是刺激宠物人造草坪、便盆托盘与益智玩具即时转化的核心外部杠杆。"
                </div>
                <ul style="font-size: 0.85rem; color: var(--text-muted); padding-left: 1.25rem; line-height: 1.6;" id="pbList3">
                    <li><b>恶劣天气/暴雪/酷暑（>90°F / <40°F）：</b> 幼犬无法出门排泄，极易受凉中暑 &rarr; 即时触发室内排水人造草垫与专用便盆托盘。</li>
                    <li><b>长时间闭门室内：</b> 幼犬精力无处释放引发拆家焦虑 &rarr; 精准推送安抚心跳玩具与高耐咬益智磨牙玩具。</li>
                    <li><b>动态定价与急迫性捆绑：</b> 恶劣天气警报期，力推应急 Starter Kit 礼包，客单价（AOV）可提升 20-30% 且成交率显著提升。</li>
                </ul>
            </div>
        </div>

        <!-- Footer -->
        <footer>
            <span id="lblFooter">数据源：<b>Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx</b> • 算法规范严格执行 <b>marketing_parameter.html</b> • 集成 <b>OpenWeatherMap</b> 实时气象引擎。</span>
        </footer>
    </div>

    <!-- Live Weather Pitch Modal -->
    <div class="modal-overlay" id="weatherModalOverlay" onclick="closeWeatherModal(event)">
        <div class="modal-box" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.3rem;">🌦️</span>
                    <span style="font-weight: 800; font-size: 1.1rem; color: #38bdf8;" id="modalTitleText">实时天气情境话术与即时成交方案</span>
                </div>
                <button class="modal-close-btn" onclick="closeWeatherModal()">&times;</button>
            </div>
            <div id="modalContentBody"></div>
        </div>
    </div>

    <!-- Interactive Data, Weather Engine, I18N Engine & Controller -->
    <script>
        const rawLeads = {raw_leads_json};
        let filteredLeads = [...rawLeads];
        let currentPage = 1;
        const pageSize = 50;
        let currentLang = '{default_lang}';

        // Complete Bilingual Dictionary (I18N)
        const i18n = {{
            "vi": {{
                "pageTitle": "Pet & Grass Lead Intelligence CRM - Thị Trường Hoa Kỳ (USA)",
                "brandBadge": "⚡ HỆ THỐNG RAG & CRM KHÁCH HÀNG MỤC TIÊU HOA KỲ (USA)",
                "title": "Báo Cáo Phân Tích Leads & Sàn Amazon Thị Trường Mỹ 2026",
                "desc": "Chiến lược Giai đoạn 1: <b>Tập trung 100% thị phần nội địa Hoa Kỳ (United States)</b> với <b>3.324 Khách Hàng Tiềm Năng Cấp A (Score ≥ 61)</b> chọn lọc từ 14.138 hồ sơ làm sạch. Hệ thống chấm điểm chuẩn theo marketing_parameter.html kết hợp rà soát uy tín gian hàng Amazon US & <b>Tích hợp Radar Thời Tiết Real-Time (OpenWeatherMap API)</b> cho 3 dòng sản phẩm cốt lõi: <b>Cỏ nhân tạo</b>, <b>Khay/Nhà vệ sinh thú cưng</b>, và <b>Đồ chơi cún con</b>.",
                "btnExport": "📥 Tải File Sales (.XLSX Excel)",
                "alertTitle": "Nguyên Tắc Chấm Điểm Chuẩn & Tín Nhiệm Sàn Amazon",
                "alertContent": "Hệ thống áp dụng <b>Mô hình chấm điểm chuẩn xác từ marketing_parameter.html</b> tính trực tiếp trên danh sách hồ sơ khách hàng kết hợp điểm hành vi động:\\n<br><div class=\\\"formula-pill\\\">Điểm Chuẩn = Hồ sơ Nền tảng (Website + Puppy Page + Form Application + 10+ Đánh giá + Đa giống) + Uy tín Kênh Amazon (+15 điểm Target kép) + Hành vi Web</div><br>\\n• <b>Hạng A (Ưu tiên cao nhất / Score ≥ 61):</b> Trại chó quy mô lớn, đầy đủ liên hệ, có gian hàng Amazon bán sản phẩm mục tiêu &rarr; <i>Sales gọi điện thoại chốt ngay</i>.<br>\\n• <b>Hạng B (Quy mô trung bình / Score 45-60):</b> Trại chó thương mại uy tín &rarr; <i>Gửi chuỗi email marketing tự động + Follow-up telesale</i>.<br>\\n• <b>Hạng C/D (< 45 điểm):</b> Tiềm năng tầm trung hoặc cứu trợ &rarr; <i>Nhắn tin Fanpage mạng xã hội</i>.<br>\\n• <b>Phạm vi Địa lý:</b> <i>100% Đối tác nội địa Hoa Kỳ (Mã vùng +1, 50 Bang & Mã bưu chính Zip Code US). Khách hàng quốc tế lưu trữ cho chiến lược mở rộng sau này.</i>",
                "radarTitle": "🛰️ RADAR KHÍ TƯỢNG HOA KỲ & ĐÒN BẨY TIẾP THỊ THEO NGỮ CẢNH (REAL-TIME OPENWEATHERMAP)",
                "radarDesc": "Đo nhiệt độ và lượng mưa trực tiếp tại các bang trọng điểm theo Zip Code & Tọa độ trạm khí tượng. Dữ liệu thời tiết kích hoạt tức thời nhu cầu Thảm Cỏ Nhân Tạo, Khay Potty thoát nước và Đồ chơi xoa dịu stress khi cún bị nhốt trong nhà.",
                "btnRefreshRadar": "🔄 Quét Lại Radar Thời Tiết",
                "radarStatus": "🟢 Trực tiếp từ OpenWeatherMap API",
                "kpiTotal": "Tổng Khách Hàng Tiềm Năng Mỹ",
                "kpiSubTotal": "100% Hoa Kỳ (3.324 Khách Hàng Tiềm Năng Cấp A)",
                "kpiExcluded": "Lọc Bỏ Phi Khách Hàng",
                "kpiSubExcluded": "AKC, UKC, PetSmart, Chewy, Meme (3.745)",
                "kpiBreeders": "Trại Chó Thương Mại (Breeder)",
                "kpiSubBreeders": "Khách mua sỉ Puppy Take-Home Kit (3.242)",
                "kpiAmazon": "Có Gian Hàng Amazon",
                "kpiSubAmazon": "<b>13</b> bán cả Đồ chơi + Cỏ/Potty (TARGET kép)",
                "kpiPriority": "Hot Leads Ưu Tiên (Tier S & A)",
                "kpiSubPriority": "Nhóm ưu tiên gọi điện & email trong ngày (3.324)",
                "chartTier": "Phân Bổ Cấp Bậc (Tier S / A / B / C / D)",
                "chartAmazon": "Trạng Thái Sàn Amazon & Tín Nhiệm Thương Mại",
                "chartRecency": "Độ Tươi Mới Hoạt Động (Recency)",
                "chartCat": "Cơ Cấu Danh Mục Doanh Nghiệp (ICP Fit)",
                "searchPlaceholder": "🔍 Tìm tên trại, chủ sở hữu/đại diện, phone, email, city, state, zip...",
                "amzOptions": [
                    {{"val": "", "text": "🛒 Kênh Amazon: Tất cả"}},
                    {{"val": "both_target", "text": "★ Bán Cả Đồ Chơi + Cỏ/Potty (TARGET Kép)"}},
                    {{"val": "grass_target", "text": "Bán Cỏ / Khay Potty (TARGET)"}},
                    {{"val": "toys_target", "text": "Bán Đồ Chơi (TARGET)"}},
                    {{"val": "has_amz", "text": "Có Gian Hàng Amazon (Bất kỳ)"}},
                    {{"val": "no_amz", "text": "Chưa Tìm Thấy Amazon"}}
                ],
                "tierOptions": [
                    {{"val": "", "text": "🏆 Cấp bậc: Tất cả"}},
                    {{"val": "Tier S", "text": "Tier S (85 - 100 điểm)"}},
                    {{"val": "Tier A", "text": "Tier A (70 - 84 điểm)"}},
                    {{"val": "Tier B", "text": "Tier B (50 - 69 điểm)"}},
                    {{"val": "Tier C", "text": "Tier C (30 - 49 điểm)"}}
                ],
                "catOptions": [
                    {{"val": "", "text": "🏢 Danh mục: Tất cả"}},
                    {{"val": "Dog Breeder", "text": "Dog Breeder / Trại chó"}},
                    {{"val": "Pet Care", "text": "Huấn luyện & Boarding"}},
                    {{"val": "Pet Rescue", "text": "Trạm cứu trợ / Shelter"}}
                ],
                "weatherFilterOptions": [
                    {{"val": "", "text": "🌦️ Ngữ cảnh Thời tiết: Tất cả"}},
                    {{"val": "cold", "text": "❄️ Rét buốt / Tuyết rơi (<45°F) - Đẩy Cỏ & Khay Potty"}},
                    {{"val": "rain", "text": "🌧️ Mưa ẩm / Giông bão - Đẩy Cỏ thoát nước chống hôi"}},
                    {{"val": "hot", "text": "☀️ Nắng gắt / Nóng bức (>80°F) - Đẩy Cỏ râm mát & Đồ chơi"}},
                    {{"val": "mild", "text": "🌤️ Tiết trời ôn hòa (45-80°F) - Đẩy Puppy Take-Home Kit"}}
                ],
                "thCode": "Mã",
                "thName": "Tên Đối Tác & Liên Hệ",
                "thLocation": "Địa Điểm (City / State / Zip)",
                "thWeather": "Thời Tiết Real-Time & Kịch Bản",
                "thCategory": "Danh Mục",
                "thAmazon": "Kênh Amazon & Uy Tín",
                "thProduct": "Gợi Ý Sản Phẩm",
                "thScore": "Điểm Số",
                "thTier": "Hạng",
                "pageLbl": "Trang",
                "prevBtn": "← Trước",
                "nextBtn": "Sau →",
                "pbTitle1": "Kịch Bản Mở Đầu Cho Đội Sales (Email & Điện Thoại)",
                "pbQuote1": "\\"Do you currently provide a puppy take-home package for your buyers?\\"<br>(Hiện tại trại của anh/chị có chuẩn bị bộ quà tặng Take-Home Kit cho khách hàng khi họ đón cún con về nhà mới không?)",
                "pbNote1": "<b>Đối với Breeder đã bán trên Amazon:</b> Nhấn mạnh vào việc giảm chi phí đóng gói tự túc bằng cách đặt kit combo giá sỉ in logo riêng của trại.",
                "pbTitle2": "Đòn Bẩy Sản Phẩm Mục Tiêu Theo Kênh Amazon",
                "pbList2": "<li><b>Đang bán Cỏ/Khay vệ sinh trên Amazon:</b> Chào khay cỏ nhân tạo thoát nước chuyên dụng, kích thước chuẩn chuồng trại với chiết khấu BOM số lượng lớn.</li><li><b>Đang bán Đồ chơi trên Amazon:</b> Giới thiệu đồ chơi ngứa răng xoa dịu mùi hương mẹ (Snuggle Puppy) kèm gói Take-Home Kit.</li><li><b>Chưa có Amazon:</b> Đề xuất giải pháp trọn gói Starter Kit giúp tăng 15-20% giá trị cún con xuất chuồng.</li>",
                "pbTitle3": "Đòn Bẩy Tiếp Thị Theo Ngữ Cảnh Thời Tiết (OpenWeatherMap Trigger)",
                "pbQuote3": "\\"Dữ liệu nhiệt độ & thời tiết OpenWeatherMap (từ file 天气预报.html) là mỏ vàng để kích hoạt chốt đơn cỏ nhân tạo & đồ chơi theo ngữ cảnh thực tế.\\"",
                "pbList3": "<li><b>Mưa bão / Tuyết lạnh / Nắng gắt (>90°F / <40°F):</b> Cún ngại ra đường, nguy cơ cảm lạnh/bỏng chân &rarr; Kích hoạt thảm cỏ nhân tạo thoát nước & khay vệ sinh trong nhà.</li><li><b>Nhốt trong nhà kéo dài:</b> Cún bị cuồng chân, stress cắn xé &rarr; Đẩy mạnh đồ chơi gặm nhai xoa dịu (Snuggle Puppy, KONG, Snuffle Mat).</li><li><b>Định giá động:</b> Trong đợt bão tuyết khẩn cấp, chào combo trọn gói Starter Kit với AOV cao hơn 20-30% vì nhu cầu là tức thì.</li>",
                "footer": "Dữ liệu tổng hợp từ <b>Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx</b> • Chuẩn hóa theo <b>marketing_parameter.html</b> • Tích hợp API <b>OpenWeatherMap</b>.",
                "noMatch": "Không tìm thấy khách hàng phù hợp bộ lọc.",
                "amzNone": "Chưa có Amazon",
                "amzTargetBoth": "★ Cỏ + Đồ Chơi TARGET",
                "amzTargetGrass": "🌱 Cỏ / Potty TARGET",
                "amzTargetToys": "🎾 Đồ Chơi TARGET",
                "amzOther": "Có Amazon (Khác)",
                "prefixSales": "Danh_Sach_Khach_Hang_Sales_Pet_Grass",
                "showingPrefix": "Hiển thị",
                "showingSuffix": "đối tác (Trang",
                "pageSlash": ")",
                "modalTitle": "Kịch Bản Chốt Đơn Theo Thời Tiết Real-Time",
                "modalClose": "Đóng",
                "modalCopy": "📋 Sao chép kịch bản Sales",
                "modalCopied": "✅ Đã sao chép kịch bản!",
                "weatherSyncing": "⚡ Đang đo nhiệt độ...",
                "weatherStation": "Trạm khí tượng:",
                "weatherImpact": "Tác động tâm lý cún cưng:",
                "weatherPitch": "Kịch bản Telesale / Email hôm nay:"
            }},
            "zh": {{
                "pageTitle": "Pet & Grass 潜客智能CRM系统 - 美国本土市场专案",
                "brandBadge": "⚡ 美国本土市场专案 - RAG智能向量检索与CRM潜客系统",
                "title": "美国本土狗舍潜客与亚马逊渠道营销分析报告 2026",
                "desc": "第一阶段战略重点：<b>100% 聚焦美国本土市场（United States）</b>。基于 14,138 条清洗线索中严格筛选出的 <b>3,324 条高净值重点潜客（Class A Hot Leads / 分数 ≥ 61）</b>。严格执行 marketing_parameter.html 评分标准，深度集成亚马逊店铺背书，并<b>集成 OpenWeatherMap 全美实时气象雷达</b>，精准锚定三大核心品类：<b>宠物人造草坪</b>、<b>室内便盆/尿垫</b>以及<b>幼犬益智玩具</b>。",
                "btnExport": "📥 导出销售表格 (.XLSX Excel)",
                "alertTitle": "标准打分模型与亚马逊渠道公信力",
                "alertContent": "系统严格遵循 <b>marketing_parameter.html 客户评分标准</b>，基于客户资料库进行精准打分，彻底杜绝满分饱和：\\n<br><div class=\\\"formula-pill\\\">综合评分 = 基础资料 (官网 + 销售页 + 申请表 + 10+评价 + 多犬种) + 亚马逊背书 (+15分 双目标) + 网站浏览行为</div><br>\\n• <b>A 级（重点销售 / 分数 ≥ 61）：</b> 规模化商业繁育犬舍，联系方式完整，拥有亚马逊目标店铺 &rarr; <i>销售团队当天电话直联</i>。<br>\\n• <b>B 级（次优潜力 / 分数 45-60）：</b> 商业繁育犬舍 &rarr; <i>自动化培育邮件序列 + 电话跟进</i>。<br>\\n• <b>C/D 级（分数 < 45）：</b> 一般潜力或救助机构 &rarr; <i>社交媒体内容长期沉淀</i>。<br>\\n• <b>战略地理范围：</b> <i>100% 聚焦美国本土客户（北美区号 +1、全美50州及5位邮编 Zip Code）。海外客户归入未来拓展储备池。</i>",
                "radarTitle": "🛰️ 全美实时气象雷达与情境营销指挥中心 (OPENWEATHERMAP LIVE)",
                "radarDesc": "直连 OpenWeatherMap API 接口，按客户所在州、城市与5位邮编即时测算实时气温与雨雪状况。恶劣气候与降雨直接催化宠物室内排泄及益智防拆玩具的刚性采购需求。",
                "btnRefreshRadar": "🔄 重新扫描全美雷达",
                "radarStatus": "🟢 直连 OpenWeatherMap API 实时在线",
                "kpiTotal": "有效清洗全美线索总量",
                "kpiSubTotal": "100% 美国本土（3,324 条高净值线索）",
                "kpiExcluded": "负向过滤非商业机构",
                "kpiSubExcluded": "AKC、UKC协会、PetSmart、Chewy等 (3,745)",
                "kpiBreeders": "商业繁育犬舍 (Breeder)",
                "kpiSubBreeders": "幼犬回家礼包（Take-Home Kit）主力买家 (3,242)",
                "kpiAmazon": "已审计亚马逊渠道店铺",
                "kpiSubAmazon": "<b>13</b> 家同时销售草坪便盆 + 玩具（双目标）",
                "kpiPriority": "高优先级成交客群 (S & A)",
                "kpiSubPriority": "销售团队优先电话与邮件联系 (3,324)",
                "chartTier": "潜客评级分布梯队 (Tier S / A / B / C / D)",
                "chartAmazon": "亚马逊渠道分布与商业公信力",
                "chartRecency": "社媒发布时间新鲜度衰减分布 (Recency)",
                "chartCat": "机构业务类型构成 (ICP Fit)",
                "searchPlaceholder": "🔍 搜索犬舍名称、所有者/代表、电话、邮箱、城市、州、邮编...",
                "amzOptions": [
                    {{"val": "", "text": "🛒 亚马逊状态：全部"}},
                    {{"val": "both_target", "text": "★ 目标玩具 + 草坪便盆（双目标最高信誉）"}},
                    {{"val": "grass_target", "text": "销售草坪 / 便盆（TARGET）"}},
                    {{"val": "toys_target", "text": "销售玩具（TARGET）"}},
                    {{"val": "has_amz", "text": "已发现亚马逊链接（任意）"}},
                    {{"val": "no_amz", "text": "暂无亚马逊链接"}}
                ],
                "tierOptions": [
                    {{"val": "", "text": "🏆 评级筛选：全部"}},
                    {{"val": "Tier S", "text": "S 级（85 - 100 分）"}},
                    {{"val": "Tier A", "text": "A 级（70 - 84 分）"}},
                    {{"val": "Tier B", "text": "B 级（50 - 69 分）"}},
                    {{"val": "Tier C", "text": "C 级（30 - 49 分）"}}
                ],
                "catOptions": [
                    {{"val": "", "text": "🏢 业务类型：全部"}},
                    {{"val": "Dog Breeder", "text": "商业繁育犬舍 (Breeder)"}},
                    {{"val": "Pet Care", "text": "训犬与寄宿机构 (Training)"}},
                    {{"val": "Pet Rescue", "text": "动物救助站 (Rescue)"}}
                ],
                "weatherFilterOptions": [
                    {{"val": "", "text": "🌦️ 实时天气触发：全部"}},
                    {{"val": "cold", "text": "❄️ 严寒暴雪 (<45°F) - 触发室内便盆托盘与防拆玩具"}},
                    {{"val": "rain", "text": "🌧️ 阴雨多雨 - 触发快排水人造草坪"}},
                    {{"val": "hot", "text": "☀️ 高温酷暑 (>80°F) - 触发遮阳草垫与安抚咀嚼玩具"}},
                    {{"val": "mild", "text": "🌤️ 舒适温和 (45-80°F) - 触发幼犬回家大礼包 Take-Home Kit"}}
                ],
                "thCode": "序号",
                "thName": "客户/犬舍名称 & 联系方式",
                "thLocation": "地理位置 (City / State / Zip)",
                "thWeather": "实时天气与话术触发",
                "thCategory": "业务分类",
                "thAmazon": "亚马逊渠道与公信力",
                "thProduct": "推荐匹配产品",
                "thScore": "综合评分",
                "thTier": "评级",
                "pageLbl": "页码",
                "prevBtn": "← 上一页",
                "nextBtn": "下一页 →",
                "pbTitle1": "经典销售切入话术（邮件 & 电话沟通）",
                "pbQuote1": "\\"Do you currently provide a puppy take-home package for your buyers?\\"<br>（请问贵犬舍目前在幼犬交付时，是否会为买家准备幼犬回家大礼包 Take-Home Kit ？）",
                "pbNote1": "<b>针对已拥有亚马逊店铺的客户：</b> 直接切入定制化批发方案，强调犬舍专属 Logo 印刷与打包成本优势，降低犬舍自采琐碎成本。",
                "pbTitle2": "基于亚马逊渠道的品类进攻策略",
                "pbList2": "<li><b>已推荐草坪/便盆的犬舍：</b> 重点推荐快排水、防咬抗撕裂人造草垫与室内幼犬托盘，出示批量订购 BOM 折扣。</li><li><b>已推荐玩具的犬舍：</b> 引入安抚幼犬心跳玩具（Snuggle Puppy 同类）与出牙咀嚼玩具包，切入幼犬回家场景。</li><li><b>尚未建立电商渠道的犬舍：</b> 提供开箱即用的 Take-Home Starter Kit 现成打包方案，赋能犬舍品牌溢价提升 15-20%。</li>",
                "pbTitle3": "基于 OpenWeatherMap 天气预报的情境营销杠杆 (Contextual Marketing)",
                "pbQuote3": "\\"天气数据（源自 天气预报.html）是刺激宠物人造草坪、便盆托盘与益智玩具即时转化的核心外部杠杆。\\"",
                "pbList3": "<li><b>恶劣天气/暴雪/酷暑（>90°F / <40°F）：</b> 幼犬无法出门排泄，极易受凉中暑 &rarr; 即时触发室内排水人造草垫与专用便盆托盘。</li><li><b>长时间闭门室内：</b> 幼犬精力无处释放引发拆家焦虑 &rarr; 精准推送安抚心跳玩具与高耐咬益智磨牙玩具。</li><li><b>动态定价与急迫性捆绑：</b> 恶劣天气警报期，力推应急 Starter Kit 礼包，客单价（AOV）可提升 20-30% 且成交率显著提升。</li>",
                "footer": "数据源：<b>Master_Standard_Leads_PetGrass_Potty_Toys_2026.xlsx</b> • 算法规范严格执行 <b>marketing_parameter.html</b> • 集成 <b>OpenWeatherMap</b> 实时气象引擎。",
                "noMatch": "未检索到符合条件的客户线索。",
                "amzNone": "暂无亚马逊",
                "amzTargetBoth": "★ 草坪+玩具 TARGET",
                "amzTargetGrass": "🌱 草坪/便盆 TARGET",
                "amzTargetToys": "🎾 益智玩具 TARGET",
                "amzOther": "亚马逊其他品类",
                "prefixSales": "美国狗舍潜客销售联络表",
                "showingPrefix": "已筛选出",
                "showingSuffix": "家客户（第",
                "pageSlash": "页）",
                "modalTitle": "实时天气情境话术与即时成交方案",
                "modalClose": "关闭",
                "modalCopy": "📋 一键复制销售话术",
                "modalCopied": "✅ 话术已复制至剪贴板！",
                "weatherSyncing": "⚡ 正在测算气温...",
                "weatherStation": "气象观测站：",
                "weatherImpact": "幼犬心理与生理反应：",
                "weatherPitch": "今日电销/邮件开场话术："
            }}
        }};

        // OpenWeatherMap Engine Parameters
        const OWM_API_KEY = '2e519601af416c660ebaa2323bee4f54';
        const weatherCache = {{}};

        // 4 Regional Hubs for the Live Radar Bar
        const regionalHubs = [
            {{ id: 'pnw', nameVi: 'Tây Bắc Thái Bình Dương (PNW)', nameZh: '太平洋西北 (WA / OR)', city: 'Seattle, WA', zip: '98101', defaultTemp: 48, defaultMain: 'Rain', defaultDesc: 'Mưa ẩm triền miên', triggerVi: '🌧️ Cún ngại ướt chân -> Chốt Cỏ nhân tạo & Khay Potty thoát nước', triggerZh: '🌧️ 多雨泥泞：力推快排水人造草垫与室内幼犬便盆托盘' }},
            {{ id: 'midwest', nameVi: 'Vùng Trung Tây & Tuyết Rơi', nameZh: '中西部大湖区 (IL / MN / OH)', city: 'Chicago, IL', zip: '60601', defaultTemp: 32, defaultMain: 'Snow', defaultDesc: 'Rét buốt / Tuyết', triggerVi: '❄️ Bão tuyết cấm ra ngoài -> Chốt combo Cỏ + Đồ chơi gặm xoa dịu stress', triggerZh: '❄️ 严寒暴雪：足不出户排泄，力推防拆益智玩具+室内草坪' }},
            {{ id: 'east', nameVi: 'Bờ Đông & Đô Thị Lớn', nameZh: '东部走廊 (NY / PA / VA)', city: 'New York, NY', zip: '10001', defaultTemp: 55, defaultMain: 'Clouds', defaultDesc: 'Mây rải rác', triggerVi: '🏢 Chung cư/Nhà phố hẹp -> Chốt Starter Kit tiện lợi', triggerZh: '🏢 紧凑公寓生活：极度需要防臭抗菌宠物草坪与便垫' }},
            {{ id: 'sunbelt', nameVi: 'Bờ Nam & Bờ Tây Nắng Nóng', nameZh: '阳光带与西岸 (CA / TX / FL)', city: 'San Diego, CA', zip: '92114', defaultTemp: 78, defaultMain: 'Clear', defaultDesc: 'Nắng ấm', triggerVi: '☀️ Sốc nhiệt trưa hè -> Chốt Thảm cỏ râm mát + Đồ chơi cấp nước', triggerZh: '☀️ 酷暑路面烫脚：力推遮阳抗UV草垫与耐咬洁齿玩具' }}
        ];

        async function fetchWeather(lead) {{
            const locKey = lead.zip ? lead.zip : `${{lead.city || ''}}_${{lead.state || ''}}`;
            if (!locKey || locKey === '_') return null;
            if (weatherCache[locKey]) return weatherCache[locKey];

            let url = '';
            if (lead.zip) {{
                url = `https://api.openweathermap.org/data/2.5/weather?zip=${{lead.zip}},US&units=imperial&appid=${{OWM_API_KEY}}`;
            }} else if (lead.city && lead.state) {{
                url = `https://api.openweathermap.org/data/2.5/weather?q=${{encodeURIComponent(lead.city)}},${{lead.state}},US&units=imperial&appid=${{OWM_API_KEY}}`;
            }}

            try {{
                const res = await fetch(url);
                if (!res.ok) throw new Error('API request failed');
                const data = await res.json();
                const tempF = Math.round(data.main.temp);
                const tempC = Math.round((tempF - 32) * 5 / 9);
                const main = data.weather[0].main;
                const desc = data.weather[0].description;
                const icon = data.weather[0].icon;

                let conditionType = 'mild';
                if (tempF < 45 || main === 'Snow') conditionType = 'cold';
                else if (main === 'Rain' || main === 'Drizzle' || main === 'Thunderstorm') conditionType = 'rain';
                else if (tempF > 80) conditionType = 'hot';

                weatherCache[locKey] = {{
                    locKey,
                    tempF,
                    tempC,
                    main,
                    desc,
                    icon,
                    humidity: data.main.humidity,
                    wind: data.wind.speed,
                    conditionType,
                    cityName: data.name || lead.city,
                    isLive: true
                }};
                return weatherCache[locKey];
            }} catch (err) {{
                const st = (lead.state || '').toUpperCase();
                let fType = 'mild', fTemp = 68, fDesc = 'Trời mát / Ôn hòa', fMain = 'Clear', fIcon = '01d';
                if (['WA', 'OR'].includes(st)) {{
                    fType = 'rain'; fTemp = 48; fDesc = 'Mưa ẩm cục bộ'; fMain = 'Rain'; fIcon = '10d';
                }} else if (['NY', 'MN', 'ND', 'NE', 'IL', 'PA', 'IN', 'SD', 'IA', 'RI', 'OH', 'WI', 'MI'].includes(st)) {{
                    fType = 'cold'; fTemp = 36; fDesc = 'Gió lạnh / Rét buốt'; fMain = 'Snow'; fIcon = '13d';
                }} else if (['CA', 'FL', 'TX', 'AZ', 'NV'].includes(st)) {{
                    fType = 'hot'; fTemp = 82; fDesc = 'Nắng ráo / Nhiệt cao'; fMain = 'Clear'; fIcon = '01d';
                }}
                weatherCache[locKey] = {{
                    locKey,
                    tempF: fTemp,
                    tempC: Math.round((fTemp - 32) * 5 / 9),
                    main: fMain,
                    desc: fDesc,
                    icon: fIcon,
                    humidity: 55,
                    wind: 6,
                    conditionType: fType,
                    cityName: lead.city || lead.state,
                    isLive: false
                }};
                return weatherCache[locKey];
            }}
        }}

        async function renderRadarHubs() {{
            const grid = document.getElementById('radarHubsGrid');
            grid.innerHTML = '';
            const isVi = currentLang === 'vi';

            for (const hub of regionalHubs) {{
                const card = document.createElement('div');
                card.className = 'radar-card';
                card.id = `radar-card-${{hub.id}}`;
                
                const title = isVi ? hub.nameVi : hub.nameZh;
                const trigger = isVi ? hub.triggerVi : hub.triggerZh;

                card.innerHTML = `
                    <div class="radar-card-top">
                        <span class="radar-region">${{title}}</span>
                        <span style="font-size: 0.75rem; color: #10b981; font-weight: 700;">LIVE</span>
                    </div>
                    <div class="radar-city">📍 ${{hub.city}} (${{hub.zip}})</div>
                    <div class="radar-weather-display">
                        <span id="temp-${{hub.id}}" class="radar-temp">${{hub.defaultTemp}}°F</span>
                        <div>
                            <div id="desc-${{hub.id}}" class="radar-desc-text">${{hub.defaultDesc}}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted); font-family: var(--font-mono);" id="sub-${{hub.id}}">${{Math.round((hub.defaultTemp-32)*5/9)}}°C</div>
                        </div>
                    </div>
                    <div class="radar-trigger-pill">${{trigger}}</div>
                `;
                grid.appendChild(card);

                fetchWeather({{ zip: hub.zip, city: hub.city.split(',')[0], state: hub.city.split(',')[1].trim() }}).then(w => {{
                    if (w) {{
                        const elTemp = document.getElementById(`temp-${{hub.id}}`);
                        const elDesc = document.getElementById(`desc-${{hub.id}}`);
                        const elSub = document.getElementById(`sub-${{hub.id}}`);
                        if (elTemp) elTemp.innerText = `${{w.tempF}}°F`;
                        if (elDesc) elDesc.innerText = `${{w.main}} (${{w.desc}})`;
                        if (elSub) elSub.innerText = `${{w.tempC}}°C • 💧${{w.humidity}}% • 💨${{w.wind}}mph`;
                    }}
                }});
            }}
        }}

        function refreshLiveRadar() {{
            for (let k in weatherCache) delete weatherCache[k];
            renderRadarHubs();
            renderTable();
        }}

        function setLanguage(lang) {{
            currentLang = lang;
            const t = i18n[lang];

            document.getElementById('langBtnVi').classList.toggle('active', lang === 'vi');
            document.getElementById('langBtnZh').classList.toggle('active', lang === 'zh');

            document.title = t.pageTitle;
            document.getElementById('lblBrandBadge').innerText = t.brandBadge;
            document.getElementById('lblTitle').innerText = t.title;
            document.getElementById('lblDesc').innerHTML = t.desc;
            document.getElementById('btnExport').innerText = t.btnExport;
            document.getElementById('lblAlertTitle').innerText = t.alertTitle;
            document.getElementById('lblAlertContent').innerHTML = t.alertContent;

            document.getElementById('lblRadarTitle').innerText = t.radarTitle;
            document.getElementById('lblRadarDesc').innerHTML = t.radarDesc;
            document.getElementById('lblRadarStatus').innerText = t.radarStatus;
            document.getElementById('btnRefreshRadar').innerText = t.btnRefreshRadar;

            document.getElementById('kpiLabelTotal').innerText = t.kpiTotal;
            document.getElementById('kpiSubTotal').innerHTML = t.kpiSubTotal;
            document.getElementById('kpiLabelExcluded').innerText = t.kpiExcluded;
            document.getElementById('kpiSubExcluded').innerHTML = t.kpiSubExcluded;
            document.getElementById('kpiLabelBreeders').innerText = t.kpiBreeders;
            document.getElementById('kpiSubBreeders').innerHTML = t.kpiSubBreeders;
            document.getElementById('kpiLabelAmazon').innerText = t.kpiAmazon;
            document.getElementById('kpiSubAmazon').innerHTML = t.kpiSubAmazon;
            document.getElementById('kpiLabelPriority').innerText = t.kpiPriority;
            document.getElementById('kpiSubPriority').innerHTML = t.kpiSubPriority;

            document.getElementById('chartTitleTier').innerText = t.chartTier;
            document.getElementById('chartTitleAmazon').innerText = t.chartAmazon;
            document.getElementById('chartTitleRecency').innerText = t.chartRecency;
            document.getElementById('chartTitleCat').innerText = t.chartCat;

            document.getElementById('searchInput').placeholder = t.searchPlaceholder;
            
            const selAmz = document.getElementById('amzFilter');
            const curAmz = selAmz.value;
            selAmz.innerHTML = t.amzOptions.map(o => `<option value="${{o.val}}"${{o.val===curAmz?' selected':''}}>${{o.text}}</option>`).join('');

            const selTier = document.getElementById('tierFilter');
            const curTier = selTier.value;
            selTier.innerHTML = t.tierOptions.map(o => `<option value="${{o.val}}"${{o.val===curTier?' selected':''}}>${{o.text}}</option>`).join('');

            const selCat = document.getElementById('catFilter');
            const curCat = selCat.value;
            selCat.innerHTML = t.catOptions.map(o => `<option value="${{o.val}}"${{o.val===curCat?' selected':''}}>${{o.text}}</option>`).join('');

            const selW = document.getElementById('weatherFilter');
            const curW = selW.value;
            selW.innerHTML = t.weatherFilterOptions.map(o => `<option value="${{o.val}}"${{o.val===curW?' selected':''}}>${{o.text}}</option>`).join('');

            document.getElementById('thCode').innerText = t.thCode;
            document.getElementById('thName').innerText = t.thName;
            document.getElementById('thLocation').innerText = t.thLocation;
            document.getElementById('thWeather').innerText = t.thWeather;
            document.getElementById('thCategory').innerText = t.thCategory;
            document.getElementById('thAmazon').innerText = t.thAmazon;
            document.getElementById('thProduct').innerText = t.thProduct;
            document.getElementById('thScore').innerText = t.thScore;
            document.getElementById('thTier').innerText = t.thTier;

            document.getElementById('lblPage').innerText = t.pageLbl;
            document.getElementById('prevBtn').innerText = t.prevBtn;
            document.getElementById('nextBtn').innerText = t.nextBtn;

            document.getElementById('pbTitle1').innerText = t.pbTitle1;
            document.getElementById('pbQuote1').innerHTML = t.pbQuote1;
            document.getElementById('pbNote1').innerHTML = t.pbNote1;
            document.getElementById('pbTitle2').innerText = t.pbTitle2;
            document.getElementById('pbList2').innerHTML = t.pbList2;
            document.getElementById('pbTitle3').innerText = t.pbTitle3;
            document.getElementById('pbQuote3').innerHTML = t.pbQuote3;
            document.getElementById('pbList3').innerHTML = t.pbList3;
            document.getElementById('lblFooter').innerHTML = t.footer;
            document.getElementById('modalTitleText').innerText = t.modalTitle;

            renderRadarHubs();
            renderTable();
        }}

        function getLeadWeatherTrigger(lead, w) {{
            const isVi = currentLang === 'vi';
            const cond = w ? w.conditionType : 'mild';
            const temp = w ? `${{w.tempF}}°F (${{w.tempC}}°C)` : '';

            if (cond === 'cold') {{
                return {{
                    icon: '❄️',
                    badgeClass: 'weather-badge-cold',
                    label: isVi ? `${{temp}} Rét buốt` : `${{temp}} 严寒暴雪`,
                    pitch: isVi ? 'Khay Potty & Thảm Cỏ chống buốt chân + Đồ chơi xoa dịu' : '室内草坪便盆套件 + 防拆解压益智玩具'
                }};
            }} else if (cond === 'rain') {{
                return {{
                    icon: '🌧️',
                    badgeClass: 'weather-badge-rain',
                    label: isVi ? `${{temp}} Mưa ẩm` : `${{temp}} 多雨潮湿`,
                    pitch: isVi ? 'Thảm cỏ thoát nước chuyên dụng ngăn mùi hôi lông' : '快排水抗菌人造草垫 + 室内排泄便盆'
                }};
            }} else if (cond === 'hot') {{
                return {{
                    icon: '☀️',
                    badgeClass: 'weather-badge-hot',
                    label: isVi ? `${{temp}} Nắng gắt` : `${{temp}} 高温炎热`,
                    pitch: isVi ? 'Cỏ nhân tạo góc râm mát + Đồ chơi gặm xoa dịu nhiệt' : '抗UV遮阳草垫 + 洁齿耐咬咀嚼玩具'
                }};
            }} else {{
                return {{
                    icon: '🌤️',
                    badgeClass: 'weather-badge-mild',
                    label: isVi ? `${{temp}} Ôn hòa` : `${{temp}} 气候温和`,
                    pitch: isVi ? 'Bộ quà tặng Puppy Take-Home Kit trọn gói' : '幼犬回家大礼包 Take-Home Kit 现成方案'
                }};
            }}
        }}

        function renderTable() {{
            const tbody = document.getElementById('leadsTableBody');
            tbody.innerHTML = '';
            const t = i18n[currentLang];
            const isVi = currentLang === 'vi';
            
            const start = (currentPage - 1) * pageSize;
            const end = start + pageSize;
            const pageData = filteredLeads.slice(start, end);
            
            if (pageData.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2.5rem; color: var(--text-muted); font-size: 0.95rem;">${{t.noMatch}}</td></tr>`;
                document.getElementById('recordCount').innerText = '0';
                return;
            }}

            pageData.forEach(lead => {{
                const tr = document.createElement('tr');
                
                // Tier Badge
                let tierClass = 'badge-b';
                if (lead.rank_tier === 'Tier S') tierClass = 'badge-s';
                else if (lead.rank_tier === 'Tier A') tierClass = 'badge-a';
                else if (lead.rank_tier === 'Tier C') tierClass = 'badge-c';
                else if (lead.rank_tier === 'Tier D') tierClass = 'badge-d';

                // Amazon Badge
                let amzBadge = `<span class="badge badge-amz-none">${{t.amzNone}}</span>`;
                if (lead.amz_cat.includes('Selling pet toys + Artificial grass')) {{
                    amzBadge = `<span class="badge badge-amz-target" title="TARGET: Đang bán cả đồ chơi và khay/cỏ">${{t.amzTargetBoth}}</span>`;
                }} else if (lead.amz_cat.includes('Selling artificial grass')) {{
                    amzBadge = `<span class="badge badge-amz-grass" title="TARGET: Đang bán cỏ hoặc khay vệ sinh">${{t.amzTargetGrass}}</span>`;
                }} else if (lead.amz_cat.includes('Selling pet toys')) {{
                    amzBadge = `<span class="badge badge-amz-toys" title="Đang bán đồ chơi">${{t.amzTargetToys}}</span>`;
                }} else if (lead.amz_cat.includes('target sales') || lead.amz_cat.includes('has_amz')) {{
                    amzBadge = `<span class="badge badge-amz-none">${{t.amzOther}}</span>`;
                }}

                if (lead.amz_link) {{
                    amzBadge = `<a href="${{lead.amz_link}}" target="_blank" style="text-decoration: none;">${{amzBadge}}</a>`;
                }}

                // Lead Name and Links
                let linkHtml = `<a class="lead-link" href="${{lead.url || lead.website || '#'}}" target="_blank">${{lead.name}}</a>`;
                if (lead.website) {{
                    linkHtml += ` <a href="${{lead.website}}" target="_blank" title="${{isVi ? 'Website chính thức' : '官方网站'}}" style="color: var(--emerald); text-decoration: none; font-size: 0.85rem;">🌐</a>`;
                }}

                // Owner / Representative row (User Requested Field)
                let ownerHtml = '';
                if (lead.owner && lead.owner !== 'Đang cập nhật hồ sơ' && lead.owner !== 'Chưa xác thực') {{
                    ownerHtml = `<div style="font-size: 0.775rem; color: #38bdf8; margin-top: 0.2rem; display: flex; align-items: center; gap: 0.35rem;">
                        <span>👤</span> <span style="font-weight: 700;">${{isVi ? 'Đại diện / Chủ:' : '所有者/代表:'}}</span> <span style="color: #f1f5f9;">${{lead.owner}}</span>
                    </div>`;
                }} else {{
                    ownerHtml = `<div style="font-size: 0.74rem; color: #64748b; margin-top: 0.15rem;">👤 ${{isVi ? 'Đại diện: Đang cập nhật' : '代表: 待进一步核实'}}</div>`;
                }}

                // Contact Items Row
                let contactItems = [];
                if (lead.phone) {{
                    contactItems.push(`<span class="lead-contact-item">📞 <a href="tel:${{lead.phone}}">${{lead.phone}}</a></span>`);
                }}
                if (lead.email) {{
                    contactItems.push(`<span class="lead-contact-item">✉️ <a href="mailto:${{lead.email}}">${{lead.email}}</a></span>`);
                }}
                let contactHtml = contactItems.length > 0 ? `<div class="lead-contact">${{contactItems.join('')}}</div>` : '';

                // Location formatting
                let locParts = [lead.city, lead.state, lead.zip].filter(Boolean);
                let locStr = locParts.length > 0 ? locParts.join(', ') : (lead.country || 'USA');

                // Initial Weather Badge
                const cleanStt = String(lead.stt).replace(/[^a-zA-Z0-9]/g, '');
                const weatherBadgeId = `wb-${{cleanStt}}`;
                const initLocKey = lead.zip || `${{lead.city||''}}_${{lead.state||''}}`;
                const cachedW = weatherCache[initLocKey];
                const trg = getLeadWeatherTrigger(lead, cachedW);

                tr.innerHTML = `
                    <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${{lead.stt}}</td>
                    <td>
                        <div class="lead-name">${{linkHtml}}</div>
                        ${{ownerHtml}}
                        ${{contactHtml}}
                    </td>
                    <td><span style="font-size: 0.8rem; color: #cbd5e1;">📍 ${{locStr}}</span></td>
                    <td>
                        <div id="${{weatherBadgeId}}" class="weather-cell-badge ${{trg.badgeClass}}" onclick="openWeatherModal('${{lead.stt}}')" title="${{isVi ? 'Nhấp để xem chi tiết thời tiết & kịch bản sales' : '点击查看实时天气与针对性销售话术'}}">
                            <div class="weather-temp-row">
                                <span>${{trg.icon}}</span>
                                <span>${{trg.label}}</span>
                            </div>
                            <div class="weather-trigger-text">${{trg.pitch}}</div>
                        </div>
                    </td>
                    <td><span style="color: #cbd5e1;">${{lead.cat}}</span></td>
                    <td>${{amzBadge}}</td>
                    <td><span style="font-size: 0.8rem; color: #cbd5e1;">${{lead.product_fit}}</span></td>
                    <td><span class="score-pill">${{lead.score}}đ</span></td>
                    <td><span class="badge ${{tierClass}}">${{lead.rank_tier}}</span></td>
                `;
                tbody.appendChild(tr);

                // If not cached, trigger background async fetch
                if (!cachedW) {{
                    fetchWeather(lead).then(w => {{
                        const el = document.getElementById(weatherBadgeId);
                        if (el && w) {{
                            const updatedTrg = getLeadWeatherTrigger(lead, w);
                            el.className = `weather-cell-badge ${{updatedTrg.badgeClass}}`;
                            el.innerHTML = `
                                <div class="weather-temp-row">
                                    <span>${{updatedTrg.icon}}</span>
                                    <span>${{updatedTrg.label}}</span>
                                </div>
                                <div class="weather-trigger-text">${{updatedTrg.pitch}}</div>
                            `;
                        }}
                    }});
                }}
            }});

            const totalPages = Math.ceil(filteredLeads.length / pageSize) || 1;
            document.getElementById('currentPage').innerText = currentPage;
            document.getElementById('totalPages').innerText = totalPages;
            document.getElementById('recordCount').innerText = `${{t.showingPrefix}} ${{filteredLeads.length.toLocaleString()}} ${{t.showingSuffix}} ${{currentPage}}/${{totalPages}}${{t.pageSlash}}`;
            document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = currentPage >= totalPages;
        }}

        function onFilterChange() {{
            const search = document.getElementById('searchInput').value.toLowerCase().trim();
            const amzVal = document.getElementById('amzFilter').value;
            const tierVal = document.getElementById('tierFilter').value;
            const catVal = document.getElementById('catFilter').value;
            const weatherVal = document.getElementById('weatherFilter').value;

            filteredLeads = rawLeads.filter(l => {{
                // Search match
                const matchSearch = !search || 
                    l.name.toLowerCase().includes(search) || 
                    (l.owner && l.owner.toLowerCase().includes(search)) ||
                    (l.phone && l.phone.toLowerCase().includes(search)) ||
                    (l.email && l.email.toLowerCase().includes(search)) ||
                    (l.city && l.city.toLowerCase().includes(search)) ||
                    (l.state && l.state.toLowerCase().includes(search)) ||
                    (l.zip && l.zip.toLowerCase().includes(search)) ||
                    l.cat.toLowerCase().includes(search);
                
                // Tier match
                const matchTier = !tierVal || l.rank_tier === tierVal;

                // Cat match
                const matchCat = !catVal || l.cat.includes(catVal);

                // Amazon match
                let matchAmz = true;
                if (amzVal === 'both_target') matchAmz = l.amz_cat.includes('Selling pet toys + Artificial grass');
                else if (amzVal === 'grass_target') matchAmz = l.amz_cat.includes('Selling artificial grass');
                else if (amzVal === 'toys_target') matchAmz = l.amz_cat.includes('Selling pet toys');
                else if (amzVal === 'has_amz') matchAmz = l.amz_cat !== 'Amazon link not found';
                else if (amzVal === 'no_amz') matchAmz = l.amz_cat === 'Amazon link not found';

                // Weather match
                let matchWeather = true;
                if (weatherVal) {{
                    const st = (l.state || '').toUpperCase();
                    if (weatherVal === 'cold') matchWeather = ['NY', 'MN', 'ND', 'NE', 'IL', 'PA', 'IN', 'SD', 'IA', 'RI', 'OH', 'WI', 'MI'].includes(st);
                    else if (weatherVal === 'rain') matchWeather = ['WA', 'OR', 'VA', 'NC', 'LA', 'FL'].includes(st);
                    else if (weatherVal === 'hot') matchWeather = ['CA', 'AZ', 'NV', 'TX', 'FL'].includes(st);
                    else if (weatherVal === 'mild') matchWeather = !['NY', 'MN', 'ND', 'NE', 'IL', 'PA', 'IN', 'SD', 'IA', 'RI', 'OH', 'WI', 'MI', 'WA', 'OR'].includes(st);
                }}

                return matchSearch && matchTier && matchCat && matchAmz && matchWeather;
            }});

            currentPage = 1;
            renderTable();
        }}

        function changePage(delta) {{
            const totalPages = Math.ceil(filteredLeads.length / pageSize);
            const target = currentPage + delta;
            if (target >= 1 && target <= totalPages) {{
                currentPage = target;
                renderTable();
                document.querySelector('.table-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}

        // Interactive Weather Pitch Modal
        function openWeatherModal(stt) {{
            const lead = rawLeads.find(l => String(l.stt) === String(stt));
            if (!lead) return;

            const isVi = currentLang === 'vi';
            const t = i18n[currentLang];
            const locKey = lead.zip || `${{lead.city||''}}_${{lead.state||''}}`;
            const w = weatherCache[locKey] || {{
                tempF: 65, tempC: 18, main: 'Clear', desc: 'Ôn hòa', humidity: 55, wind: 6, conditionType: 'mild'
            }};

            let condTitle = '', petBehavior = '', salesPitch = '';

            if (w.conditionType === 'cold') {{
                condTitle = isVi ? `❄️ Rét Buốt & Đóng Băng (${{w.tempF}}°F / ${{w.tempC}}°C)` : `❄️ 严寒冰冻与暴雪气候 (${{w.tempF}}°F / ${{w.tempC}}°C)`;
                petBehavior = isVi 
                    ? `Nhiệt độ xuống thấp khiến cún con co ro, ngại đi ra thảm cỏ ngoài sân; nguy cơ viêm phổi, bỏng lạnh đệm chân và nhịn tiểu kéo dài. Khi bị nhốt trong nhà nhiều giờ, cún sinh cuồng chân, sủa dai và cắn xé đồ đạc.`
                    : `极低温度导致幼犬排斥出门，极易引发受凉、肉垫冻伤及憋尿感染。长时间室内禁足导致幼犬精力过剩、焦虑吠叫并拆毁家具。`;
                salesPitch = isVi
                    ? `"Chào anh/chị [${{lead.name}}], em thấy khu vực ${{lead.city || lead.state}} đợt này nhiệt độ đang xuống tới ${{w.tempF}}°F. Bên em đang có giải pháp Khay Vệ Sinh Potty & Thảm Cỏ Nhân Tạo thoát nước ấm áp đặt ngay trong chuồng/phòng ấm cho cún con, kèm Đồ chơi ngứa răng xoa dịu stress khi cún bị nhốt trong nhà. Trại mình có muốn xem qua bảng giá sỉ và mẫu Take-Home Kit in logo riêng của trại không ạ?"`
                    : `"您好 [${{lead.name}}]，看到贵犬舍所在的 ${{lead.city || lead.state}} 当地气温已骤降至 ${{w.tempF}}°F。在极寒暴雪期，我们专为商业犬舍提供室内排水防咬人造草垫托盘套装，以及针对幼犬室内焦虑的安抚咬胶玩具。目前有针对犬舍专属定制的批量批发样包，请问可以发给您审阅一下吗？"`;
            }} else if (w.conditionType === 'rain') {{
                condTitle = isVi ? `🌧️ Mưa Ẩm Kéo Dài & Lầy Lội (${{w.tempF}}°F / ${{w.tempC}}°C)` : `🌧️ 阴雨连绵与泥泞天气 (${{w.tempF}}°F / ${{w.tempC}}°C)`;
                petBehavior = isVi
                    ? `Mưa ướt khiến lông cún bị bết dính bùn đất, phát sinh mùi hôi nồng nặc và nấm da. Chủ nuôi rất ngại dọn bãi cỏ tự nhiên ướt sũng.`
                    : `雨水导致幼犬毛发潮湿泥泞，极易滋生真菌皮肤病及严重异味。繁育者打理室外泥地极其耗时费力。`;
                salesPitch = isVi
                    ? `"Chào anh/chị, thời tiết mưa ẩm tại ${{lead.city || lead.state}} khiến việc dọn dẹp vệ sinh cho đàn cún con rất vất vả. Thảm cỏ nhân tạo chuyên dụng có màng thoát nước siêu tốc và kháng khuẩn bên em giúp chuồng trại khô ráo 100%, cún đi vệ sinh xong xịt nước là sạch ngay. Anh/chị xem qua bảng giá ưu đãi theo m2 chuồng trại nhé?"`
                    : `"您好，近期 ${{lead.city || lead.state}} 多雨潮湿，打理幼犬极易出现泥水异味。我们专供繁育犬舍的超快渗水人造草垫具备抗菌抗撕裂层，水冲即净，能彻底解决下雨天幼犬排泄和卫生难题。可以给您寄送一份犬舍规格方案吗？"`;
            }} else if (w.conditionType === 'hot') {{
                condTitle = isVi ? `☀️ Nắng Gắt & Nhiệt Cao (${{w.tempF}}°F / ${{w.tempC}}°C)` : `☀️ 高温烈日与地面炙热 (${{w.tempF}}°F / ${{w.tempC}}°C)`;
                petBehavior = isVi
                    ? `Mặt đường bê tông và sân ngoài trời hấp nhiệt trên 120°F gây bỏng đệm chân cún con; nguy cơ sốc nhiệt (heatstroke) đe dọa tính mạng cún.`
                    : `水泥地面受烈日暴晒温度超 120°F，极易烫伤幼犬肉垫；中午高温易诱发犬只中暑休克危险。`;
                salesPitch = isVi
                    ? `"Chào anh/chị, thời tiết nắng gắt trên ${{w.tempF}}°F tại ${{lead.city || lead.state}} khiến cún không thể chạy nhảy ngoài sân xi măng trưa hè. Thảm cỏ nhân tạo làm mát chống tia UV bên em lót góc râm mát là lựa chọn số 1 của các trại chó lớn tại California & Texas, kèm đồ chơi gặm nhai xoa dịu nhiệt. Em gửi bảng báo giá combo sỉ cho trại mình nhé?"`
                    : `"您好，${{lead.city || lead.state}} 目前气温高达 ${{w.tempF}}°F，烈日暴晒下幼犬无法在室外活动。我们在加州和德州顶级犬舍广泛普及的抗UV隔热人造草坪垫与冰感益智咬胶，是繁育基地的夏日标配。请问是否方便给您发送批发折扣表？"`;
            }} else {{
                condTitle = isVi ? `🌤️ Khí Hậu Dễ Chịu & Ôn Hòa (${{w.tempF}}°F / ${{w.tempC}}°C)` : `🌤️ 舒适宜人与交付旺季 (${{w.tempF}}°F / ${{w.tempC}}°C)`;
                petBehavior = isVi
                    ? `Thời tiết lý tưởng nhất trong năm để khách hàng đón cún về nhà mới (Puppy Adoption Peak Season). Nhu cầu mua trọn gói Starter Kit tăng vọt.`
                    : `全年最适宜幼犬新家交付的黄金旺季（Adoption Peak）。客户对一站式回家礼包（Starter Kit）需求最为强烈。`;
                salesPitch = isVi
                    ? `"Chào anh/chị [${{lead.name}}], mùa xuất chuồng này bên em đang cung cấp trọn gói Puppy Take-Home Kit (gồm thảm cỏ tập đi vệ sinh, khay lót và đồ chơi ôm ấm có mùi mẹ) in logo riêng của trại mình. Khi bán kèm cún con, trại mình vừa tăng thêm 15-20% giá trị cún, vừa giúp khách hàng chăm cún không lo tè bậy. Em gửi mẫu demo nhé?"`
                    : `"您好 [${{lead.name}}]，当前正是幼犬新家交付旺季。我们为优质犬舍专属定制一站式 Puppy Take-Home Kit（包含入厕训练草坪便垫、便盆与母犬气味心跳安抚玩具），支持定制印刷犬舍专属 Logo。既能增加 15-20% 溢价，又能提升买家口碑。方便给您发送样品包吗？"`;
            }}

            const modalBody = document.getElementById('modalContentBody');
            modalBody.innerHTML = `
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-card); border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                        <div>
                            <div style="font-weight: 800; font-size: 1.15rem; color: #ffffff;">${{lead.name}}</div>
                            ${{lead.owner ? `<div style="font-size: 0.825rem; color: #38bdf8; margin-top: 0.2rem;">👤 <b>${{isVi ? 'Chủ sở hữu / Đại diện:' : '所有者/业务代表:'}}</b> ${{lead.owner}}</div>` : ''}}
                            <div style="font-size: 0.825rem; color: var(--text-muted); margin-top: 0.2rem;">📍 ${{lead.city || ''}}, ${{lead.state || ''}} ${{lead.zip || ''}} • ${{lead.country || 'USA'}}</div>
                        </div>
                        <span class="badge badge-a">${{lead.rank_tier}} • ${{lead.score}}đ</span>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.75rem; background: rgba(0, 0, 0, 0.3); padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.75rem;">
                        <div><span style="font-size: 0.75rem; color: var(--text-muted);">${{t.weatherStation}}</span><b style="display: block; font-size: 0.85rem; color: #38bdf8;">${{w.cityName || lead.city || lead.state}}</b></div>
                        <div><span style="font-size: 0.75rem; color: var(--text-muted);">Nhiệt độ / Temp:</span><b style="display: block; font-size: 0.85rem; color: #f8fafc;">${{w.tempF}}°F / ${{w.tempC}}°C</b></div>
                        <div><span style="font-size: 0.75rem; color: var(--text-muted);">Độ ẩm / Humidity:</span><b style="display: block; font-size: 0.85rem; color: #10b981;">💧 ${{w.humidity}}%</b></div>
                        <div><span style="font-size: 0.75rem; color: var(--text-muted);">Gió / Wind:</span><b style="display: block; font-size: 0.85rem; color: #a5b4fc;">💨 ${{w.wind}} mph</b></div>
                    </div>

                    <div style="font-weight: 700; color: #38bdf8; font-size: 0.95rem; margin-bottom: 0.35rem;">${{condTitle}}</div>
                    <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 0.75rem;">
                        <b>${{t.weatherImpact}}</b> ${{petBehavior}}
                    </p>
                </div>

                <div style="margin-bottom: 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-weight: 700; color: #ffffff; font-size: 0.9rem;">${{t.weatherPitch}}</span>
                        <button class="btn btn-sky" style="padding: 0.3rem 0.65rem; font-size: 0.75rem;" onclick="copyPitchText()">${{t.modalCopy}}</button>
                    </div>
                    <div id="salesPitchContainer" style="background: rgba(15, 23, 42, 0.95); border-left: 4px solid #38bdf8; border-radius: 0 0.5rem 0.5rem 0; padding: 1rem; font-size: 0.875rem; color: #e2e8f0; line-height: 1.6; font-style: italic;">
                        ${{salesPitch}}
                    </div>
                </div>

                <div style="display: flex; justify-content: flex-end;">
                    <button class="btn btn-primary" onclick="closeWeatherModal()">${{t.modalClose}}</button>
                </div>
            `;

            document.getElementById('weatherModalOverlay').style.display = 'flex';
        }}

        function closeWeatherModal(e) {{
            document.getElementById('weatherModalOverlay').style.display = 'none';
        }}

        function copyPitchText() {{
            const el = document.getElementById('salesPitchContainer');
            if (!el) return;
            const text = el.innerText;
            navigator.clipboard.writeText(text).then(() => {{
                const t = i18n[currentLang];
                alert(t.modalCopied);
            }});
        }}

        // Native Excel (.XLSX) Export Function with Live Weather Trigger
        function exportSalesData() {{
            const isVi = currentLang === 'vi';
            const headers = isVi ? [
                'STT / Mã', 'Tên Đối Tác / Breeder Name', 'Chủ Sở Hữu / Đại Diện (Owner)', 'Điện Thoại / Phone', 'Email', 'Website',
                'Facebook URL', 'Địa Chỉ / Address', 'Thành Phố / City', 'Bang / State',
                'Mã Zip / Postal Code', 'Quốc Gia / Country',
                'Kênh Bán Amazon', 'Link Amazon Storefront / Wishlist', 'Gợi Ý Sản Phẩm',
                'Điểm Chuẩn (Score)', 'Phân Cấp (Tier)', 'Thời Tiết Real-Time & Kích Hoạt (Weather Trigger)',
                'Hành Động Đội Sales (Sales Action)'
            ] : [
                '序号', '客户名称', '所有者/业务代表', '联系电话', '商务邮箱', '官方网站',
                'Facebook主页', '详细地址', '城市', '州',
                '邮编', '国家',
                '亚马逊渠道状态', '亚马逊店铺链接', '推荐匹配产品',
                '综合评分', '客户评级', '实时天气与营销触发机制 (Weather Trigger)',
                '销售动作建议'
            ];

            const rows = filteredLeads.map(l => {{
                const locKey = l.zip || `${{l.city||''}}_${{l.state||''}}`;
                const w = weatherCache[locKey];
                const trg = getLeadWeatherTrigger(l, w);
                const weatherStr = `${{trg.icon}} ${{trg.label}}: ${{trg.pitch}}`;

                return [
                    l.stt,
                    l.name || '',
                    l.owner || '',
                    l.phone || '',
                    l.email || '',
                    l.website || '',
                    l.url || '',
                    l.address || '',
                    l.city || '',
                    l.state || '',
                    l.zip || '',
                    l.country || 'United States',
                    l.amz_cat || '',
                    l.amz_link || '',
                    l.product_fit || '',
                    l.score,
                    l.rank_tier,
                    weatherStr,
                    l.sales_action || ''
                ];
            }});

            const fileNamePrefix = isVi ? "Danh_Sach_Khach_Hang_Sales_Pet_Grass" : "美国狗舍潜客销售联络表";
            const dateStr = new Date().toISOString().slice(0, 10);

            if (typeof XLSX !== 'undefined') {{
                const aoa = [headers, ...rows];
                const wb = XLSX.utils.book_new();
                const ws = XLSX.utils.aoa_to_sheet(aoa);

                ws['!cols'] = [
                    {{ wch: 16 }}, // STT
                    {{ wch: 32 }}, // Name
                    {{ wch: 25 }}, // Owner
                    {{ wch: 18 }}, // Phone
                    {{ wch: 28 }}, // Email
                    {{ wch: 30 }}, // Web
                    {{ wch: 25 }}, // FB
                    {{ wch: 22 }}, // Addr
                    {{ wch: 16 }}, // City
                    {{ wch: 10 }}, // State
                    {{ wch: 12 }}, // Zip
                    {{ wch: 15 }}, // Country
                    {{ wch: 26 }}, // Amz Cat
                    {{ wch: 28 }}, // Amz Link
                    {{ wch: 25 }}, // Product
                    {{ wch: 12 }}, // Score
                    {{ wch: 12 }}, // Tier
                    {{ wch: 55 }}, // Weather
                    {{ wch: 38 }}  // Action
                ];

                XLSX.utils.book_append_sheet(wb, ws, isVi ? 'Khach_Hang_Sales' : '潜客销售列表');
                XLSX.writeFile(wb, `${{fileNamePrefix}}_${{dateStr}}.xlsx`);
            }} else {{
                const csvLines = [
                    "sep=,",
                    headers.map(h => `"${{h.replace(/"/g, '""')}}"`).join(','),
                    ...rows.map(r => r.map(c => `"${{String(c).replace(/"/g, '""')}}"`).join(','))
                ];
                const csvContent = "\\uFEFF" + csvLines.join('\\r\\n');
                const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${{fileNamePrefix}}_${{dateStr}}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }}
        }}

        // Initialize on DOM Ready
        window.addEventListener('DOMContentLoaded', () => {{
            setLanguage(currentLang);

            // Tier Chart
            new Chart(document.getElementById('tierChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Tier S (85-100)', 'Tier A (70-84)', 'Tier B (50-69)', 'Tier C (30-49)', 'Tier D (<30)'],
                    datasets: [{{
                        data: [102, 3025, 197, 872, 2134],
                        backgroundColor: ['#f59e0b', '#6366f1', '#10b981', '#94a3b8', '#f43f5e'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
                    }}
                }}
            }});

            // Amazon Credibility Chart
            new Chart(document.getElementById('amzChart'), {{
                type: 'bar',
                data: {{
                    labels: ['TARGET Kép (Cỏ + Đồ chơi)', 'Cỏ / Potty TARGET', 'Đồ chơi TARGET', 'Amazon khác', 'Chưa có Amz'],
                    datasets: [{{
                        label: 'Số website',
                        data: [13, 9, 3, 1, 3298],
                        backgroundColor: ['#f59e0b', '#10b981', '#6366f1', '#06b6d4', '#475569'],
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            type: 'logarithmic',
                            ticks: {{ color: '#94a3b8' }},
                            grid: {{ color: 'rgba(255,255,255,0.05)' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ display: false }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Recency Chart
            new Chart(document.getElementById('recencyChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Hot (≤ 3 ngày)', 'Warm (4-14 ngày)', 'Cool (15-30 ngày)', 'Cold (> 30 ngày)'],
                    datasets: [{{
                        label: 'Số lượng Leads',
                        data: [2898, 1043, 480, 1577],
                        backgroundColor: ['#f59e0b', '#10b981', '#06b6d4', '#475569'],
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Category Chart
            new Chart(document.getElementById('catChart'), {{
                type: 'pie',
                data: {{
                    labels: ['Dog Breeder / Kennel', 'Pet Care & Training', 'Pet Rescue / Shelter', 'Cá nhân / Community'],
                    datasets: [{{
                        data: [3242, 45, 37, 0],
                        backgroundColor: ['#10b981', '#6366f1', '#06b6d4', '#475569'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>"""

# Generate Vietnamese Dashboard
html_vi = generate_dashboard_html(default_lang='vi')
with open('Bao_Cao_Phan_Tich_Leads_Pet_Grass_Potty_Toys_2026.html', 'w', encoding='utf-8') as f:
    f.write(html_vi)
print(f"Generated Bao_Cao_Phan_Tich_Leads_Pet_Grass_Potty_Toys_2026.html (Size: {len(html_vi)} bytes)")

# Generate Chinese Dashboards
html_zh = generate_dashboard_html(default_lang='zh')
with open('Facebook潜客营销与RAG分析报告.html', 'w', encoding='utf-8') as f:
    f.write(html_zh)
with open('Facebook潜客营销与RAG分析报告_2026.html', 'w', encoding='utf-8') as f:
    f.write(html_zh)
print(f"Generated Facebook潜客营销与RAG分析报告.html and Facebook潜客营销与RAG分析报告_2026.html (Size: {len(html_zh)} bytes)")
print("ALL DASHBOARDS SUCCESSFULLY REBUILT WITH PER-USER DETAILS AND WEATHER MODALS!")
