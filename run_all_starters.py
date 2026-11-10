"""Run every astronomy starter script and report which ones work.

Usage (from the repo root; in a cloud session, just ask Claude to run it):
    pip install -r requirements.txt        # not needed in the class cloud environment (setup script + SessionStart hook)
    python3 run_all_starters.py            # all 30 (~10-20 min; a few downloads are ~100 MB)
    python3 run_all_starters.py 07 15      # just some, by project number

Each script runs in its own folder under ./test_runs/ with a time limit.
PASS = exited cleanly and saved its plot. Plots are left in ./test_runs/<ID>/ to look at.
Project 02 (AAVSO) is skipped unless AAVSO_TOKEN is set (it needs a free account).
"""
import os, sys, glob, time, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 900  # seconds per script
scripts = sorted(glob.glob(os.path.join(HERE, 'starters', '[0-3][0-9]_*.py')))
if len(sys.argv) > 1:
    scripts = [s for s in scripts if os.path.basename(s)[:2] in sys.argv[1:]]

env = dict(os.environ, MPLBACKEND='Agg')  # no plot windows
results = []
for path in scripts:
    sid, name = os.path.basename(path)[:2], os.path.basename(path)
    if sid == '02' and not os.environ.get('AAVSO_TOKEN'):
        results.append((name, 'SKIP', 'set AAVSO_TOKEN to test (free AAVSO account)', 0))
        print(f'SKIP {name}'); continue
    run_dir = os.path.join(HERE, 'test_runs', sid)
    shutil.rmtree(run_dir, ignore_errors=True); os.makedirs(run_dir)
    shutil.copy(path, run_dir)
    for helper in glob.glob(os.path.join(HERE, 'starters', '_*.py')):  # shared helpers, e.g. _ensure.py
        shutil.copy(helper, run_dir)
    print(f'RUN  {name} ...', flush=True)
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, name], cwd=run_dir, env=env, capture_output=True, text=True, timeout=TIMEOUT)
        pngs = glob.glob(os.path.join(run_dir, '*.png'))
        ok = p.returncode == 0 and pngs
        err = (p.stderr.strip().splitlines() or ['no plot saved'])[-1]
        results.append((name, 'PASS' if ok else 'FAIL', '' if ok else err[:160], time.time() - t0))
        open(os.path.join(run_dir, 'output.log'), 'w').write(p.stdout + '\n--- stderr ---\n' + p.stderr)
    except subprocess.TimeoutExpired:
        results.append((name, 'FAIL', f'timed out after {TIMEOUT} s', time.time() - t0))
    print(f'     {results[-1][1]} ({results[-1][3]:.0f} s) {results[-1][2]}', flush=True)

print('\n==== Summary ====')
for name, status, msg, secs in results:
    print(f'{status:4}  {name:32} {secs:6.0f} s  {msg}')
print(f"\n{sum(r[1] == 'PASS' for r in results)} passed, {sum(r[1] == 'FAIL' for r in results)} failed, "
      f"{sum(r[1] == 'SKIP' for r in results)} skipped. Full logs: test_runs/<ID>/output.log")
