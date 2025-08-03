#!/usr/bin/env python3
"""
Setup script for Transcription Platform Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="transcription-platform",
    version="1.0.0",
    author="Transcription Platform",
    author_email="support@example.com",
    description="Official Python SDK for the Transcription Platform API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/transcription-platform/python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "pytest-mock>=3.0.0",
            "black>=21.0",
            "flake8>=3.8.0",
            "mypy>=0.900",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/transcription-platform/python-sdk/issues",
        "Source": "https://github.com/transcription-platform/python-sdk",
        "Documentation": "https://docs.example.com/sdk/python",
    },
)