# pip install lightkurve matplotlib numpy
import numpy as np, matplotlib.pyplot as plt
import lightkurve as lk

# TESS 2-minute light curve of WASP-18 (hot-Jupiter host), Sector 2, from MAST (a few MB)
# We use WASP-18's TESS Input Catalog number (TIC 100100827) instead of its name. Searching by
# name needs MAST's name-lookup service, whose certificate Python sometimes rejects in the
# cloud environment (CERTIFICATE_VERIFY_FAILED). The TIC number skips that step.
lc = lk.search_lightcurve('TIC 100100827', mission='TESS', author='SPOC', exptime=120, sector=2).download().remove_nans()
# Pass 1: remove slow trends (~30 h window), then Box Least Squares search over 0.5-5 day periods
pg = lc.flatten(window_length=901).to_periodogram(method='bls', period=np.linspace(0.5, 5, 20000),
                                                  duration=[0.05, 0.08, 0.1, 0.15])
P, t0 = pg.period_at_max_power, pg.transit_time_at_max_power
# Pass 2: re-flatten while ignoring in-transit points, so the trend fit does not eat the transit
flat = lc.flatten(window_length=901, mask=pg.get_transit_mask(duration=2 * pg.duration_at_max_power))
print('Best BLS period:', P)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
pg.plot(ax=ax1)                                            # BLS power vs trial period
flat.fold(period=P, epoch_time=t0).scatter(ax=ax2, s=1)    # phase-folded transit
ax2.set_xlim(-0.2, 0.2); ax2.set_title(f'WASP-18 b folded at P = {P.value:.4f} d')
plt.tight_layout()
plt.savefig('transit.png', dpi=150)
