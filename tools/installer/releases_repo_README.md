# UAVResearch GCS – Releases

Public download page for the **UAVResearch Ground Control Station**.

The source code lives in a private repository and is built automatically by
GitHub Actions. Every version tag (`v*`) triggers a CI build across all three
platforms; the resulting installers are published here as GitHub Releases.

---

## Download

Go to the [**Releases**](../../releases) tab and pick the latest version.

| Platform | File | Install |
|----------|------|---------|
| **Windows** | `uavresearch-gcs-setup-X.Y.Z.exe` | Run the installer |
| **macOS** | `uavresearch-gcs-macos.tar.gz` | Extract → run `UAVResearchGCS/uavresearch gcs` |
| **Linux** (Ubuntu 22.04 Jammy) | `uavresearch-gcs_X.Y.Z_amd64.deb` | `sudo dpkg -i *.deb` |

### SmartScreen / Gatekeeper warning

The binaries are not code-signed yet. On **Windows**, click *More info → Run anyway*.
On **macOS**, right-click the app → Open.

---

## In-app updates

The GCS checks this repository's Releases API on startup and offers a
one-click upgrade when a newer version is available. It looks for a release
asset whose name starts with `uavresearch-gcs-setup-` and ends with `.exe`.

---

## Changelog

See individual release notes on the [Releases](../../releases) page.

---

*Built with [PyInstaller](https://pyinstaller.org) · MIT License*
