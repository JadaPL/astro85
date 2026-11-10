# pip install gwpy matplotlib requests
import os
import requests
from gwpy.timeseries import TimeSeries

gps = 1126259462.4   # GW150914 merger time (GPS seconds)

# 32 s of LIGO-Livingston strain around the merger (GWOSC's event file, about 1 MB).
# Data source: Gravitational Wave Open Science Center (GWOSC), https://gwosc.org
URL = ('https://gwosc.org/eventapi/json/GWTC-1-confident/GW150914/v3/'
       'L-L1_GWOSC_4KHZ_R1-1126259447-32.hdf5')

# Why we download the file ourselves instead of using TimeSeries.fetch_open_data:
# gwosc.org's security certificate is signed by "emSign Root CA - G1". Python's
# built-in certificate list (the certifi package) doesn't include that authority,
# so gwpy's download stopped with CERTIFICATE_VERIFY_FAILED. The operating system's
# certificate list does include it, so we tell requests to use that one.
# This keeps the security check switched on; it only changes which list is used.
SYSTEM_CERTS = '/etc/ssl/certs/ca-certificates.crt'   # Linux / cloud environment
verify = SYSTEM_CERTS if os.path.exists(SYSTEM_CERTS) else True

os.makedirs('data', exist_ok=True)
path = os.path.join('data', os.path.basename(URL))
if not os.path.exists(path):          # download once, then reuse the cached copy
    r = requests.get(URL, verify=verify, timeout=60)
    r.raise_for_status()
    with open(path, 'wb') as f:
        f.write(r.content)

data = TimeSeries.read(path, format='hdf5.gwosc')

q = data.q_transform(outseg=(gps - 0.5, gps + 0.2), frange=(20, 500))   # whitened time-frequency map
plot = q.plot(figsize=(8, 4))
ax = plot.gca()
ax.set_xscale('seconds'); ax.set_epoch(gps)          # time axis = seconds relative to the merger
ax.set_yscale('log'); ax.set_ylim(20, 500); ax.set_ylabel('Frequency [Hz]')
ax.set_title('GW150914 at LIGO Livingston: two black holes merging')
ax.colorbar(cmap='viridis', label='Normalized energy')
plot.savefig('hear_a_merger.png', dpi=150, bbox_inches='tight')

# Bonus: make it audible -> whiten, keep 30-400 Hz, 3 s around the merger, save as WAV
data.whiten(4, 2).bandpass(30, 400).crop(gps - 2, gps + 1).write('GW150914.wav')
