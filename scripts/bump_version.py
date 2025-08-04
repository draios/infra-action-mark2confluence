#!/usr/bin/env python3
"""
Script to bump version in pyproject.toml (the single source of truth)
Usage: python scripts/bump_version.py [major|minor|patch] [new_version]
"""

import re
import sys
from pathlib import Path

def bump_version(version, bump_type=None, new_version=None):
    """Bump version according to semantic versioning"""
    if new_version:
        return new_version
    
    if not bump_type:
        print("Error: Must specify bump type (major|minor|patch) or new version")
        sys.exit(1)
    
    major, minor, patch = map(int, version.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        print(f"Error: Invalid bump type '{bump_type}'. Use major, minor, or patch")
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"

def update_pyproject_version(new_version):
    """Update version in pyproject.toml"""
    project_root = Path(__file__).parent.parent
    pyproject_file = project_root / "pyproject.toml"
    
    with open(pyproject_file, 'r') as f:
        content = f.read()
    
    # Update version in pyproject.toml
    pattern = r'(version\s*=\s*)"[^"]*"'
    replacement = rf'\1"{new_version}"'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content == content:
        print("Warning: No version line found to update in pyproject.toml")
        return False
    
    with open(pyproject_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated pyproject.toml with version: {new_version}")
    return True

def get_current_version():
    """Get current version from pyproject.toml"""
    project_root = Path(__file__).parent.parent
    pyproject_file = project_root / "pyproject.toml"
    
    with open(pyproject_file, 'r') as f:
        content = f.read()
    
    match = re.search(r'version\s*=\s*"([^"]*)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    return match.group(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/bump_version.py [major|minor|patch] [new_version]")
        print("Examples:")
        print("  python scripts/bump_version.py patch")
        print("  python scripts/bump_version.py minor")
        print("  python scripts/bump_version.py major")
        print("  python scripts/bump_version.py 1.2.3")
        sys.exit(1)
    
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    if len(sys.argv) == 2:
        # Single argument - could be bump type or new version
        arg = sys.argv[1]
        if arg in ['major', 'minor', 'patch']:
            new_version = bump_version(current_version, arg)
        else:
            # Assume it's a new version
            new_version = arg
    else:
        # Two arguments - bump type and new version
        bump_type = sys.argv[1]
        new_version = sys.argv[2]
        if bump_type in ['major', 'minor', 'patch']:
            new_version = bump_version(current_version, bump_type, new_version)
    
    if update_pyproject_version(new_version):
        print(f"Version bumped from {current_version} to {new_version}")

if __name__ == "__main__":
    main()
