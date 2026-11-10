# pip install requests pandas matplotlib
import io, requests, pandas as pd, matplotlib.pyplot as plt

# Curiosity SAM, experiment 25387 (sol 1546): "solid sample pyrolysis with GCMS", calibrated mass-spec counts (~15-20 MB text)
URL = ('https://pds-geosciences.wustl.edu/msl/msl-m-sam-2-rdr-l0-v1/mslsam_1xxx/data/'
       'eid25387/level1b/sm25387f1546rdr1b_spyr_qms_massdtc_2.tab')
df = pd.read_csv(io.StringIO(requests.get(URL, timeout=300).text), skipinitialspace=True, header=0,
                 names=['time', 'amu', 'pyro_T', 'gc_T', 'cps'], usecols=range(5))  # column order from the PDS4 .xml label
df['cps'] = pd.to_numeric(df['cps'], errors='coerce')
df['minutes'] = (df['time'] - df['time'].min()) / 60
print(df['amu'].round().value_counts().head(25))               # which m/z values did SAM scan?

plt.figure(figsize=(11, 5))
for mz, name in [(78, 'benzene'), (91, 'toluene'), (112, 'chlorobenzene')]:
    s = df[(df['amu'].round() == mz) & (df['cps'] > 0)]
    plt.plot(s['minutes'], s['cps'], lw=0.8, label=f'm/z {mz} ({name})')
plt.yscale('log'); plt.xlabel('Minutes since start of experiment'); plt.ylabel('Counts per second')
plt.title('Curiosity SAM pyrolysis GC-MS, sol 1546: extracted-ion traces'); plt.legend()
plt.tight_layout(); plt.savefig('mars_sam_gcms.png', dpi=150)
