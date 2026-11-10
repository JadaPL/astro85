# pip install requests pandas matplotlib
import os, requests, pandas as pd, matplotlib.pyplot as plt

# DAWN JWST Archive merged NIRSpec table v4.4 (Zenodo, May 2025): 80,367 public JWST spectra, 133 MB
url = 'https://zenodo.org/records/15472354/files/dja_msaexp_emission_lines_v4.4.csv.gz?download=1'
fn = 'dja_msaexp_emission_lines_v4.4.csv.gz'
if not os.path.exists(fn):                                # download once (~1-3 min)
    open(fn, 'wb').write(requests.get(url, timeout=900).content)
df = pd.read_csv(fn, usecols=['root', 'srcid', 'ra', 'dec', 'z_best', 'grade'])
good = df[df.grade == 3].drop_duplicates(['root', 'srcid'])   # grade 3 = robust redshift
print(len(df), 'spectra |', len(good), 'robust redshifts |', (good.z_best > 10).sum(), 'galaxies at z > 10')

plt.hist(good.z_best, bins=70, range=(0, 14), log=True)
plt.xlabel('spectroscopic redshift z'); plt.ylabel('number of sources')
plt.title('Public JWST/NIRSpec redshifts (DJA v4.4, grade 3)')
plt.tight_layout()
plt.savefig('jwst_redshifts.png', dpi=150)
