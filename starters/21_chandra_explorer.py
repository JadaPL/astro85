# pip install pyvo matplotlib numpy
import numpy as np
import matplotlib.pyplot as plt
import pyvo

# Chandra Source Catalog 2.2 (Chandra X-ray Center, SAO) via TAP: a box around the Orion Nebula Cluster (RA 83.82, Dec -5.39)
tap = pyvo.dal.TAPService('https://cda.cfa.harvard.edu/csc22tap')
query = """SELECT m.name, m.ra, m.dec, m.significance, m.flux_aper_b, m.hard_hm
           FROM csc22.master_source m
           WHERE m.ra BETWEEN 83.67 AND 83.97 AND m.dec BETWEEN -5.54 AND -5.24"""
t = tap.search(query, maxrec=20000).to_table().to_pandas().dropna()
print(len(t), 'X-ray sources with broad-band flux and hardness ratio')

fig, ax = plt.subplots(figsize=(7, 5))
sc = ax.scatter(t['flux_aper_b'], t['hard_hm'], c=np.log10(t['significance']), s=8, cmap='viridis')
ax.set(xscale='log', xlabel='Broad-band (0.5-7 keV) flux [erg cm$^{-2}$ s$^{-1}$]',
       ylabel='Hardness ratio (H-M)/(H+M)', title='Chandra X-ray sources in the Orion Nebula Cluster (CSC 2.2)')
fig.colorbar(sc, label='log$_{10}$ detection significance')
plt.savefig('chandra_explorer.png', dpi=150, bbox_inches='tight')
