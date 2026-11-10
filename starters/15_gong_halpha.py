# pip install requests astropy numpy matplotlib
import re, io, requests, numpy as np, matplotlib.pyplot as plt
from astropy.io import fits
day = '20260830'   # NSO's GONG blog featured a large filament this day; any date since 2010 works
base = f'https://gong2.nso.edu/ftp/HA/haf/{day[:6]}/{day}/'           # science-grade FITS, 1/min/site
names = sorted(set(re.findall(r'\d{14}[A-Z]h\.fits\.fz', requests.get(base, timeout=60).text)))
print(len(names), 'images that day, e.g.', names[:3])
name = names[len(names) // 2]                                          # pick one from mid-day
img = fits.getdata(io.BytesIO(requests.get(base + name, timeout=120).content)).astype(float)
lo, hi = np.percentile(img[img > 0], [1, 99.7])                        # contrast stretch
plt.figure(figsize=(7, 7)); plt.imshow(img, origin='lower', cmap='gray', vmin=lo, vmax=hi)
plt.title(f'GONG H-alpha {name[:4]}-{name[4:6]}-{name[6:8]} {name[8:10]}:{name[10:12]} UT (site {name[14]})')
plt.axis('off'); plt.savefig('gong_halpha.png', dpi=150)
