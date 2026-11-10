# pip install pandas matplotlib
import pandas as pd, matplotlib.pyplot as plt

url = "https://planet4589.org/space/gcat/tsv/cat/satcat.tsv"  # GCAT, every tracked object since 1957 (~tens of MB, updated daily)
df = pd.read_csv(url, sep="\t", dtype=str, quoting=3)  # tab-separated; quoting=3 treats " as plain text
pay = df[df["Type"].str.startswith("P", na=False)].copy()  # Type starting with P = payload (a satellite or probe)
pay["year"] = pd.to_numeric(pay["LDate"].str[:4], errors="coerce")  # LDate looks like "2019 May 24 0230"
pay["starlink"] = pay["Name"].str.contains("Starlink", case=False, na=False)
n = pay.groupby(["year", "starlink"]).size().unstack(fill_value=0)

plt.figure(figsize=(10, 4.5))
plt.bar(n.index, n[False], color="gray", label="All other payloads")
plt.bar(n.index, n[True], bottom=n[False], color="tab:red", label="Starlink")
plt.xlabel("Launch year"); plt.ylabel("Payloads launched")
plt.title("Satellites launched per year (GCAT, J. McDowell)"); plt.legend()
plt.savefig("satellites.png", dpi=150)
