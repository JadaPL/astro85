# pip install requests pandas matplotlib
import io, requests, pandas as pd, matplotlib.pyplot as plt
# SILSO monthly mean total sunspot number, 1749-now (semicolon-separated, no header row)
txt = requests.get('https://sidc.be/SILSO/INFO/snmtotcsv.php', timeout=60).text
ssn = pd.read_csv(io.StringIO(txt), sep=';', header=None, names=['year', 'month', 'decyear', 'ssn', 'std', 'nobs', 'final'])
ssn['smooth'] = ssn['ssn'].rolling(13, center=True).mean()          # simple 13-month running mean
swpc = 'https://services.swpc.noaa.gov/json/solar-cycle/'
panel = pd.DataFrame(requests.get(swpc + 'solar-cycle-25-predicted.json', timeout=60).json())  # 2019 NOAA/NASA panel forecast
now = pd.DataFrame(requests.get(swpc + 'predicted-solar-cycle.json', timeout=60).json())       # SWPC's current forecast
yr = lambda tags: pd.to_datetime(tags).dt.year + (pd.to_datetime(tags).dt.month - 0.5) / 12  # "2026-05" -> 2026.375
fig, (top, bot) = plt.subplots(2, 1, figsize=(10, 8))
for ax in (top, bot): ax.plot(ssn.decyear, ssn.ssn, color='0.7', lw=0.5, label='SILSO monthly'); ax.plot(ssn.decyear, ssn.smooth, 'k', label='13-month mean')
bot.plot(yr(panel.time_tag), panel.smoothed_ssn, 'b--', label='2019 panel forecast')
bot.plot(yr(now['time-tag']), now.predicted_ssn, 'r', label='SWPC forecast (latest)')
bot.fill_between(yr(now['time-tag']), now.low_ssn, now.high_ssn, color='r', alpha=0.2)
top.set(ylabel='Sunspot number', title='Sunspot cycles since 1749 (SILSO) and Cycle 25 vs. forecasts (NOAA SWPC)')
bot.set(xlim=(2008, 2031), xlabel='Year', ylabel='Sunspot number'); bot.legend()
plt.tight_layout(); plt.savefig('solar_cycle.png', dpi=150)
