# pip install "sunpy[net]" matplotlib numpy
try:
    from _ensure import ensure_packages   # class repo: waits for the background install (starters/_ensure.py)
except ImportError:
    ensure_packages = lambda needed: None  # running this file on its own: use the pip line above
ensure_packages({"sunpy": "sunpy[net]", "drms": "sunpy[net]", "zeep": "sunpy[net]"})
import numpy as np, matplotlib.pyplot as plt
from sunpy.net import Fido, attrs as a
# Every GOES X-ray flare in the Heliophysics Events Knowledgebase (HEK) for 2024, near solar max (~1-3 min)
res = Fido.search(a.Time('2024-01-01', '2024-12-31 23:59'), a.hek.EventType('FL'), a.hek.OBS.Observatory == 'GOES')
t = res['hek']
events = set(zip([str(c).strip() for c in t['fl_goescls']], [str(p) for p in t['event_peaktime']]))  # drop duplicates
scale = {'A': 1e-8, 'B': 1e-7, 'C': 1e-6, 'M': 1e-5, 'X': 1e-4}      # W/m^2 for class 1.0 of each letter
flux = np.array([scale[c[0]] * float(c[1:]) for c, _ in events if c[:1] in scale and len(c) > 1])
n, edges = np.histogram(flux, bins=np.logspace(-7, -3, 25))
mid, dndf = np.sqrt(edges[1:] * edges[:-1]), n / np.diff(edges)       # flares per unit peak flux
fit = (mid > 1e-5) & (n > 0)                                           # fit M and X flares (small ones are under-counted)
slope, icpt = np.polyfit(np.log10(mid[fit]), np.log10(dndf[fit]), 1)
plt.loglog(mid[n > 0], dndf[n > 0], 'o', label=f'{len(flux)} GOES flares in 2024')
plt.loglog(mid[fit], 10**icpt * mid[fit]**slope, 'r-', label=f'power law fit: slope = {slope:.2f}')
plt.xlabel('Peak 1-8 Å X-ray flux (W/m²)'); plt.ylabel('dN/dF (flares per W/m²)'); plt.legend()
plt.savefig('flare_powerlaw.png', dpi=150)
