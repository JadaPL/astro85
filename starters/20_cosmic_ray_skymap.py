# pip install pandas matplotlib astropy
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord

# Pierre Auger Observatory: catalog of its highest-energy cosmic rays, 2004-2020 (energy in EeV = 1e18 eV)
df = pd.read_csv('https://opendata.auger.org/catalog/list/auger_catalogSD.csv')
famous = {'Amaterasu (Telescope Array, ~244 EeV)': (255.9, 16.1), "Oh-My-God (Fly's Eye, ~320 EeV)": (85.2, 48.0),
          'Centaurus A (nearby radio galaxy)': (201.37, -43.02)}            # (RA, Dec) in degrees

def galactic(ra, dec):   # RA/Dec (deg) -> Galactic lon/lat (radians), longitude increasing to the left
    g = SkyCoord(ra, dec, unit='deg').galactic
    return -g.l.wrap_at('180d').radian, g.b.radian

fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={'projection': 'mollweide'})
sc = ax.scatter(*galactic(df['ra'], df['dec']), c=df['energy'], s=df['energy'] / 2, cmap='plasma')
for name, (ra, dec) in famous.items():
    ax.plot(*galactic(ra, dec), '*', ms=14, label=name)
ax.set_xticks(np.radians(range(-150, 151, 30)), labels=[f'{-t % 360}°' for t in range(-150, 151, 30)])
ax.grid(True); ax.legend(loc='lower right', fontsize=7); ax.set_title('Highest-energy cosmic rays (Galactic plane = equator)', pad=20)
fig.colorbar(sc, orientation='horizontal', shrink=0.5, label='Energy [EeV]')
plt.savefig('cosmic_ray_skymap.png', dpi=150, bbox_inches='tight')
