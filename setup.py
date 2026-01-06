#!/usr/bin/env python3
"""
setup.py for tt-jukebox

Enables pip installation and creates console script entry points.
"""

from setuptools import setup
import re

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Intelligent Model & Environment Manager for Tenstorrent Hardware"

# Extract version from tt-jukebox.py
version = "1.0.0"
try:
    with open("tt-jukebox.py", "r", encoding="utf-8") as f:
        content = f.read()
        # Look for version string in the file
        version_match = re.search(r'[Vv]ersion:\s*([0-9]+\.[0-9]+\.[0-9]+)', content)
        if version_match:
            version = version_match.group(1)
except FileNotFoundError:
    pass

# Base requirements (none for CLI-only mode)
install_requires = []

# Optional TUI requirements
extras_require = {
    "tui": ["textual>=0.47.0", "rich>=13.7.0"],
}

setup(
    name="tt-jukebox",
    version=version,
    description="Intelligent Model & Environment Manager for Tenstorrent Hardware",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tenstorrent Community",
    author_email="",
    url="https://github.com/tenstorrent/tt-jukebox",

    # Single-file modules
    py_modules=["tt-jukebox", "tt-jukebox-tui"],

    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,

    # Console script entry points
    entry_points={
        "console_scripts": [
            "tt-jukebox=tt-jukebox:main",
            "tt-jukebox-tui=tt-jukebox-tui:main",
        ],
    },

    # PyPI classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Hardware",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],

    keywords="tenstorrent tt-metal vllm model-management hardware-acceleration ai ml",

    project_urls={
        "Bug Reports": "https://github.com/tenstorrent/tt-jukebox/issues",
        "Source": "https://github.com/tenstorrent/tt-jukebox",
        "Documentation": "https://github.com/tenstorrent/tt-jukebox#readme",
        "Discord": "https://discord.gg/tenstorrent",
    },
)
