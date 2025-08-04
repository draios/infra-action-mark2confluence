"""
mark2confluence - A GitHub Action to convert Markdown files to Confluence pages using mark
"""

import tomllib
from pathlib import Path

def get_version():
    """Get version from pyproject.toml"""
    try:
        # Get the project root directory (two levels up from this file)
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        return data["tool"]["poetry"]["version"]
    except (KeyError, FileNotFoundError):
        # Fallback version if pyproject.toml is not available
        return "0.1.0"

__version__ = get_version()
__author__ = "Devops"
__email__ = "devops@sysdig.com"
