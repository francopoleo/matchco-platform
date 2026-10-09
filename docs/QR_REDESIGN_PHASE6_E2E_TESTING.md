---
name: QR Redesign Phase 6 E2E Testing & Performance
description: Complete end-to-end testing suite for QR redesign critical paths
type: reference
---

# Phase 6: E2E Testing & Performance

**Phase**: 6 of 6  
**Status**: 🚀 Ready to Implement  
**Date**: 2026-10-09  
**Priority**: High (Go-to-Market)  
**Estimated Timeline**: 2-3 weeks

---

## Objective

Validate all critical user flows work end-to-end across browsers, stress-test platform capacity, and establish performance baselines before production launch.

**Key Goals**:
- ✅ Full coverage of 3 critical paths (candidate, employer, store)
- ✅ Detect regressions in new code
- ✅ Ensure browser compatibility (desktop + mobile)
- ✅ Establish performance baselines (latency, throughput, stability)
- ✅ Identify bottlenecks under load

---

## Architecture

### Testing Stack

**Framework**: [Playwright](https://playwright.dev/) (Python)
- Multi-browser support (Chrome, Firefox, Safari, Edge)
- Mobile emulation (iOS, Android)
- Auto-waits for elements (no flaky tests)
- Network interception (mock external APIs)
- Screenshots/videos on failure

**Why Playwright over Selenium**:
- Better mobile support
- Auto-retry logic reduces flakiness
- Faster execution
- Better documentation
- WSL/Docker friendly

### Test Structure

```
tests/e2e/
├── conftest.py                 ← Fixtures, setup/teardown
├── critical_paths/
│   ├── test_candidate_flow.py  ← Candidate signup → contact
│   ├── test_employer_flow.py   ← Employer matching → interest
│   └── test_store_flow.py      ← Store questions → responses
├── performance/
│   ├── test_form_load.py       ← Form render times
│   ├── test_api_latency.py     ← Backend response times
│   └── test_concurrent_users.py ← Load under 100+ concurrent
├── browser_compat/
│   ├── test_chrome.py
│   ├── test_firefox.py
│   ├── test_safari.py
│   └── test_mobile.py
└── regression/
    ├── test_rbac_enforcement.py ← Phase 4 checks
    ├── test_compliance_validation.py ← Phase 5 checks
    └── test_data_integrity.py
```

---

## Critical Path Tests

### Path 1: Candidate Complete Flow

**Scenario**: Candidate signs up, matches with opportunity, declares interest, enables contact

**Steps**:
1. Navigate to QR entry point
2. Select store from dropdown
3. Choose "Create Profile" action
4. Fill questionnaire (all question types):
   - Text input (name)
   - Boolean (willing to work weekends)
   - Select (preferred shift)
   - Date (available start date)
   - Scale rating (experience level)
5. Enter phone & email
6. Submit OTP verification
7. **Verify**: CandidateProfile created
8. **Verify**: Can view "Matches" tab after match algorithm runs
9. Declare interest in matching opportunity
10. **Verify**: Relation state transitions to PERSON_INTERESTED
11. Receive employer interest notification
12. Accept employer interest → EMPLOYER_INTERESTED
13. See MATCHED state → enable contact
14. **Verify**: Contact information visible to employer

**Assertions**:
```python
# Profile created with all answers
profile = CandidateProfile.objects.filter(mobile=phone).first()
assert profile is not None
assert len(profile.signup_answers) == 5  # All questions answered

# Relation state progression
relation = Relation.objects.filter(candidate_profile=profile).first()
assert relation.state in [STATE_PERSON_INTERESTED, STATE_EMPLOYER_INTEREST_VIEW, ...]

# Contact enabled after match
assert relation.state == STATE_CONTACT_ENABLED
assert relation.candidate_contact_enabled_at is not None
```

**Timing**: ~3-5 minutes per run (includes wait for match algorithm)

---

### Path 2: Employer Matching & Interest Flow

**Scenario**: Employer declares hiring need, reviews candidates, declares interest, exchanges contact

**Steps**:
1. Employer logs into portal
2. Creates opportunity (position, requirements)
3. Triggers matching algorithm (or waits for scheduled run)
4. **Verify**: Candidates appear in "Candidates" tab
5. Click "View Detail" on candidate in EMPLOYER_INTEREST_VIEW state
6. Review candidate profile & answers
7. Click "Interessar" (declare interest)
8. **Verify**: Relation transitions to EMPLOYER_INTERESTED
9. Wait for candidate to also declare interest
10. **Verify**: Relation becomes MATCHED
11. Click "Liberar Contato" (enable contact)
12. **Verify**: Contact information appears, can reply

**Assertions**:
```python
# Employer can only view candidates in allowed states
for relation in employer.relations:
    if relation.state not in VIEWABLE_STATES:
        # GET detail should return 403
        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 403
    else:
        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 200

# Interest declaration enforces state machine
relation = Relation.objects.get(...)
assert relation.state == STATE_EMPLOYER_INTEREST_VIEW
response = client.post(f'/portal/relation/{relation.id}/interessar/')
assert response.status_code == 302  # Redirect (success)
relation.refresh_from_db()
assert relation.state == STATE_EMPLOYER_INTERESTED
```

**Timing**: ~2-3 minutes per run

---

### Path 3: Store Custom Questions & Responses

**Scenario**: Store admin defines custom questions, receives candidate responses

**Steps**:
1. Store admin logs into console
2. Navigate to "Questions" section
3. Create 3-5 new questions:
   - "Experiência com POS?" (boolean) → APPROVED ✅
   - "Conhece SQL?" (text) → APPROVED ✅
   - "Qual sua formação?" (text) → REQUIRES_OPS_APPROVAL 🟡
4. **Verify**: Auto-compliance checking ran
5. **Verify**: Approved questions appear in signup form
6. **Verify**: Ambiguous question flagged for ops review
7. Candidate completes signup with new questions
8. **Verify**: Answers stored in CandidateSignupAnswer
9. Store admin views "Responses" dashboard
10. **Verify**: Can see all candidate responses

**Assertions**:
```python
# Question compliance auto-check
question = QuestionnaireQuestion.objects.create(
    label="Tem experiência com caixa?",
    field_type='boolean'
)
assert question.compliance_status == 'approved'

# Ambiguous question flagged
question2 = QuestionnaireQuestion.objects.create(
    label="Fale sobre você"
)
assert question2.compliance_status == 'requires_ops_approval'

# Audit log created
audit = QuestionAuditLog.objects.filter(question=question).first()
assert audit.action == 'created'
assert audit.compliance_flag in [True, False]
```

**Timing**: ~2 minutes per run

---

## Performance Tests

### Test 1: Form Load Time

**Goal**: Form renders in <200ms, full questionnaire interactive in <500ms

```python
@pytest.mark.performance
def test_custom_signup_form_load(page, live_server):
    """Measure time to interactive for signup form"""
    start = time.time()
    page.goto(f"{live_server}/candidato/formulario/")
    
    # Wait for form fully interactive
    page.wait_for_selector("input[name='responses']", timeout=2000)
    
    load_time = (time.time() - start) * 1000
    assert load_time < 500, f"Form took {load_time}ms (target: <500ms)"
    
    # Measure first question render
    first_q_time = measure_element_paint_time(page, ".question-0")
    assert first_q_time < 200
```

### Test 2: API Latency Under Load

**Goal**: Backend maintains <500ms p99 latency under 100 concurrent requests

```python
@pytest.mark.performance
async def test_candidate_profile_creation_under_load():
    """Create 100 concurrent profiles, measure latency"""
    
    async with asyncio.TaskGroup() as tg:
        results = []
        for i in range(100):
            result = await tg.create_task(
                create_candidate_profile(
                    mobile=f"+5511998765{i:03d}",
                    email=f"candidate{i}@test.com"
                )
            )
            results.append(result)
    
    # Measure latencies
    latencies = [r['duration_ms'] for r in results]
    p50 = statistics.median(latencies)
    p99 = np.percentile(latencies, 99)
    
    assert p99 < 500, f"p99 latency: {p99}ms (target: <500ms)"
    assert sum(r['success'] for r in results) > 98  # >98% success
```

### Test 3: Database Query Count

**Goal**: No N+1 queries, critical views <5 queries

```python
@pytest.mark.performance
def test_relation_detail_view_queries(django_db_blocker, client, relation):
    """Verify relation detail doesn't trigger N+1"""
    with django_db_blocker.unblock():
        with django.test.utils.CaptureQueriesContext(connection) as ctx:
            response = client.get(f'/portal/relation/{relation.id}/')
            
            # Should fetch: relation + related data
            assert len(ctx.captured_queries) < 5, \
                f"Got {len(ctx)} queries, optimize the view"
```

---

## Browser Compatibility Matrix

| Browser | Desktop | Mobile | Status |
|---------|---------|--------|--------|
| Chrome | ✅ Latest 2 versions | ✅ Android 12+ | Critical |
| Firefox | ✅ Latest 2 versions | - | Important |
| Safari | ✅ Latest 2 versions | ✅ iOS 14+ | Important |
| Edge | ✅ Latest version | - | Nice-to-have |

**Responsive Tests**:
```python
@pytest.mark.parametrize("viewport", [
    {"width": 1920, "height": 1080},  # Desktop
    {"width": 768, "height": 1024},   # Tablet
    {"width": 375, "height": 667},    # Mobile
])
def test_signup_responsive(page, viewport):
    page.set_viewport_size(**viewport)
    page.goto("/candidato/loja/escolher/")
    
    # Verify all buttons clickable, no horizontal scroll
    page.click("button:has-text('Continue')")
    assert not page.locator("body").evaluate("el => el.scrollWidth > window.innerWidth")
```

---

## Regression Test Suite

### RBAC Enforcement (Phase 4)

```python
class TestRBACEnforcement:
    """Verify Phase 4: State-based access control"""
    
    def test_cannot_view_notice_delivered_relation(self, client, relation_notice):
        """Employer cannot view candidate before PERSON_INTERESTED"""
        response = client.get(f'/portal/relation/{relation_notice.id}/')
        assert response.status_code == 403
        assert "manifestar interesse" in response.content.decode()
    
    def test_cannot_declare_interest_before_allowed_state(self, client, relation_notice):
        """Can only declare interest from EMPLOYER_INTEREST_VIEW"""
        response = client.post(f'/portal/relation/{relation_notice.id}/interessar/')
        assert response.status_code == 302  # Redirect (prevented)
    
    def test_cannot_enable_contact_before_match(self, client, relation_employer_interested):
        """Contact channel opens only after bilateral MATCHED"""
        response = client.post(f'/portal/relation/{relation_employer_interested.id}/liberar-contato/')
        assert "Aguarde confirmação bilateral" in str(response.messages)
```

### Compliance Validation (Phase 5)

```python
class TestComplianceValidation:
    """Verify Phase 5: Question whitelist/blacklist"""
    
    def test_whitelist_question_auto_approved(self, admin_client):
        """Whitelist match → auto-approved"""
        response = admin_client.post('/console/questionnaire/question/add/', {
            'label': 'Tem experiência em vendas?',
            'field_type': 'boolean',
        })
        q = QuestionnaireQuestion.objects.latest('id')
        assert q.compliance_status == 'approved'
    
    def test_blacklist_question_rejected(self, admin_client):
        """Blacklist match → rejected"""
        response = admin_client.post('/console/questionnaire/question/add/', {
            'label': 'Qual sua idade?',
            'field_type': 'text',
        })
        assert response.status_code == 200  # Form redisplayed
        assert "violates compliance" in response.content.decode()
    
    def test_ambiguous_question_requires_ops_approval(self, admin_client):
        """No pattern match → flagged for ops"""
        response = admin_client.post('/console/questionnaire/question/add/', {
            'label': 'Fale sobre você',
            'field_type': 'textarea',
        })
        q = QuestionnaireQuestion.objects.latest('id')
        assert q.compliance_status == 'requires_ops_approval'
        
        # Audit log created
        audit = QuestionAuditLog.objects.get(question=q, action='created')
        assert audit.compliance_flag is True
```

---

## Setup & Execution

### Install Dependencies

```bash
# Add to requirements.txt
pip install playwright pytest-playwright pytest-asyncio pytest-django django-webtest

# Install browser binaries
playwright install
```

### Configure Pytest

**pytest.ini**:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = matchco.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    e2e: end-to-end tests
    performance: performance tests
    regression: regression tests
    slow: slow tests
asyncio_mode = auto
```

### Run Tests Locally

```bash
# All E2E tests
pytest tests/e2e/ -v

# Only critical paths (fast)
pytest tests/e2e/critical_paths/ -v -m "not slow"

# Performance tests (requires load testing setup)
pytest tests/e2e/performance/ -v --performance

# Specific browser
pytest tests/e2e/ --browser=firefox

# With screenshots/videos on failure
pytest tests/e2e/ --headed --video=retain-on-failure

# Regression suite only
pytest tests/e2e/regression/ -v
```

### CI/CD Integration

**GitHub Actions** (.github/workflows/e2e-tests.yml):
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - run: pip install -r requirements.txt
      - run: playwright install --with-deps
      
      - run: python manage.py migrate
      - run: pytest tests/e2e/critical_paths/ -v
      - run: pytest tests/e2e/regression/ -v
      
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## Success Criteria

### Coverage
- ✅ All 3 critical paths pass end-to-end
- ✅ 100% of RBAC state transitions tested
- ✅ 100% of compliance validation scenarios tested
- ✅ Mobile viewport passes all tests

### Performance
- ✅ Form renders in <500ms
- ✅ API p99 latency <500ms under 100 concurrent users
- ✅ Database queries: <5 per view
- ✅ No memory leaks under sustained load (1000+ requests)

### Reliability
- ✅ Tests pass consistently (no flakiness)
- ✅ Pass rate: >98% across all browsers
- ✅ Video evidence for all failures

### Browser Compatibility
- ✅ Chrome, Firefox, Safari all pass critical paths
- ✅ Mobile: iOS 14+, Android 12+ pass
- ✅ No layout shifts on viewport changes

---

## Timeline & Milestones

### Week 1: Test Infrastructure
- Day 1-2: Setup Playwright, create fixtures, test environment
- Day 3: Implement critical path 1 (candidate flow)
- Day 4-5: Implement paths 2 & 3, establish baseline

**Deliverable**: All 3 critical paths passing, baseline metrics

### Week 2: Performance & Regression
- Day 1-2: Performance tests (load, latency, queries)
- Day 3: Regression suite (Phase 4 RBAC, Phase 5 compliance)
- Day 4-5: Browser compatibility (Chrome, Firefox, Safari, Mobile)

**Deliverable**: Performance report, regression test suite, browser matrix

### Week 3: Hardening & Go-Live
- Day 1-2: Fix failures, optimize bottlenecks
- Day 3: Load testing (1000+ concurrent)
- Day 4: Documentation & runbooks
- Day 5: CI/CD integration, final sign-off

**Deliverable**: Production-ready test suite, monitoring alerts configured

---

## Known Limitations & Future

### Phase 6 (Now)
- ✅ E2E test suite (Playwright)
- ✅ Critical path coverage
- ✅ Performance baselines
- ✅ Regression suite
- ✅ Browser compatibility

### Future Enhancements
- [ ] Visual regression testing (Percy, Applitools)
- [ ] Accessibility testing (WCAG 2.1 compliance)
- [ ] Security testing (OWASP top 10)
- [ ] Chaos engineering (failure scenario testing)
- [ ] Continuous monitoring (NewRelic/DataDog)

---

## Troubleshooting

### Tests Timeout on Slow Network
**Fix**: Increase timeout, use `expect(locator).to_be_visible(timeout=10000)`

### Database State Pollution Between Tests
**Fix**: Use `@pytest.fixture(autouse=True)` with rollback after each test

### Mobile Tests Fail on Desktop CI
**Fix**: Use Playwright's `device` fixture for iOS/Android emulation

### Screenshots/Videos Not Capturing
**Fix**: Run with `--headed` to show browser, add `--video=on`

---

## Related Documents

- **Phase 1-3**: See `QR_REDESIGN_IMPLEMENTATION_SUMMARY.md`
- **Phase 4**: See `QR_REDESIGN_PHASE4_RBAC.md`
- **Phase 5**: See `QR_REDESIGN_PHASE5_ADMIN_VALIDATION.md`
- **Master Guide**: See `QR_REDESIGN_MASTER_GUIDE.md`
- **Architecture**: See `CODEBASE_MAP.md`

---

## Code Changes Summary

| Component | Files | Lines |
|-----------|-------|-------|
| Test infrastructure | `conftest.py`, `fixtures.py` | ~150 |
| Critical path tests | 3 test files | ~400 |
| Performance tests | 3 test files | ~250 |
| Regression tests | 3 test files | ~300 |
| CI/CD config | `.github/workflows/e2e-tests.yml` | ~50 |
| **Total** | **~12 files** | **~1150** |

---

**Status**: 🚀 Phase 6 Ready | Ready to implement | Timeline: 2-3 weeks from kickoff
