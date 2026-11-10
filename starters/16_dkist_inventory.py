# pip install dkist pandas matplotlib
try:
    from _ensure import ensure_packages   # class repo: waits for the background install (starters/_ensure.py)
except ImportError:
    ensure_packages = lambda needed: None  # running this file on its own: use the pip line above
ensure_packages({"sunpy": "sunpy[net]", "drms": "sunpy[net]", "zeep": "sunpy[net]", "dkist": "dkist"})
import dkist.net                     # registers the DKIST Data Center search with sunpy's Fido (no login needed)
import pandas as pd, matplotlib.pyplot as plt
from sunpy.net import Fido, attrs as a
rows = []
for page in range(1, 100):           # the archive returns datasets 300 per page
    t = Fido.search(a.Time('2022-01-01', '2026-12-31'), a.dkist.Page(page), a.dkist.PageSize(300))[0]
    if len(t) == 0: break
    rows += [dict(inst=r['Instrument'], start=str(r['Start Time']), nm=r['Wavelength'][0].to_value('nm'),
                  embargoed=r['Embargoed']) for r in t]
    if len(rows) >= t.total_available_results: break
df = pd.DataFrame(rows); df['start'] = pd.to_datetime(df['start'])
print(len(df), 'datasets'); print(df.groupby(['inst', 'embargoed']).size())   # public vs. embargoed per instrument
fig, ax = plt.subplots(figsize=(10, 5))
for inst, g in df.groupby('inst'): ax.scatter(g['start'], g['nm'], s=12, alpha=0.6, label=inst)
ax.set(yscale='log', xlabel='Observation start (UT)', ylabel='Wavelength (nm)', title='Every DKIST Level-1 dataset in the archive')
ax.legend(); plt.savefig('dkist_inventory.png', dpi=150)
