# MatchCo Platform - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.0-alpha.4] - 2026-11-09

### Changed
- **Django 5.2 Upgrade** — Migrated from Django 4.2 to Django 5.2 for Python 3.14+ compatibility
  - Removed deprecated `USE_L10N` setting
  - Replaced `STATICFILES_STORAGE` with `STORAGES` dictionary
  - Added missing dependencies: `django-tenants`, `unidecode`, `django-ratelimit`

### Fixed
- Routes `/console/courses/`, `/console/quizzes/` and `/app/feed/` now work correctly after dependency installation

---

## [2.0.0-alpha.3] - 2026-10-09

### Added
- **Talk↔Recruitment Integration Enhancements**
  - Dynamic topic names with actual course titles in ProfileSignal
  - Course ID tracking in signal keys for better deduplication
  - Message length engagement metrics in signal values
  - Enables employers to see participation depth and course context

- **Console Menu Organization**
  - Reorganized 60 menu items into 12 logical sections
  - Clear flow: setup → people → content → analytics → specialized
  - Improved navigation mental model for users
  - Section comments for code maintainability

- **Menu UX Consolidation**
  - Consolidated 3 groups: platform→access, services→structure, people→access
  - Reduced visual clutter by 23% (13 groups → 10 groups)
  - Fixed singleton group anti-pattern
  - Improved semantic grouping

### Fixed
- **Admin Menu Filter Bug**
  - Admins now bypass service-level menu filters
  - Admins can see all 8 intelligence menu items (was showing only 1)
  - Service filtering now respects user role (admins exempt)
  - Backward compatible with staff-only restrictions

### Changed
- Menu structure: Reorganized for better UX
- Access group: Renamed from "Acessos e governança" to "Gestão de pessoas e acessos"
- GROUP_ORDER: Adjusted for logical flow (org → people → content → analytics)

### Documentation
- Added SESSION_SUMMARY_2026_10_09.md with complete session documentation
- Enhanced VERSIONING.md with release process
- Created CHANGELOG.md (this file)
- Memory system entries for future sessions

---

## [2.0.0-alpha.2] - 2026-10-08

### Added
- **Phase 6: E2E Testing - 95% Complete**
  - Playwright infrastructure (conftest.py with fixtures)
  - Critical path tests (46 tests: candidate, employer, store flows)
  - Performance baselines (form load, API latency, 11 tests)
  - Regression suite (45+ tests for Phase 4-5 validation)
  - Load testing (18 tests, up to 100 concurrent users)
  - Browser compatibility (48 tests: Chrome, Firefox, Safari, iOS, Android, Tablet)
  - Total: 170+ test methods, 270+ assertions, 4,800+ test lines

### Documentation
- Added QR_REDESIGN_PHASE6_E2E_TESTING.md
- Complete test architecture documentation
- Performance baselines and browser compatibility matrix

---

## [2.0.0-alpha.1] - 2026-10-07

### Added
- **Phase 5: Admin Question Validation**
  - Question whitelist: 30+ allowed patterns
  - Question blacklist: 35+ forbidden patterns
  - Admin warning system for ambiguous questions
  - Audit log for all question changes
  - Ops approval workflow
  - Migration: 0073_phase5_admin_validation

- **Phase 4: RBAC Enforcement**
  - State-based access control
  - Protected views with state validation
  - Complete state machine implementation (7 states)
  - Error messages explaining state-based blocking

### Documentation
- Added QR_REDESIGN_PHASE4_RBAC.md
- Added QR_REDESIGN_PHASE5_ADMIN_VALIDATION.md
- Complete RBAC and compliance documentation

---

## [2.0.0-alpha.0] - 2026-10-01

### Added
- **Phase 1-3: Universal QR with Store-Customizable Signup**
  - StoreSignupConfiguration model
  - Three new views: StoreChooserView, ActionChooserView, CustomSignupView
  - Dynamic questionnaire rendering (all question types)
  - OTP phone verification
  - Session-based state management
  - Three new templates with Tailwind + dark mode
  - Migration: 0072_add_store_signup_configuration

### Documentation
- Added QR_REDESIGN_MASTER_GUIDE.md
- Added QR_REDESIGN_IMPLEMENTATION_SUMMARY.md
- Added QR_REDESIGN_TEST_GUIDE.md
- Complete Phase 1-3 documentation

---

## [2.0.0] - Planned (Q4 2026)

### Planned
- Phase 6 completion: CI/CD pipeline integration
- Final optimization and sign-off
- Production release

---

## [1.0.0] - Legacy (Earlier)

Earlier releases. See git history for details.

---

## Release Guidelines

- Follow [Conventional Commits](https://www.conventionalcommits.org/)
- Update this file before creating release tag
- Tag format: `vMAJOR.MINOR.PATCH[-PRERELEASE]`
- Create GitHub release with changelog excerpt

See VERSIONING.md for detailed release process.
