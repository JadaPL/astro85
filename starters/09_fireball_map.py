# pip install requests pandas numpy matplotlib
import requests, numpy as np, pandas as pd, matplotlib.pyplot as plt

js = requests.get('https://ssd-api.jpl.nasa.gov/fireball.api', params={'req-loc': 'true'}, timeout=60).json()
df = pd.DataFrame(js['data'], columns=js['fields'])
df['lat'] = df['lat'].astype(float) * np.where(df['lat-dir'] == 'S', -1, 1)   # API gives 8.0 + 'S'
df['lon'] = df['lon'].astype(float) * np.where(df['lon-dir'] == 'W', -1, 1)
df['kt'] = df['impact-e'].astype(float)                                       # impact energy, kilotons of TNT

ax = plt.figure(figsize=(11, 6)).add_subplot(projection='mollweide')
sc = ax.scatter(np.radians(df['lon']), np.radians(df['lat']), s=4 + 20 * np.sqrt(df['kt']),
                c=np.log10(df['kt']), cmap='plasma', alpha=0.7, edgecolors='k', linewidths=0.2)
plt.colorbar(sc, label='log10 impact energy (kilotons TNT)', shrink=0.6)
big = df.loc[df['kt'].idxmax()]
ax.set_title(f"{len(df)} located fireballs {df['date'].min()[:4]}-{df['date'].max()[:4]} (largest: {big['kt']:.0f} kt, {big['date'][:10]})")
ax.grid(True); plt.savefig('fireball_map.png', dpi=150)
