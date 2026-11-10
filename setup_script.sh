#!/bin/bash
# CS85 astronomy cloud environment: paste this into the environment's "Setup script" box.
# Runs once, then Claude caches the result, so later sessions start with everything installed.
# The environment stops this script after about 5 minutes, so it does the quick certificate
# step first and installs only the core packages (same list as requirements-core.txt).
# The solar and DASCH packages (requirements-extras.txt) are installed by the repo's
# SessionStart hook, .claude/hooks/session-start.sh, instead.

# 1. Trust the "emSign Root CA - G1" certificate authority. gwosc.org (projects 18, 19) and
# mastresolver.stsci.edu (project 25, star-name lookups) use certificates that chain to it.
# It's in Mozilla's trusted list (shipped in Python's certifi package) but not yet in this
# container's older system list, so those downloads failed with "CERTIFICATE_VERIFY_FAILED".
# The repo's SessionStart hook adds it again each session (a reused environment can lose it;
# the hook's copy is certs/emSign_Root_CA_-_G1.crt), then points Python (REQUESTS_CA_BUNDLE,
# SSL_CERT_FILE) at this system list, because the cloud proxy's own list lacks emSign.
# SHA-256 fingerprint: 40:F6:AF:03:46:A9:9A:A1:CD:1D:55:5A:4E:9C:CE:62:C7:F9:63:46:03:EE:40:66:15:83:3D:C8:C8:D0:03:67
cat > /usr/local/share/ca-certificates/emSign_Root_CA_-_G1.crt <<'PEM'
-----BEGIN CERTIFICATE-----
MIIDlDCCAnygAwIBAgIKMfXkYgxsWO3W2DANBgkqhkiG9w0BAQsFADBnMQswCQYD
VQQGEwJJTjETMBEGA1UECxMKZW1TaWduIFBLSTElMCMGA1UEChMcZU11ZGhyYSBU
ZWNobm9sb2dpZXMgTGltaXRlZDEcMBoGA1UEAxMTZW1TaWduIFJvb3QgQ0EgLSBH
MTAeFw0xODAyMTgxODMwMDBaFw00MzAyMTgxODMwMDBaMGcxCzAJBgNVBAYTAklO
MRMwEQYDVQQLEwplbVNpZ24gUEtJMSUwIwYDVQQKExxlTXVkaHJhIFRlY2hub2xv
Z2llcyBMaW1pdGVkMRwwGgYDVQQDExNlbVNpZ24gUm9vdCBDQSAtIEcxMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAk0u76WaK7p1b1TST0Bsew+eeuGQz
f2N4aLTNLnF115sgxk0pvLZoYIr3IZpWNVrzdr3YzZr/k1ZLpVkGoZM0Kd0WNHVO
8oG0x5ZOrRkVUkr+PHB1cM2vK6sVmjM8qrOLqs1D/fXqcP/tzxE7lM5OMhbTI0Aq
d7OvPAEsbO2ZLIvZTmmYsvePQbAyeGHWDV/D+qJAkh1cF+ZwPjXnorfCYuKrpDhM
tTk1b+oDafo6VGiFbdbyL0NVHpENDtjVaqSW0RM8LHhQ6DqS0hdW5TUaQBw+jSzt
Od9C4INBdN+jzcKGYEho42kLVACL5HZpIQ15TjQIXhTCzLG3rdd8cIrHhQIDAQAB
o0IwQDAdBgNVHQ4EFgQU++8Nhp6w492pufEhF38+/PB3KxowDgYDVR0PAQH/BAQD
AgEGMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAFn/8oz1h31x
PaOfG1vR2vjTnGs2vZupYeveFix0PZ7mddrXuqe8QhfnPZHr5X3dPpzxz5KsbEjM
wiI/aTvFthUvozXGaCocV685743QNcMYDHsAVhzNixl03r4PEuDQqqE/AjSxcM6d
GNYIAwlG7mDgfrbESQRRfXBgvKqy/3lyeqYdPV8q+Mri/Tm3R7nrft8EI6/6nAYH
6ftjk4BAtcZsCjEozgyfz7MjNYBBjWzEN3uBL4ChQEKF6dk4jeihU80Bv2noWgby
RQuQ+q7hv53yrlc8pa6yVvSLZUDp/TGBLPQ5Cdjua6e0ph0VpZj3AYHYhX3zUVxx
iN66zB+Afko=
-----END CERTIFICATE-----
PEM
update-ca-certificates
grep -q "MIIDlDCCAnygAwIBAgIKMfXkYgxsWO3W2D" /etc/ssl/certs/ca-certificates.crt && echo "emSign root installed" || { echo "ERROR: emSign root not in system bundle"; exit 1; }

# 2. Core Python packages, installed with uv: a fast replacement for pip that downloads and
# installs packages in parallel, so this finishes well inside the time limit.
# If uv isn't already here, we install it with pip. UV_NATIVE_TLS makes uv use the system
# certificate list, which trusts the cloud proxy.
CORE_PACKAGES="alerce astropy astroquery gwpy lightkurve matplotlib numpy pandas pyvo requests
  scikit-learn scipy skyfield sparclclient plotly streamlit"
export UV_NATIVE_TLS=1
export PATH="$PATH:/root/.local/bin"
command -v uv >/dev/null || pip install --break-system-packages -q --root-user-action=ignore uv
if command -v uv >/dev/null \
   && uv pip install --system --break-system-packages -q $CORE_PACKAGES; then
  echo "CS85 core packages installed with uv"
else
  # Fallback: plain pip (much slower). --use-pep517 builds source-only packages with a fresh
  # setuptools; without it, the system's Debian setuptools fails with "AttributeError: install_layout".
  echo "uv didn't work; falling back to pip"
  pip install --break-system-packages -q --ignore-installed --use-pep517 --root-user-action=ignore \
    pip setuptools wheel
  pip install --break-system-packages -q --use-pep517 --root-user-action=ignore $CORE_PACKAGES \
    || echo "WARNING: CS85 setup pip install failed"
fi
