# pip install requests pandas numpy matplotlib
import requests, numpy as np, pandas as pd, matplotlib.pyplot as plt

# Every known near-Earth object passing within 0.05 au (~19.5 Moon distances) of Earth in the next 365 days
params = {'date-min': 'now', 'date-max': '+365', 'dist-max': '0.05', 'fullname': 'true'}
js = requests.get('https://ssd-api.jpl.nasa.gov/cad.api', params=params, timeout=60).json()
df = pd.DataFrame(js['data'], columns=js['fields'])
df['date'] = pd.to_datetime(df['cd'], format='%Y-%b-%d %H:%M')
df['dist_LD'] = df['dist'].astype(float) * 149597870.7 / 384400          # au -> lunar distances
df['size_m'] = 1329e3 / np.sqrt(0.14) * 10 ** (-df['h'].astype(float) / 5)  # size estimate from H (albedo 0.14)

plt.figure(figsize=(10, 5))
sc = plt.scatter(df['date'], df['dist_LD'], s=np.clip(df['size_m'] / 5, 4, 400), c=np.log10(df['size_m']), cmap='viridis', alpha=0.7)
plt.colorbar(sc, label='log10 estimated diameter (m)')
plt.axhline(1, color='gray', ls='--', label='distance of the Moon')
plt.ylabel('Miss distance (lunar distances)'); plt.legend()
plt.title(f'{len(df)} near-Earth-object close approaches in the next year')
plt.tight_layout(); plt.savefig('close_approach.png', dpi=150)
