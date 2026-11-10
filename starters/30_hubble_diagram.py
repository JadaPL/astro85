# pip install pandas astropy matplotlib numpy
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from astropy.cosmology import FlatLambdaCDM

# Pantheon+SH0ES: 1701 Type Ia supernova light curves (566 kB whitespace-separated text file on GitHub)
url = ('https://github.com/PantheonPlusSH0ES/DataRelease/raw/refs/heads/main/'
       'Pantheon+_Data/4_DISTANCES_AND_COVAR/Pantheon+SH0ES.dat')
sn = pd.read_csv(url, sep=r'\s+').query('zHD > 0.01')    # drop very nearby SNe (peculiar velocities)
# with dark energy (Pantheon+ best fit: 33% matter, 67% dark energy) vs. matter only (no dark energy)
lcdm, matter = FlatLambdaCDM(H0=73, Om0=0.334), FlatLambdaCDM(H0=73, Om0=1.0)
z = np.logspace(-2, np.log10(2.3), 200)

fig, (top, bot) = plt.subplots(2, 1, sharex=True, figsize=(7, 7))
top.errorbar(sn.zHD, sn.MU_SH0ES, yerr=sn.MU_SH0ES_ERR_DIAG, fmt='.', alpha=0.3, color='k')
bot.errorbar(sn.zHD, sn.MU_SH0ES - matter.distmod(sn.zHD.values).value, yerr=sn.MU_SH0ES_ERR_DIAG, fmt='.', alpha=0.3, color='k')
for cosmo, label in [(lcdm, 'with dark energy (LCDM)'), (matter, 'matter only')]:
    top.plot(z, cosmo.distmod(z).value, label=label)
    bot.plot(z, cosmo.distmod(z).value - matter.distmod(z).value)
top.set(xscale='log', ylabel='distance modulus mu (mag)'); top.legend()
bot.set(xlabel='redshift z', ylabel='mu - mu(matter only)')
plt.tight_layout()
plt.savefig('hubble_diagram.png', dpi=150)
