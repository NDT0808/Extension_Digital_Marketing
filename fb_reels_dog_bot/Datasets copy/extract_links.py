import pandas as pd

df = pd.read_csv('2026_10_02_v1_master.csv', dtype=str)
websites = df['websites'].dropna().tolist()
links = set()

for w in websites:
    for link in w.split(' | '):
        if link.strip():
            links.add(link.strip())

with open('sample_websites.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(list(links)[:100]))
print('Done!')
