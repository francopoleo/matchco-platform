# E2E Testing Suite

Comprehensive end-to-end testing for MatchCo QR Redesign Phases 1-6.

## Structure

```
tests/e2e/
├── conftest.py                          # Pytest fixtures & configuration
├── critical_paths/
│   ├── test_candidate_flow.py          # Candidate signup → contact
│   ├── test_employer_flow.py           # Employer matching → interest (TODO)
│   └── test_store_flow.py              # Store setup → responses (TODO)
├── performance/
│   ├── test_form_load.py               # Form load times (<500ms)
│   ├── test_api_latency.py            # API response times (TODO)
│   └── test_concurrent_users.py       # Load testing 100+ users (TODO)
├── browser_compat/
│   ├── test_chrome.py                  # Chrome compatibility (TODO)
│   ├── test_firefox.py                 # Firefox compatibility (TODO)
│   ├── test_safari.py                  # Safari compatibility (TODO)
│   └── test_mobile.py                  # Mobile/iOS compatibility (TODO)
├── regression/
│   ├── test_rbac_enforcement.py        # Phase 4 state-based access
│   └── test_compliance_validation.py   # Phase 5 question whitelist
└── README.md                            # This file
```

## Quick Start

### Install Dependencies

```bash
# Add to requirements.txt and install
pip install playwright pytest-playwright pytest-django pytest-asyncio

# Install browser binaries
playwright install
```

### Run Tests

```bash
# All tests
pytest tests/e2e/ -v

# Only critical paths (fastest)
pytest tests/e2e/critical_paths/ -v

# Only regression (Phase 4-5 validation)
pytest tests/e2e/regression/ -v

# Only performance
pytest tests/e2e/performance/ -v -m performance

# Specific test
pytest tests/e2e/critical_paths/test_candidate_flow.py::TestCandidateSignupFlow::test_candidate_qr_entry_to_profile_creation -v

# With browser UI visible
pytest tests/e2e/ --headed

# With videos on failure
pytest tests/e2e/ --video=retain-on-failure

# With specific browser
pytest tests/e2e/ --browser=firefox
```

## Test Markers

```bash
# E2E tests only
pytest tests/e2e/ -m e2e

# Performance tests
pytest tests/e2e/ -m performance

# Regression tests
pytest tests/e2e/ -m regression

# Skip slow tests
pytest tests/e2e/ -m "not slow"
```

## Fixtures

All fixtures defined in `conftest.py`:

- `page` — Playwright page object (browser automation)
- `live_server` — Django test server URL
- `db_setup` — Multi-tenant database setup
- `authenticated_client` — HTTP client with auth
- `store_with_questionnaire` — Pre-configured store + template
- `candidate_profile` — Test candidate with answers
- `relation_*` — Relations in various states
- `measure_load_time()` — Performance measurement
- `measure_query_count()` — Database query analysis
- `measure_api_latency()` — API latency tracking

## Critical Paths Tested

### 1. Candidate Flow
- **File**: `critical_paths/test_candidate_flow.py`
- **Flow**: QR entry → store select → action choose → form fill → OTP verify → profile created → view matches → declare interest → accept employer → enable contact
- **Tests**: 6 test classes, 60+ assertions
- **Duration**: ~5 minutes per full run

### 2. Employer Flow (TODO)
- **File**: `critical_paths/test_employer_flow.py`
- **Flow**: Create opportunity → view candidates → declare interest → see match → enable contact → send response
- **Tests**: 5 test classes (to be implemented)
- **Duration**: ~3 minutes per full run

### 3. Store Flow (TODO)
- **File**: `critical_paths/test_store_flow.py`
- **Flow**: Create template → add questions → verify compliance → candidate completes → view responses
- **Tests**: 4 test classes (to be implemented)
- **Duration**: ~2 minutes per full run

## Performance Baselines

| Metric | Target | Current |
|--------|--------|---------|
| Store chooser load | <500ms | - |
| Action chooser load | <500ms | - |
| Form load | <500ms | - |
| First field interactive | <200ms | - |
| Form submission | <1s | - |
| No layout shift (CLS) | <0.1 | - |

## Regression Suite

### Phase 4: RBAC Enforcement
- **File**: `regression/test_rbac_enforcement.py`
- **Coverage**: All state transitions and access control
- **Tests**: 20+ test methods
- **Time**: ~2 minutes

### Phase 5: Compliance Validation
- **File**: `regression/test_compliance_validation.py`
- **Coverage**: Whitelist, blacklist, ops approval, audit logs
- **Tests**: 25+ test methods
- **Time**: ~2 minutes

## Browser Compatibility (TODO)

Will test across:
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- iOS 14+
- Android 12+

## CI/CD Integration (TODO)

GitHub Actions workflow:
- Runs on: push to main, PR creation
- Triggers: All critical paths + regression suite
- Reports: Screenshots/videos on failure
- Duration: ~15 minutes

## Troubleshooting

### "No tenant for hostname" Error
**Cause**: Multi-tenant setup requires proper domain configuration

**Solution**: Use `live_server` fixture which handles domain setup

### Database State Pollution
**Cause**: Tests not cleaning up data between runs

**Solution**: All fixtures use Django test transactions (auto-rollback)

### Timeout on Slow Network
**Cause**: Default timeouts too short

**Solution**: Increase timeout: `page.wait_for_selector(..., timeout=5000)`

### Screenshots Not Saving
**Cause**: Directory doesn't exist

**Solution**: Ensure `screenshots/` and `videos/` directories exist

### Mobile Tests Fail on Desktop CI
**Cause**: No actual mobile devices available

**Solution**: Use Playwright's `device` fixture for emulation

## Next Steps

1. **Complete Critical Paths**: Employer flow and store flow tests
2. **Add Performance Tests**: Concurrent users, API latency, database optimization
3. **Browser Compatibility**: Test across Chrome, Firefox, Safari, Mobile
4. **CI/CD Pipeline**: Setup GitHub Actions for automated testing
5. **Load Testing**: Validate platform stability at scale

---

For detailed documentation, see [docs/QR_REDESIGN_PHASE6_E2E_TESTING.md](../../docs/QR_REDESIGN_PHASE6_E2E_TESTING.md)
