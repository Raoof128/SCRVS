"""Setup script for Solidity Vulnerability Scanner."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README with explicit UTF-8 encoding for Windows compatibility
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    try:
        long_description = readme_file.read_text(encoding="utf-8")
    except Exception:
        long_description = ""
else:
    long_description = ""

setup(
    name="solidity-scanner",
    version="1.0.0",
    description="Static analysis tool for detecting reentrancy vulnerabilities and security issues in Solidity smart contracts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/solidity-scanner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    entry_points={
        "console_scripts": [
            "solscan=solidity_scanner.cli:main",
        ],
    },
    include_package_data=True,
)

