#!/usr/bin/env python3
from setuptools import setup, find_packages

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
