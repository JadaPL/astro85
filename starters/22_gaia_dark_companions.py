# pip install astroquery matplotlib numpy
import numpy as np, matplotlib.pyplot as plt
from astroquery.gaia import Gaia

# Gaia DR3 astrometric binary orbits (Thiele-Innes constants A,B,F,G in mas, period in days)
query = """SELECT source_id, nss_solution_type, period, parallax, a_thiele_innes, b_thiele_innes, f_thiele_innes, g_thiele_innes
           FROM gaiadr3.nss_two_body_orbit WHERE a_thiele_innes IS NOT NULL AND parallax / parallax_error > 10"""
t = Gaia.launch_job_async(query).get_results().to_pandas()     # anonymous, ~1-3 min, <=~170k rows

A, B, F, G = (t[c + '_thiele_innes'] for c in 'abfg')
u, v = (A**2 + B**2 + F**2 + G**2) / 2, A * G - B * F
a0 = np.sqrt(u + np.sqrt(u**2 - v**2))                          # size of the star's orbital wobble [mas]
t['f_M'] = (a0 / t['parallax'])**3 / (t['period'] / 365.25)**2   # astrometric mass function [Msun]
cand = t[t['f_M'] > 3]               # a DARK companion must be heavier than f_M -> >3 Msun = black-hole territory
print(cand.sort_values('f_M', ascending=False).head(20)); print(t[t['source_id'] == 4373465352415301632])  # Gaia BH1

plt.scatter(t['period'], t['f_M'], s=1, c='gray', alpha=0.3, label=f'{len(t)} Gaia DR3 orbits')
plt.scatter(cand['period'], cand['f_M'], s=12, c='red', label=f'{len(cand)} with $f_M > 3\\,M_\\odot$')
plt.xscale('log'); plt.yscale('log'); plt.xlabel('Orbital period [days]'); plt.ylabel('Astrometric mass function [$M_\\odot$]')
plt.title('Hunting hidden black holes in Gaia DR3'); plt.legend()
plt.savefig('gaia_dark_companions.png', dpi=150, bbox_inches='tight')
