# pip install pandas matplotlib
import pandas as pd
import matplotlib.pyplot as plt

# Cumulative Gravitational-Wave Transient Catalog (GWTC-1 ... GWTC-5.0) from GWOSC, one row per confident event
df = pd.read_csv('https://gwosc.org/eventapi/csv/GWTC/')
print(len(df), 'events;', df['catalog.shortName'].value_counts().to_dict())
df = df.dropna(subset=['mass_1_source', 'mass_2_source'])   # some O4b events have no published masses yet
print(len(df), 'events with masses')

fig, ax = plt.subplots(figsize=(7, 6))
sc = ax.scatter(df['mass_1_source'], df['mass_2_source'], c=df['luminosity_distance'], s=25, cmap='viridis')
ax.axvline(3, ls='--', c='gray')   # rough dividing line: neutron stars below ~3 Msun, black holes above
ax.axhline(3, ls='--', c='gray')
ax.set(xscale='log', yscale='log', xlabel='Primary mass $m_1$ [$M_\\odot$]',
       ylabel='Secondary mass $m_2$ [$M_\\odot$]', title='The stellar graveyard: every confident LVK merger')
fig.colorbar(sc, label='Luminosity distance [Mpc]')
plt.savefig('stellar_graveyard.png', dpi=150, bbox_inches='tight')
