# CS85 astronomy teaser project

The person you're working with is an undergraduate who is new to coding. They're doing a one-week project: plan Tuesday, build Tuesday to Thursday, and demo a prototype Thursday. Explain what you're doing in plain language and keep the code readable.

## Where things are

- `PROJECTS.md`: the brief for every project: question, data source, first plot, Thursday prototype and stretch goal. Read the student's project entry before you start, and keep the work aimed at its Thursday prototype.
- `starters/NN_*.py`: one starter script per project. NN matches the project number in the course email. Each script downloads a small public dataset and saves one plot.
- `plots/`: save every figure here as a PNG.
- `data/`: put downloaded data here. It's git-ignored, so large files never get committed.
- `run_all_starters.py`: a test runner that checks the starters still work.
- `starters/_ensure.py`: a shared helper that starters 03, 13, 14 and 16 use to wait for the background package install.

## How to work

1. Start by running the student's starter script unchanged, so they get a real first plot quickly.
2. Make every figure with code: matplotlib, or plotly for interactive work. Never invent or simulate data and present it as real. If a download fails, say so and show the error.
3. Save each figure to `plots/` with a descriptive name. Commit the code and the plots, then push, so the student can open them on GitHub. GitHub shows PNG images in the browser.
4. At the end of each task, list the plot files you made with their GitHub links, and explain in 2 to 4 sentences what each one shows.
5. Keep downloads small, preferably under 200 MB. Cache them in `data/` so they're only downloaded once.
6. Cite the data source in the notebook, README, or slides you help the student make.

## Network

This cloud environment should use Full network access, so public data sites are reachable. If a request fails with a 403 or a proxy error, don't try to get around it. Tell the student to check that the environment's network access is set to Full rather than Limited. Only download public data, and never send tokens or passwords to any site except the service they belong to. If an API's address or fields seem to have changed, check the service's current documentation and fix the call.

## Certificate errors (emSign)

Some data sites use certificates that chain to the "emSign Root CA - G1" authority: gwosc.org (projects 18 and 19) and mastresolver.stsci.edu (project 25), possibly others. That root is in Mozilla's trusted list but not in this cloud machine's system list, and the cloud proxy's certificate list lacks it too. `.claude/hooks/session-start.sh` adds the copy in `certs/` each session and points `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` at the system list, but sometimes that doesn't take effect.

If a download fails with `CERTIFICATE_VERIFY_FAILED` or `SSLCertVerificationError`:

1. Tell the student, in plain words, that this is a known certificate problem with the cloud machine, not a bug in their code.
2. Run `bash .claude/hooks/session-start.sh`. It checks the certificate's SHA-256 fingerprint before adding it, and only switches to the system list when that list contains emSign plus every proxy certificate.
3. Rerun the starter with both variables set in the same command, since each shell command starts fresh: `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt python3 starters/NN_name.py`
4. If it still fails, the library may be downloading through astropy, which uses certifi's own list and ignores `REQUESTS_CA_BUNDLE` (gwpy's `fetch_open_data` does this). Download the file with `requests` instead and read it from `data/`, as `starters/19_hear_a_merger.py` does.
5. Never fix it by turning off certificate verification (`verify=False`, `PYTHONHTTPSVERIFY=0`, an unverified SSL context) or by downloading a certificate from anywhere other than `certs/` in this repo.
6. If a site not listed above fails this way, tell the student which site it was, so they can let the instructor know.

## Project 30: GitHub data repo

Starter 30 downloads the Pantheon+SH0ES data file from the public GitHub repo `PantheonPlusSH0ES/DataRelease`. Each cloud session can only read GitHub repos that have been added to it, so the download fails with "HTTP Error 403: Forbidden" until that repo is added. This is not a domain problem, so don't tell the student to add a domain. Use the `add_repo` tool (read access) to add `PantheonPlusSH0ES/DataRelease`. If the session's permissions block `add_repo`, tell the student and ask whether to add the permission rule `mcp__claude-code-remote__add_repo`, then try again. Don't download the file from mirrors or other routes.

## Free sign-ups

Project 02 needs a free AAVSO API token in the `AAVSO_TOKEN` environment variable. If the student wants it, they should add it to their own personal cloud environment, never to a shared one, and never commit it.
