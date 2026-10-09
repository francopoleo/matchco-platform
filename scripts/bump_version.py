#!/usr/bin/env python3
"""
MatchCo Version Bumper - Automate semantic versioning

Usage:
    python scripts/bump_version.py --major
    python scripts/bump_version.py --minor
    python scripts/bump_version.py --patch
    python scripts/bump_version.py --prerelease alpha 4
"""

import sys
import re
from pathlib import Path
from datetime import datetime

def read_version():
    """Read current version from VERSION file."""
    version_file = Path(__file__).parent.parent / "VERSION"
    return version_file.read_text().strip()

def write_version(version):
    """Write version to VERSION file."""
    version_file = Path(__file__).parent.parent / "VERSION"
    version_file.write_text(version + "\n")

def parse_version(version):
    """Parse semantic version string.
    
    Returns: (major, minor, patch, prerelease, prerelease_num)
    Example: "2.0.0-alpha.3" → (2, 0, 0, "alpha", 3)
    """
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.(\d+))?$"
    match = re.match(pattern, version)
    
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch, prerelease, prerelease_num = match.groups()
    return (
        int(major),
        int(minor),
        int(patch),
        prerelease or None,
        int(prerelease_num) if prerelease_num else None,
    )

def format_version(major, minor, patch, prerelease=None, prerelease_num=None):
    """Format version back to string."""
    version = f"{major}.{minor}.{patch}"
    if prerelease:
        version += f"-{prerelease}.{prerelease_num}"
    return version

def bump_version(current, bump_type, prerelease=None, prerelease_num=None):
    """Bump version based on type."""
    major, minor, patch, pre, pre_num = parse_version(current)
    
    if bump_type == "major":
        return format_version(major + 1, 0, 0)
    elif bump_type == "minor":
        return format_version(major, minor + 1, 0)
    elif bump_type == "patch":
        return format_version(major, minor, patch + 1)
    elif bump_type == "prerelease":
        if prerelease_num:
            return format_version(major, minor, patch, prerelease, prerelease_num)
        else:
            pre_num = (pre_num or 0) + 1
            return format_version(major, minor, patch, prerelease, pre_num)
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")

def update_changelog(old_version, new_version):
    """Update CHANGELOG.md with new version entry."""
    changelog = Path(__file__).parent.parent / "CHANGELOG.md"
    content = changelog.read_text()
    
    date = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"""## [{new_version}] - {date}

### Added
- Add description of new features here

### Fixed
- Add bug fixes here

### Changed
- Add changes here

### Deprecated
- Add deprecations here

---

"""
    
    # Insert after header
    lines = content.split("\n")
    insert_pos = next(i for i, line in enumerate(lines) if line.startswith("## ["))
    
    new_lines = lines[:insert_pos] + new_entry.split("\n") + lines[insert_pos:]
    changelog.write_text("\n".join(new_lines))

def main():
    if len(sys.argv) < 2:
        print("Usage: python bump_version.py [--major|--minor|--patch|--prerelease TYPE NUM]")
        sys.exit(1)
    
    current = read_version()
    print(f"Current version: {current}")
    
    if sys.argv[1] == "--major":
        new = bump_version(current, "major")
    elif sys.argv[1] == "--minor":
        new = bump_version(current, "minor")
    elif sys.argv[1] == "--patch":
        new = bump_version(current, "patch")
    elif sys.argv[1] == "--prerelease" and len(sys.argv) >= 4:
        prerelease = sys.argv[2]
        prerelease_num = int(sys.argv[3])
        new = bump_version(current, "prerelease", prerelease, prerelease_num)
    else:
        print("Invalid arguments")
        sys.exit(1)
    
    print(f"New version: {new}")
    
    # Confirm
    response = input("Confirm? (y/n): ")
    if response.lower() != "y":
        print("Cancelled")
        sys.exit(1)
    
    write_version(new)
    # update_changelog(current, new)  # Optional
    
    print(f"✅ Version bumped: {current} → {new}")
    print(f"Next: git add VERSION && git commit -m 'Bump version: {current} → {new}'")

if __name__ == "__main__":
    main()
