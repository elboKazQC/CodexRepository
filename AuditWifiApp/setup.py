#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for WiFi Analyzer Application
"""

from setuptools import setup, find_packages  # type: ignore

setup(
    name="wifi-analyzer-app",
    version="1.0.0",
    description="Network WiFi Monitoring and Analysis Application",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pytest>=8.0.0",
        "pytest-cov>=4.0.0", 
        "pytest-mock>=3.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "wifi-analyzer=runner:main",
        ],
    },
)
