# pip install daschlab matplotlib
try:
    from _ensure import ensure_packages   # class repo: waits for the background install (starters/_ensure.py)
except ImportError:
    ensure_packages = lambda needed: None  # running this file on its own: use the pip line above
ensure_packages({"daschlab": "daschlab"})
import matplotlib.pyplot as plt
from daschlab import open_session

sess = open_session(source="T CrB")  # makes a folder daschlab_t_crb/ that caches all downloads
sess.select_target(name="T CrB").select_refcat("apass")
lc = sess.lightcurve(0)  # 0 = catalog star closest to the target
lc.apply_standard_rejections()  # flag known-bad plate measurements
det, lim = lc.drop.rejected(verbose=False).split_by.detected()

plt.figure(figsize=(10, 4))
plt.scatter(lim["time"].jyear, lim["limiting_mag_local"], marker="v", s=6, c="lightgray", label="not seen (fainter than)")
plt.scatter(det["time"].jyear, det["magcal_magdep"], s=4, c="k", label="measured")
plt.gca().invert_yaxis()
plt.xlabel("Year"); plt.ylabel("Calibrated magnitude (blue plates)")
plt.title("T Coronae Borealis on Harvard glass plates (DASCH DR7)"); plt.legend()
plt.savefig("dasch_century.png", dpi=150)
