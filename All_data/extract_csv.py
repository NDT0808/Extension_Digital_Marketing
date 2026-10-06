import json
import re
import pandas as pd

log_path = r"C:\Users\ASUS\.gemini\antigravity-ide\brain\fdb1fb66-ac9b-4683-9c21-54c94229d16a\.system_generated\logs\transcript_full.jsonl"

csv_lines = []
with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
csv_lines = []
for line in lines:
    data = json.loads(line)
    if data.get('type') == 'USER_INPUT':
        content = data.get('content', '')
        for text_line in content.split('\n'):
            text_line = text_line.strip()
            if text_line.startswith('"序号"') or re.match(r'^"\d+",', text_line):
                csv_lines.append(text_line)

out_file = 'c:\\Users\\ASUS\\Downloads\\plugin-support-main\\dataset_chinese_new.csv'
with open(out_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(csv_lines))

print(f"Extracted {len(csv_lines)} lines to {out_file}")
