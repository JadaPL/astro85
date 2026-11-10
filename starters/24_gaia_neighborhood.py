# pip install astroquery matplotlib
import matplotlib.pyplot as plt
from astroquery.gaia import Gaia

query = """
SELECT bp_rp, phot_g_mean_mag + 5*LOG10(parallax) - 10 AS abs_g
FROM gaiadr3.gaia_source
WHERE parallax > 10 AND parallax_over_error > 10
  AND phot_bp_mean_flux_over_error > 10 AND phot_rp_mean_flux_over_error > 10
"""  # parallax > 10 mas  <=>  closer than 100 parsecs (~326 light-years)
stars = Gaia.launch_job_async(query).get_results().to_pandas()  # anonymous; takes ~1-3 minutes
print(len(stars), "stars within 100 pc")

plt.figure(figsize=(6, 7))
plt.hexbin(stars["bp_rp"], stars["abs_g"], gridsize=250, bins="log", cmap="viridis", mincnt=1)
plt.gca().invert_yaxis()
plt.xlabel("Colour BP - RP (blue  ->  red)"); plt.ylabel("Absolute G magnitude (bright  ->  up)")
plt.title("Hertzsprung-Russell diagram: Gaia DR3 stars within 100 pc")
plt.savefig("gaia_neighborhood.png", dpi=150)
