# pip install requests pandas matplotlib
import io, requests, pandas as pd, matplotlib.pyplot as plt

# NASA Exoplanet Archive TAP: one row per confirmed planet (Planetary Systems Composite table)
q = ("select pl_name, pl_rade, pl_orbper, discoverymethod, disc_year from pscomppars "
     "where pl_rade is not null and pl_orbper is not null")
r = requests.get('https://exoplanetarchive.ipac.caltech.edu/TAP/sync', params={'query': q, 'format': 'csv'}, timeout=120)
df = pd.read_csv(io.StringIO(r.text))
df.to_csv('planets.csv', index=False)                  # snapshot so the plot is reproducible
print(len(df), 'planets with radius and period')

fig, ax = plt.subplots(figsize=(8, 6))
for method, g in df.groupby('discoverymethod'):
    if len(g) >= 10:
        ax.scatter(g.pl_orbper, g.pl_rade, s=4, label=f'{method} ({len(g)})')
ax.axhspan(1.5, 2.0, color='gray', alpha=0.2, label='radius valley (~1.5-2 Earth radii)')
ax.set(xscale='log', yscale='log', xlabel='Orbital period (days)', ylabel='Planet radius (Earth radii)')
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig('exoplanet_population.png', dpi=150)
