#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="droneresearch",
    version="0.2.0",
    packages=find_packages(include=["droneresearch*"]),
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
            "droneresearch=droneresearch.cli.main:main",
        ],
    },
)
