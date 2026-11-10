# CS85 astronomy teaser projects

Run your project in the cloud with Claude Code: nothing to install on your laptop. **[PROJECTS.md](PROJECTS.md) describes all 30 projects**, and each project's number matches its starter file in `starters/`.

## One-time setup (about 10 minutes)

1. **Make your own copy of this repo.** Visit the main page of the repo at https://github.com/ChristopherThorpe/cs85-astro-template, click the green **Use this template** button in the upper right, then **Create a new repository** under your own GitHub account. Public is simplest.
2. **Let Claude use it.** Install the Claude GitHub App on your account at https://github.com/apps/claude/installations/new and give it access to your new repo.
3. **Connect GitHub to Claude.** Go to https://claude.ai/code, sign in with your Harvard Claude account, and follow the prompt to connect GitHub.
4. **Create the class environment.** At claude.ai/code, click the cloud icon above the message box, then **Add cloud environment**, and fill it in:
   - **Name:** `CS85 Astronomy`
   - **Network access:** **Full**. The projects pull data from about 30 different science archives, and the default **Limited** setting only reaches package installers and GitHub.
   - **Setup script:** paste the contents of `setup_script.sh`.
   - Click **Create**.

## Each work session
Before beginning, take a look at the **30 starter projects** in https://github.com/ChristopherThorpe/cs85-astro-template/blob/main/PROJECTS.md

At claude.ai/code, pick your repo and the **CS85 Astronomy** environment, then ask something like:

> Run starters/07_sentry_risk.py, save the plot to plots/, and explain what it shows.

Your first session takes a few extra minutes while packages install. After that, sessions start quickly. A few projects (03, 13, 14 and 16) may print "Waiting for the background install..." the first time you run them in a session. That's normal and takes a minute or two.

**Seeing your plots:** Claude pushes its work to a branch. On GitHub, switch to that branch and open the `plots/` folder. GitHub shows the images right in the browser.

## If something goes wrong

- **`CERTIFICATE_VERIFY_FAILED` or `SSLCertVerificationError`:** most likely in projects 18, 19 and 25, occasionally others. Some data sites use certificates from an authority called emSign that the cloud machine doesn't trust by default. This repo's start-up script usually fixes that, but not every time. Ask Claude: *"Fix the emSign certificate error as described in CLAUDE.md and rerun the starter."* Watch what it does: the right fix adds the certificate stored in this repo. **Don't accept a "fix" that turns certificate checking off** (for example `verify=False`); stop Claude and ask again.
- **A download fails with 403 or "proxy":** check that your environment's network access is set to **Full**, not Limited, then start a new session.
- **"Claude Code isn't available on your account"** or **no GitHub sign-in button:** tell your instructor. That's an account setting, not something you did wrong.
- **Project 30 (Hubble diagram) fails with "HTTP Error 403: Forbidden":** the supernova data lives in a separate public GitHub repo, `PantheonPlusSH0ES/DataRelease`, and each Claude session can only read the GitHub repos added to it. Adding the domain won't help here. Instead, ask Claude to allow its `add_repo` tool (the permission rule is `mcp__claude-code-remote__add_repo`) and then add `PantheonPlusSH0ES/DataRelease` to the session (read access is enough). Then ask Claude to run the starter again.
- **Anything else:** paste the error into the chat and ask Claude to fix it.

## How the setup works (for the curious)

- `setup_script.sh` runs once when the environment is created. It adds the emSign certificate and installs the core packages (`requirements-core.txt`) with [uv](https://docs.astral.sh/uv/), a fast replacement for pip. The environment stops it after about 5 minutes.
- `.claude/hooks/session-start.sh` runs at the start of every session. It re-adds the emSign certificate (a reused environment can lose it), installs the core packages if the setup script didn't, and installs the solar and DASCH packages (`requirements-extras.txt`) in the background.
- `starters/_ensure.py` lets starters 03, 13, 14 and 16 wait for that background install, or install what's still missing.
- On your own computer instead: `pip install -r requirements.txt` installs everything. If you use the python.org installer on a Mac and see certificate errors, run "Install Certificates.command" in your Python folder in Applications.
- `allowed_domains.txt` lists every data site the starters use, in case a stricter environment is set up later.
