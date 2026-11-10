# pip install requests astropy matplotlib
import io, zipfile, requests, matplotlib.pyplot as plt
from astropy.io import ascii

# Zenodo data for "Identification of carbon dioxide in an exoplanet atmosphere" (JWST ERS team, Nature 2023), 375 kB zip
url = 'https://zenodo.org/records/6959427/files/JWST_ERS_1st_LOOK_PAPER_DATA.zip?download=1'
z = zipfile.ZipFile(io.BytesIO(requests.get(url, timeout=120).content))
print(z.namelist())                                       # explore the other reductions/models too
name = [n for n in z.namelist() if n.split('/')[-1] == 'EUREKA_REDUCTION.txt'][0]
t = ascii.read(z.read(name).decode())                     # columns: wavelength, bin_width, tr_depth, tr_depth_errneg, tr_depth_errpos, ...

plt.figure(figsize=(10, 4))
plt.errorbar(t['wavelength'], t['tr_depth'], yerr=t['tr_depth_errpos'], fmt='o', ms=3)
for mol, wl in {'H2O': 2.7, 'CH4': 3.3, 'SO2': 4.05, 'CO2': 4.3, 'CO': 4.6}.items():   # band centres (microns)
    plt.axvline(wl, color='gray', ls='--')
    plt.text(wl, plt.ylim()[1], mol, ha='center', va='bottom')
plt.xlabel('Wavelength (micron)'); plt.ylabel('Transit depth (Rp/R*)^2')
plt.title('WASP-39 b, JWST NIRSpec PRISM', pad=18)
plt.tight_layout()
plt.savefig('jwst_molecules.png', dpi=150)
