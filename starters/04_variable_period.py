# pip install requests pandas numpy astropy matplotlib
import io, requests, numpy as np, pandas as pd, matplotlib.pyplot as plt
from astropy.timeseries import LombScargle

# V782 Cyg: an RR Lyrae star in the Kepler field; Kepler measured P = 0.52364 d (Benko et al. 2010)
url = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
params = {"POS": "CIRCLE 297.82083 40.44589 0.0006", "BANDNAME": "r", "FORMAT": "CSV"}  # 2-arcsec cone
lc = pd.read_csv(io.StringIO(requests.get(url, params=params, timeout=300).text))
lc = lc[lc["catflags"] == 0]  # keep only clean measurements (hjd = heliocentric Julian Date)

freq, power = LombScargle(lc["hjd"], lc["mag"], lc["magerr"]).autopower(minimum_frequency=0.5, maximum_frequency=5)
period = 1 / freq[np.argmax(power)]
phase = (lc["hjd"] / period) % 1
plt.errorbar(np.r_[phase, phase + 1], np.r_[lc["mag"], lc["mag"]], yerr=np.r_[lc["magerr"], lc["magerr"]], fmt=".", ms=3, alpha=0.5)
plt.gca().invert_yaxis()
plt.xlabel("Phase (two cycles shown)"); plt.ylabel("ZTF r magnitude")
plt.title(f"V782 Cyg folded at best period {period:.5f} d (Kepler: 0.52364 d)")
plt.savefig("variable_period.png", dpi=150)
