#!/usr/bin/env python3
import os
import sys
from setuptools import setup, find_packages


def validate_license_secret():
    """Validate license secret before building release packages.
    
    This prevents shipping builds with the development secret that would
    allow anyone with source access to mint valid license keys.
    
    Skip validation if SKIP_LICENSE_CHECK=1 (for development builds).
    """
    if os.getenv("SKIP_LICENSE_CHECK") == "1":
        print("[SETUP] Skipping license secret validation (development build)")
        return
    
    try:
        from tools.ui._version import LICENSE_SECRET
        
        # Check if development secret is still in use
        if LICENSE_SECRET.startswith("skymeshx-dev-secret"):
            print("\n" + "="*70, file=sys.stderr)
            print("RELEASE BLOCKER: Development license secret detected!", file=sys.stderr)
            print("="*70, file=sys.stderr)
            print("\nThe LICENSE_SECRET in tools/ui/_version.py must be rotated", file=sys.stderr)
            print("before building release packages.\n", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print("  1. Set SKYMESHX_LICENSE_SECRET environment variable", file=sys.stderr)
            print("  2. Update LICENSE_SECRET in tools/ui/_version.py", file=sys.stderr)
            print("  3. Set SKIP_LICENSE_CHECK=1 for development builds\n", file=sys.stderr)
            sys.exit(1)
        
        # Check minimum secret length
        if len(LICENSE_SECRET) < 32:
            print("\n" + "="*70, file=sys.stderr)
            print("RELEASE BLOCKER: License secret too short!", file=sys.stderr)
            print("="*70, file=sys.stderr)
            print(f"\nLICENSE_SECRET must be at least 32 characters (got {len(LICENSE_SECRET)})\n", file=sys.stderr)
            sys.exit(1)
        
        print("[SETUP] License secret validation passed")
        
    except ImportError:
        # tools.ui not available, skip check
        print("[SETUP] Skipping license secret validation (tools.ui not available)")


# Run validation before setup
validate_license_secret()

setup(
    name="skymeshx",
    version="0.3.7",
    packages=find_packages(include=["skymeshx*"]),
    install_requires=[
        "pymavlink>=2.4.40",
        "pyserial>=3.5",
    ],
    extras_require={
        "ros": [],
        "test": ["pytest>=8.0"],
        "dev": ["pytest>=7.0", "pytest-timeout>=2.1"],
    },
    entry_points={
        "console_scripts": [
            "skymeshx=skymeshx.cli.main:main",
        ],
    },
)
