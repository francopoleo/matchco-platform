# MatchCo Platform - Release Guide

Quick reference for creating releases.

## Quick Start

### 1. Bump Version
```bash
# Bump to next version
python scripts/bump_version.py --minor  # 2.0.0-alpha.3 → 2.1.0-alpha.3
python scripts/bump_version.py --patch  # 2.0.0 → 2.0.1
python scripts/bump_version.py --prerelease beta 1  # → 2.0.0-beta.1
```

### 2. Update CHANGELOG.md
Edit `CHANGELOG.md` and add entry for new version:
```markdown
## [2.0.0-beta.1] - 2026-10-10

### Added
- Feature X
- Feature Y

### Fixed
- Bug A
- Bug B
```

### 3. Commit Version Bump
```bash
git add VERSION CHANGELOG.md
git commit -m "Bump version: 2.0.0-alpha.3 → 2.0.0-beta.1"
git push origin main
```

### 4. Create Tag & Release
```bash
# Create annotated tag
TAG=v2.0.0-beta.1
git tag -a $TAG -m "MatchCo $TAG: Phase 6 complete, ready for beta testing"

# Push tag (triggers GitHub Actions)
git push origin $TAG

# Create GitHub release (auto or manual)
gh release create $TAG --title "MatchCo $TAG" --notes-file CHANGELOG.md
```

### 5. Verify Release
- Check: https://github.com/francopoleo/matchco-platform/releases
- Verify tag, version, changelog

## Full Release Commands

### Alpha Release
```bash
VERSION=2.0.0-alpha.4
python scripts/bump_version.py --prerelease alpha 4
# Edit CHANGELOG.md
git add VERSION CHANGELOG.md
git commit -m "Bump version: 2.0.0-alpha.3 → $VERSION"
git tag -a v$VERSION -m "MatchCo v$VERSION: Alpha release"
git push origin main v$VERSION
gh release create v$VERSION --title "MatchCo v$VERSION" --prerelease
```

### Beta Release
```bash
VERSION=2.0.0-beta.1
python scripts/bump_version.py --minor  # Bump minor to x.1.0
# Edit CHANGELOG.md
git add VERSION CHANGELOG.md
git commit -m "Bump version: 2.0.0 → $VERSION"
git tag -a v$VERSION -m "MatchCo v$VERSION: Beta testing begins"
git push origin main v$VERSION
gh release create v$VERSION --title "MatchCo v$VERSION"
```

### Stable Release
```bash
VERSION=2.0.0
# Remove pre-release suffix
echo "$VERSION" > VERSION
# Edit CHANGELOG.md
git add VERSION CHANGELOG.md
git commit -m "Release: MatchCo v$VERSION"
git tag -a v$VERSION -m "MatchCo v$VERSION: Stable release"
git push origin main v$VERSION
gh release create v$VERSION --title "MatchCo v$VERSION"
```

### Hotfix Release
```bash
VERSION=2.0.1
python scripts/bump_version.py --patch  # Bump patch to x.x.1
# Edit CHANGELOG.md (bugfixes only)
git add VERSION CHANGELOG.md
git commit -m "Hotfix: MatchCo v$VERSION"
git tag -a v$VERSION -m "MatchCo v$VERSION: Hotfix release"
git push origin main v$VERSION
gh release create v$VERSION --title "MatchCo v$VERSION"
```

## Release Checklist

- [ ] All tests passing
- [ ] Code review approved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with all changes
- [ ] VERSION file bumped
- [ ] Git tag created: `git tag -a vX.Y.Z`
- [ ] GitHub release published
- [ ] Release notes reviewed
- [ ] Deployment tested (if applicable)
- [ ] Users notified

## Reverting a Release

If something goes wrong:

```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag
git push origin --delete vX.Y.Z

# Delete GitHub release (via GitHub UI)
```

## Automated Releases (GitHub Actions)

When you push a tag:
```bash
git push origin vX.Y.Z
```

GitHub Actions automatically:
1. Detects the tag (matches `v*`)
2. Reads VERSION file
3. Determines if prerelease (alpha/beta/rc)
4. Creates GitHub release
5. Publishes CHANGELOG excerpt

See `.github/workflows/release.yml` for automation details.

## Version History

Current stable: v2.0.1
Current pre-release: v2.0.0-alpha.3

Full history: https://github.com/francopoleo/matchco-platform/releases

## FAQ

**Q: Can I create a release without a tag?**
A: Not recommended. Always use git tags for traceability.

**Q: Should I delete a release after publishing?**
A: No, keep all releases for historical reference.

**Q: How do I support multiple major versions?**
A: Use separate branches (main for v2.x, release/1.x for v1.x hotfixes).

---

See VERSIONING.md for detailed versioning strategy.
