# pip install requests pandas matplotlib
import json, requests, pandas as pd, matplotlib.pyplot as plt
def get(path):   # NOAA SWPC JSON -> DataFrame (strips stray NUL bytes; -9999 means missing)
    txt = requests.get('https://services.swpc.noaa.gov/' + path, timeout=60).text.rstrip('\x00')
    df = pd.DataFrame(json.loads(txt)).replace(-9999, float('nan')); df['time'] = pd.to_datetime(df['time_tag']); return df
wind, mag = get('json/rtsw/rtsw_wind_1m.json'), get('json/rtsw/rtsw_mag_1m.json')   # 1-min data, ~last day, every L1 spacecraft
wind, mag = wind[wind['active'] == True], mag[mag['active'] == True]               # keep the operational spacecraft only
kp = get('products/noaa-planetary-k-index.json')                                     # 3-hourly Kp, ~last 7 days
fig, ax = plt.subplots(4, 1, figsize=(10, 10))
ax[0].plot(wind['time'], wind['proton_speed']); ax[0].set_ylabel('Speed (km/s)')
ax[1].plot(wind['time'], wind['proton_density']); ax[1].set_ylabel('Density (cm$^{-3}$)')
ax[2].plot(mag['time'], mag['bz_gsm']); ax[2].axhline(0, color='k', lw=0.5); ax[2].set_ylabel('Bz GSM (nT)')
ax[3].bar(kp['time'], kp['Kp'], width=0.12, color=['red' if v >= 5 else 'green' for v in kp['Kp']]); ax[3].set_ylabel('Kp (≥5 = storm)')
ax[0].set_title(f"Solar wind at L1 ({wind['source'].iloc[0]}, last ~24 h) and planetary K-index (last ~7 days)")
plt.tight_layout(); plt.savefig('space_weather.png', dpi=150)
