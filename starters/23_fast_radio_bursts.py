# pip install pandas matplotlib numpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Second CHIME/FRB Catalog (Jan 2026): 4539 bursts from 3641 sources, Jul 2018 - Sep 2023 (one CSV, a few MB)
url = 'https://assets.chime-frb.ca/catalogs/catalog2/releases/20251231/data/chimefrbcat2.csv'
df = pd.read_csv(url)
df = df[df['sub_num'] == 0]                         # one row per burst (drop extra sub-burst rows)
rep = df['repeater_name'].notna()                   # repeater_name is blank for one-off bursts
print(len(df), 'bursts:', rep.sum(), 'from repeaters,', (~rep).sum(), 'one-offs')

bins = np.logspace(np.log10(50), np.log10(5000), 40)
plt.figure(figsize=(7, 5))
plt.hist(df.loc[~rep, 'dm_fitb'].dropna(), bins=bins, density=True, alpha=0.6, label='One-off bursts')
plt.hist(df.loc[rep, 'dm_fitb'].dropna(), bins=bins, density=True, alpha=0.6, label='Repeating sources')
plt.xscale('log'); plt.xlabel('Dispersion measure [pc cm$^{-3}$]  (more = farther / more gas)')
plt.ylabel('Fraction of bursts (normalized)'); plt.legend()
plt.title('CHIME/FRB Catalog 2: how far do fast radio bursts travel?')
plt.savefig('fast_radio_bursts.png', dpi=150, bbox_inches='tight')
