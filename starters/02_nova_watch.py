# pip install requests pandas matplotlib
#
# This project needs a FREE AAVSO API key. To get one:
#   1. Go to https://www.aavso.org and click "Login" in the top navigation bar.
#   2. Click "Sign Up" at the bottom of the login form.
#   3. Fill in the information it asks for, then confirm your account using the email AAVSO sends you.
#   4. Go to your account settings (currently https://apps.aavso.org/v2/accounts/settings/)
#      and click "Request Key" under "API Access".
#   5. A new tab opens showing the key in JSON, for example:
#          {"token": "123412341234123412341234123412341234"}
#      Your key is the long string of letters and digits after "token": (without the quotes).
#   6. Add the key to YOUR OWN Claude cloud environment as an environment variable:
#          AAVSO_TOKEN=123412341234123412341234123412341234
#      (in Claude Code on the web or the app, open the cloud environment menu in the session's title bar,
#      choose Edit, and add it under environment variables; then start a new session so it takes effect).
#      Never paste the key into a chat with Claude.
#      Use a personal environment, never a shared one, and never put the key in a file you commit.
#      (Running on your own computer instead? In Terminal:  export AAVSO_TOKEN="paste-your-key")
import os, sys, time, requests, pandas as pd, matplotlib.pyplot as plt

if not os.environ.get("AAVSO_TOKEN"):
    sys.exit("AAVSO_TOKEN is not set. See the steps at the top of this script to get a free AAVSO API key.")

star, since = "T CrB", "2025-01-01"  # or: star, since = "V1452 Tau", "2026-08-01"
url = "https://apps.aavso.org/v2/api/observations/photometry/"  # docs: https://docs.aavso.org/observations
headers = {"Authorization": "Token " + os.environ["AAVSO_TOKEN"]}
rows = []
for page in range(1, 21):  # AAVSO asks for at most 1 request every 10 s
    r = requests.get(url, headers=headers, params={"target": star, "band": 2, "start_date": since, "page": page}, timeout=60)
    r.raise_for_status()  # stops with a clear error if the token or URL is wrong
    rows += r.json()["results"]
    if not r.json()["next"]: break  # no more pages
    time.sleep(10)
df = pd.DataFrame(rows)  # band 2 = Johnson V
dates = pd.to_datetime(df["jd_dbl"] - 2440587.5, unit="D")  # Julian Date -> calendar date
plt.scatter(dates, pd.to_numeric(df["magnitude"], errors="coerce"), s=4)
plt.gca().invert_yaxis()  # brighter = up
plt.ylabel("V magnitude"); plt.title(f"{star}: AAVSO V-band observations")
plt.savefig("nova_watch.png", dpi=150)
