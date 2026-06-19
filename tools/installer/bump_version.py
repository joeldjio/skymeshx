#!/usr/bin/env python3
"""
bump_version.py – Bump the SkyMeshX GCS version in all relevant files.

Usage:
    python tools/installer/bump_version.py 0.4.0

Updates:
    - tools/ui/_version.py          (VERSION = "x.y.z")
    - tools/installer/inno/skymeshx_gcs.iss  (#define AppVersion "x.y.z")

Then prints the git commands to tag and push the release.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

FILES = [
    # (file path, regex pattern, replacement template)
    (
        PROJECT_ROOT / "tools" / "ui" / "_version.py",
        r'(VERSION\s*:\s*str\s*=\s*")[^"]+(")',
        r"\g<1>{version}\g<2>",
    ),
    (
        PROJECT_ROOT / "tools" / "installer" / "inno" / "skymeshx_gcs.iss",
        r'(#define\s+AppVersion\s+")[^"]+(")',
        r"\g<1>{version}\g<2>",
    ),
]


def bump(new_version: str) -> None:
    # Validate semver-ish format
    if not re.fullmatch(r"\d+\.\d+\.\d+", new_version):
        print(f"ERROR: Version must be in X.Y.Z format, got: {new_version}")
        sys.exit(1)

    changed: list[Path] = []

    for file_path, pattern, replacement in FILES:
        if not file_path.exists():
            print(f"SKIP (not found): {file_path.relative_to(PROJECT_ROOT)}")
            continue

        original = file_path.read_text(encoding="utf-8")
        updated = re.sub(pattern, replacement.format(version=new_version), original)

        if updated == original:
            print(f"UNCHANGED:        {file_path.relative_to(PROJECT_ROOT)}")
        else:
            file_path.write_text(updated, encoding="utf-8")
            print(f"UPDATED:          {file_path.relative_to(PROJECT_ROOT)}")
            changed.append(file_path)

    if not changed:
        print("\nNo files changed – is the version already set?")
        return

    print(f"\nVersion bumped to {new_version}. Run these commands to release:\n")
    print(f"  git add tools/ui/_version.py tools/installer/inno/skymeshx_gcs.iss")
    print(f'  git commit -m "Bump version to {new_version}"')
    print(f"  git tag v{new_version}")
    print(f"  git push origin ui-dashboard --tags")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    bump(sys.argv[1])
