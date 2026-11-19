# MatchCo Platform - Versioning & Releases

## Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)
- **PRERELEASE**: alpha, beta, rc (e.g., `2.0.0-alpha.3`)
- **BUILD**: Build metadata (e.g., `+20261009`)

## Current Version

**Active**: `2.1.0` (development line)

## Release Lifecycle

### Development (Alpha)
- Prefix: `2.0.0-alpha.N`
- Status: Unstable, features under development
- Phase 6 E2E testing in progress
- Used internally for testing

### Testing (Beta)
- Prefix: `2.0.0-beta.N`
- Status: Feature complete, testing phase
- Ready for limited external testing
- Bug fixes and refinements

### Release Candidate (RC)
- Prefix: `2.0.0-rc.N`
- Status: Ready for production (pending final QA)
- No new features, only critical fixes
- Final testing with stakeholders

### Stable Release
- Format: `2.0.0`
- Status: Production ready
- Full support and maintenance
- Bugfix releases: `2.0.1`, `2.0.2`, etc.

## Release Process

### 1. Create Release Tag
```bash
# Create annotated tag
git tag -a v2.0.0-beta.1 -m "MatchCo v2.0.0-beta.1: Phase 6 complete, ready for testing"

# Push tag to GitHub
git push origin v2.0.0-beta.1
```

### 2. Create GitHub Release
```bash
# Via GitHub CLI
gh release create v2.0.0-beta.1 \
  --title "MatchCo v2.0.0-beta.1: Phase 6 Complete" \
  --notes "See CHANGELOG.md"

# Or manually on GitHub: https://github.com/francopoleo/matchco-platform/releases/new
```

### 3. Update VERSION File
Edit `VERSION` file:
```
2.0.0-beta.1
```

### 4. Update Changelog
Add entry to `CHANGELOG.md` with:
- Features added
- Bug fixes
- Breaking changes
- Migration instructions (if needed)

### 5. Commit & Push
```bash
git add VERSION CHANGELOG.md
git commit -m "Bump version: 2.0.0-alpha.3 → 2.0.0-beta.1"
git push origin main
```

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types trigger version bumps:
- `feat:` → MINOR version bump
- `fix:` → PATCH version bump
- `BREAKING CHANGE:` in footer → MAJOR version bump

Examples:
```
feat(recruitment): add store-customizable signup forms (→ MINOR)
fix(sidebar): correct admin menu filter (→ PATCH)
feat!: redesign API response format (→ MAJOR)
```

## Version Bumping Rules

| Change | Rule | Example |
|--------|------|---------|
| New feature | Minor bump | `2.0.0` → `2.1.0` |
| Bug fix | Patch bump | `2.0.0` → `2.0.1` |
| Breaking change | Major bump | `2.0.0` → `3.0.0` |
| Pre-release | Add suffix | `2.0.0` → `2.0.0-rc.1` |

## Release Checklist

- [ ] All tests passing (CI/CD)
- [ ] Code review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] VERSION file bumped
- [ ] Git tag created
- [ ] GitHub release published
- [ ] SDKs updated (Python, Node, PHP)
- [ ] Docker image built and pushed
- [ ] Deployment tested
- [ ] Changelog published in release notes

## Maintenance Branches

- **main**: Latest stable/pre-release
- **release/2.0.x**: Hotfixes for v2.0 series
- **release/1.x**: Legacy support (if needed)

## Long-term Support (LTS)

Planned LTS releases:
- `2.0.0` (stable, Q4 2026)
- Support window: 24 months

## FAQ

**Q: When do I bump to v3.0.0?**
A: Only for breaking API/schema changes. Not frequently—major versions are rare.

**Q: Should I release every commit?**
A: No. Release when features are complete (weekly/monthly), not per-commit.

**Q: What if I need a hotfix?**
A: Branch from tag, fix, test, tag as patch version.

**Q: How do I revert a release?**
A: Delete the tag, fix code, re-tag with same version (or new patch version).

## Tools & Automation

### Manual Releases
```bash
# Full release process
VERSION=2.0.0-beta.1
git tag -a v$VERSION -m "Release $VERSION"
git push origin v$VERSION
gh release create v$VERSION --title "v$VERSION" --notes "See CHANGELOG.md"
```

### Automated (GitHub Actions)
Create `.github/workflows/release.yml` to:
- Detect version change in VERSION file
- Run tests
- Build Docker image
- Create GitHub release
- Push to registries

(See RELEASE_AUTOMATION.md for setup)

---

**Last Updated**: 2026-10-09  
**Maintainer**: Franco  
**Repository**: https://github.com/francopoleo/matchco-platform
