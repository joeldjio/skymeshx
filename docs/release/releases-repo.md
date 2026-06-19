# Public Releases-Repository: rz-gcs-releases

**URL:** https://github.com/joeldjio/rz-gcs-releases

Das öffentliche Repository ist der Download-Kanal für Endnutzer.
Der Quellcode bleibt im privaten Repo — Nutzer sehen nur die fertigen Installer.

---

## Zweck

- Öffentlicher Download-Punkt für alle Plattform-Installer
- In-App-Updater fragt die GitHub Releases API dieses Repos ab
- Nutzer können das Repo ohne GitHub-Account durchsuchen / herunterladen

---

## Was hier veröffentlicht wird

| Datei | Plattform |
|-------|-----------|
| `skymeshx-gcs-setup-X.Y.Z.exe` | Windows |
| `skymeshx-gcs-setup-X.Y.Z.exe.sha256` | Windows (Checksum) |
| `skymeshx-gcs-macos.tar.gz` | macOS |
| `skymeshx-gcs-macos.tar.gz.sha256` | macOS (Checksum) |
| `skymeshx-gcs_X.Y.Z_amd64_jammy.deb` | Ubuntu 22.04 |
| `skymeshx-gcs_X.Y.Z_amd64_jammy.deb.sha256` | Ubuntu 22.04 (Checksum) |

---

## Was hier NICHT veröffentlicht wird

- Quellcode
- Python-Dateien
- Build-Scripts
- License-Secrets / GitHub-Tokens
- Interne Notizen

---

## Automatische Veröffentlichung

Releases werden automatisch durch GitHub Actions erstellt wenn ein `v*`-Tag
im privaten Source-Repo gepusht wird.

**Benötigtes Secret im Source-Repo:**
```
RELEASES_REPO_TOKEN  →  GitHub PAT (classic, public_repo Scope)
```

Manueller Release: Actions → "Build & Publish SkyMeshX GCS" → Run workflow → publish = true

---

## In-App-Updater Integration

`tools/ui/_version.py`:
```python
GITHUB_REPO = "joeldjio/rz-gcs-releases"
INSTALLER_ASSET_PREFIX = "skymeshx-gcs-setup-"
```

Der Updater:
1. Ruft `https://api.github.com/repos/joeldjio/rz-gcs-releases/releases/latest` ab
2. Vergleicht Tag-Version mit aktueller `VERSION`
3. Sucht Asset mit Prefix `skymeshx-gcs-setup-` und Suffix `.exe`
4. Lädt `.sha256` Datei zur Verifikation herunter
5. Zeigt Update-Banner wenn neue Version verfügbar
