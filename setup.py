from setuptools import setup, find_packages
import tomllib
from pathlib import Path

def get_project_metadata():
    """Get project metadata from pyproject.toml"""
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        poetry_data = data["tool"]["poetry"]
        return {
            "name": poetry_data["name"],
            "version": poetry_data["version"],
            "description": poetry_data["description"],
            "authors": poetry_data.get("authors", ["Your Name <your.email@example.com>"])
        }
    except (KeyError, FileNotFoundError):
        # Fallback metadata
        return {
            "name": "mark2confluence",
            "version": "0.1.0",
            "description": "A GitHub Action to convert Markdown files to Confluence pages using mark",
            "authors": ["Your Name <your.email@example.com>"]
        }

# Get metadata from pyproject.toml
metadata = get_project_metadata()
author_info = metadata["authors"][0].split(" <")
author_name = author_info[0]
author_email = author_info[1].rstrip(">") if len(author_info) > 1 else "your.email@example.com"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name=metadata["name"],
    version=metadata["version"],
    author=author_name,
    author_email=author_email,
    description=metadata["description"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mark2confluence=mark2confluence.main:main",
        ],
    },
)
