# pip install astroquery matplotlib
from astroquery.jplhorizons import Horizons
import matplotlib.pyplot as plt
import numpy as np

# Note (Nov 2026): Horizons' .vectors() currently returns empty tables (no x, y, z columns) through astroquery,
# so this script uses .ephemerides() instead: distance from the Sun (r) plus ecliptic longitude and latitude,
# turned into x, y below. Same positions, same plot.

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
year = {'start': '2025-06-01', 'stop': '2026-06-01', 'step': '2d'}
# Left: 3I/ATLAS (= comet C/2025 N1) vs Earth (399) and Mars (499), Sun-centred, ecliptic plane
for label, hid, idtype in [('3I/ATLAS', 'C/2025 N1', 'designation'), ('Earth', '399', None), ('Mars', '499', None)]:
    e = Horizons(id=hid, id_type=idtype, location='@sun', epochs=year).ephemerides(
        quantities='18,19', closest_apparition=(idtype == 'designation'))  # 18 = heliocentric ecliptic lon/lat, 19 = r
    lon, lat = np.radians(e['EclLon']), np.radians(e['EclLat'])
    ax1.plot(e['r'] * np.cos(lat) * np.cos(lon), e['r'] * np.cos(lat) * np.sin(lon), label=label)
ax1.plot(0, 0, 'y*', ms=15); ax1.set_aspect('equal'); ax1.legend(); ax1.set_xlabel('x (au)'); ax1.set_ylabel('y (au)')
# Right: Apophis (99942) distance from Earth's centre around 13 Apr 2029, every 10 minutes
ap = Horizons(id='99942', id_type='smallbody', location='500@399',
              epochs={'start': '2029-04-12', 'stop': '2029-04-15', 'step': '10m'}).ephemerides(quantities='20')  # 20 = delta (distance from observer)
hours = (ap['datetime_jd'] - ap['datetime_jd'][ap['delta'].argmin()]) * 24
ax2.plot(hours, ap['delta'] * 149597870.7, label='Apophis'); ax2.axhline(42164, ls='--', c='gray', label='geostationary satellites')
ax2.set_yscale('log'); ax2.set_xlabel('Hours from closest approach (2029 Apr 13)'); ax2.set_ylabel('Distance from Earth centre (km)'); ax2.legend()
plt.tight_layout(); plt.savefig('interstellar_apophis.png', dpi=150)
