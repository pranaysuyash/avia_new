"""
Setup script for the Transcription API Python SDK
"""

from setuptools import setup, find_packages
import os

# Read the README file
current_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_dir, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open(os.path.join(current_dir, "requirements.txt"), "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="transcription-api",
    version="1.0.0",
    author="Transcription API Team",
    author_email="support@transcriptionapi.com",
    description="Python SDK for the Audio/Video Transcription Platform API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/transcription-api/python-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/transcription-api/python-sdk/issues",
        "Documentation": "https://docs.transcriptionapi.com/sdk/python",
        "Source Code": "https://github.com/transcription-api/python-sdk",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "async": ["aiohttp>=3.8.0", "aiofiles>=0.8.0"],
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.17.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "transcription-cli=transcription_api.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "transcription_api": ["py.typed"],
    },
    keywords=[
        "transcription",
        "speech-to-text",
        "audio",
        "video",
        "ai",
        "machine-learning",
        "api",
        "sdk",
    ],
    zip_safe=False,
)