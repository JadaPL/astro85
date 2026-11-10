# pip install sparclclient matplotlib numpy
import matplotlib.pyplot as plt
from sparcl.client import SparclClient

client = SparclClient()                                   # public DESI DR1: no login needed
found = client.find(outfields=['sparcl_id', 'redshift', 'ra', 'dec'], limit=None,
                    constraints={'data_release': ['DESI-DR1'], 'spectype': ['QSO'], 'redshift': [2.4, 2.401]})
q = min(found.records, key=lambda r: r.sparcl_id)         # deterministic pick from the matches
s = client.retrieve(uuid_list=[q.sparcl_id], include=['wavelength', 'flux', 'model'], dataset_list=['DESI-DR1']).records[0]

plt.figure(figsize=(11, 4))
plt.plot(s.wavelength, s.flux, lw=0.4, color='gray', label='DESI flux')
plt.plot(s.wavelength, s.model, color='k', label='DESI pipeline model')
plt.ylim(min(0, s.model.min()), 1.4 * s.model.max())    # ignore noise spikes
for line, rest in {'Ly-alpha': 1215.67, 'C IV': 1549.06, 'C III]': 1908.73, 'Mg II': 2798.75}.items():
    plt.axvline(rest * (1 + q.redshift), color='r', ls='--')
    plt.text(rest * (1 + q.redshift), 0.92, line, color='r', transform=plt.gca().get_xaxis_transform())
plt.xlabel('observed wavelength (Angstrom)'); plt.ylabel('flux (1e-17 erg/s/cm2/A)')
plt.title(f'DESI DR1 quasar at z = {q.redshift:.3f} (RA {q.ra:.4f}, Dec {q.dec:.4f})'); plt.legend()
plt.tight_layout()
plt.savefig('quasar_spectrum.png', dpi=150)
