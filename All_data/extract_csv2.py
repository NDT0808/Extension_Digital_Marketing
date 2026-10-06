import re
log_path = r"C:\Users\ASUS\.gemini\antigravity-ide\brain\fdb1fb66-ac9b-4683-9c21-54c94229d16a\.system_generated\logs\transcript_full.jsonl"
out_path = r"c:\Users\ASUS\Downloads\plugin-support-main\dataset_chinese_new.csv"

with open(log_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Handle literal \n or actual \n in JSON content
content = content.replace('\\n', '\n').replace('\\"', '"')

lines = content.split('\n')
csv_lines = []
for line in lines:
    line = line.strip()
    if line.startswith('"序号"') or re.match(r'^"\d+",', line):
        csv_lines.append(line)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(csv_lines))

print(f"Extracted {len(csv_lines)} lines")
