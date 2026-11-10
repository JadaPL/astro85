# pip install requests pandas matplotlib
import os, requests, pandas as pd, matplotlib.pyplot as plt

URL = 'https://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT.gz'   # every known asteroid orbit (~100 MB gzipped)
if not os.path.exists('MPCORB.DAT.gz'):                                # download only once
    open('MPCORB.DAT.gz', 'wb').write(requests.get(URL, timeout=1800).content)
# fixed-width columns from the MPC orbit-format page: e = 71-79, a = 93-103, flags = 162-165, name = 167-194
df = pd.read_fwf('MPCORB.DAT.gz', colspecs=[(70, 79), (92, 103), (161, 165), (166, 194)],
                 names=['e', 'a', 'flags', 'name'], skiprows=43, dtype=str, compression='gzip')
df['a'], df['e'] = pd.to_numeric(df['a'], errors='coerce'), pd.to_numeric(df['e'], errors='coerce')
df = df.dropna(subset=['a', 'e'])                                      # drops any header/blank lines
neo = df['flags'].fillna('0').apply(int, base=16) & 0x0800 > 0         # MPC flag bit 11 = NEO
new = df['name'].str.startswith('2026', na=False)                     # provisional designations from 2026 (Rubin era)

plt.figure(figsize=(10, 6))
plt.scatter(df['a'], df['e'], s=0.05, c='0.6', rasterized=True, label=f'all {len(df):,} asteroids')
plt.scatter(df['a'][new], df['e'][new], s=0.3, c='tab:blue', rasterized=True, label=f'designated in 2026 ({new.sum():,})')
plt.scatter(df['a'][neo], df['e'][neo], s=0.3, c='tab:red', rasterized=True, label=f'near-Earth objects ({neo.sum():,})')
plt.xlim(0.5, 5.5); plt.ylim(0, 1); plt.xlabel('Semi-major axis a (au)'); plt.ylabel('Eccentricity e')
plt.legend(markerscale=20, loc='upper right'); plt.tight_layout(); plt.savefig('mpc_orbits.png', dpi=150)
