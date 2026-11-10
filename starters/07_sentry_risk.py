# pip install requests pandas matplotlib
import requests, pandas as pd, matplotlib.pyplot as plt

API = 'https://ssd-api.jpl.nasa.gov/sentry.api'
df = pd.DataFrame(requests.get(API, timeout=60).json()['data'])       # every object on the Sentry risk list
for col in ['ip', 'ps_cum', 'diameter']:
    df[col] = pd.to_numeric(df[col], errors='coerce')                  # API returns numbers as strings

plt.figure(figsize=(9, 5.5))
plt.scatter(df['ip'], df['ps_cum'], s=5 + 300 * df['diameter'].fillna(0), alpha=0.5)
for _, row in df.nlargest(5, 'ps_cum').iterrows():                    # label the 5 most "worrying"
    plt.annotate(row['fullname'].strip(), (row['ip'], row['ps_cum']), fontsize=8)
plt.xscale('log'); plt.xlabel('Cumulative impact probability'); plt.ylabel('Palermo scale (cumulative)')
plt.title(f'JPL Sentry risk list: {len(df)} objects (dot size = diameter)')
plt.tight_layout(); plt.savefig('sentry_risk.png', dpi=150)

yr4 = requests.get(API + '?des=2024%20YR4', timeout=60).json()        # case study: is 2024 YR4 still listed?
print('2024 YR4:', yr4.get('error', 'still on the list'), yr4.get('removed', yr4.get('summary', {}).get('ip')))
