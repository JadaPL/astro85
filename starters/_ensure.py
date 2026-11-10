"""Shared setup for starters 03, 13, 14 and 16: make sure the packages they need are installed.

In cloud sessions, the repo's SessionStart hook (.claude/hooks/session-start.sh) installs the
solar and DASCH packages in the background. ensure_packages() waits for that install to finish,
then pip-installs anything still missing. On your own computer it just installs what's missing.
"""
import importlib, importlib.util, os, subprocess, sys, tempfile


def ensure_packages(needed):
    """needed maps module name -> pip package name, e.g. {"daschlab": "daschlab"}."""
    try:
        import fcntl  # file locks, to wait for the background install (not available on Windows)
        lock = open(os.path.join(tempfile.gettempdir(), "cs85-extras.lock"), "a")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Waiting for the background install of the solar and DASCH packages...", flush=True)
            fcntl.flock(lock, fcntl.LOCK_EX)
    except ImportError:
        lock = None
    importlib.invalidate_caches()
    missing = sorted({pkg for mod, pkg in needed.items() if importlib.util.find_spec(mod) is None})
    if missing:
        print("Installing", ", ".join(missing), "(about a minute)...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", *missing], check=True)
    if lock:
        lock.close()  # done: let other scripts (or the background install) go ahead
