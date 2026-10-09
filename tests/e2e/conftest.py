"""
E2E Test Configuration & Fixtures

Provides:
- Browser fixtures (Chrome, Firefox, Safari)
- Django database fixtures
- Test data factories
- Performance measurement utilities
"""

import pytest
import time
import asyncio
from datetime import datetime, timedelta
from django.test.utils import CaptureQueriesContext
from django.db import connection

# Import models
from matchco.recruitment.models import (
    Relation, CandidateProfile, QuestionnaireTemplate,
    QuestionnaireQuestion, StoreSignupConfiguration
)
from matchco.configuration.models import Organization, Store
from matchco.accounts.models import User


# ============================================================================
# BROWSER FIXTURES
# ============================================================================

@pytest.fixture
def browser_context_args(playwright):
    """Configure browser context for E2E tests"""
    return {
        "ignore_https_errors": True,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
    }


@pytest.fixture
async def chromium_launch_args():
    """Chrome launch arguments"""
    return {
        "args": ["--disable-blink-features=AutomationControlled"],
        "headless": True,
    }


@pytest.fixture
async def firefox_launch_args():
    """Firefox launch arguments"""
    return {
        "headless": True,
    }


# ============================================================================
# DJANGO FIXTURES
# ============================================================================

@pytest.fixture
def db_setup(django_db_blocker):
    """Setup test database with multi-tenant context"""
    with django_db_blocker.unblock():
        # Import here to avoid import errors
        from django_tenants.utils import get_public_schema_name

        # Create public tenant (organizations)
        org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            domain="test.local"
        )
        yield org


@pytest.fixture
def authenticated_client(db_setup, client):
    """Return authenticated client with test user"""
    with pytest.raises(Exception):  # We'll create user after
        pass

    # Create test user
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    client.force_login(user)
    client.user = user
    return client


@pytest.fixture
def store_with_questionnaire(db_setup):
    """Create store with pre-configured questionnaire"""
    org = db_setup

    # Create store
    store = Store.objects.create(
        organization=org,
        name="Test Store",
        slug="test-store",
        status="active"
    )

    # Create questionnaire template
    template = QuestionnaireTemplate.objects.create(
        organization=org,
        name="Test Questionnaire",
        slug="test-questionnaire",
        description="Test template"
    )

    # Add questions
    questions_data = [
        {
            "label": "Qual seu nome completo?",
            "field_type": "text",
            "position": 1,
            "required": True,
        },
        {
            "label": "Tem experiência com caixa?",
            "field_type": "boolean",
            "position": 2,
            "required": True,
        },
        {
            "label": "Qual seu turno preferido?",
            "field_type": "single_choice",
            "position": 3,
            "required": True,
            "options": ["Manhã", "Tarde", "Noite"],
        },
        {
            "label": "Quando pode começar?",
            "field_type": "date",
            "position": 4,
            "required": True,
        },
        {
            "label": "Nível de experiência em vendas (1-5)",
            "field_type": "scale",
            "position": 5,
            "required": False,
            "scale_min": 1,
            "scale_max": 5,
        },
    ]

    for q_data in questions_data:
        QuestionnaireQuestion.objects.create(
            template=template,
            **q_data
        )

    # Create configuration linking store to template
    config = StoreSignupConfiguration.objects.create(
        organization=org,
        store=store,
        profile_questionnaire=template,
        job_questionnaire=template,
        is_active=True
    )

    return {
        "store": store,
        "template": template,
        "config": config,
    }


@pytest.fixture
def candidate_profile(db_setup, store_with_questionnaire):
    """Create test candidate profile"""
    profile = CandidateProfile.objects.create(
        mobile="+5511998765432",
        email="candidate@test.com",
        name="Test Candidate",
        organization=db_setup,
    )

    # Add signup answers
    for q in store_with_questionnaire["template"].questions.all():
        profile.signup_answers.append({
            "question_id": q.id,
            "question_label": q.label,
            "field_type": q.field_type,
            "answer": "Test answer" if q.field_type == "text" else True,
        })
    profile.save()

    return profile


@pytest.fixture
def relation_notice_delivered(db_setup, candidate_profile, store_with_questionnaire):
    """Create relation in NOTICE_DELIVERED state"""
    relation = Relation.objects.create(
        organization=db_setup,
        candidate_profile=candidate_profile,
        store=store_with_questionnaire["store"],
        state=Relation.STATE_NOTICE_DELIVERED,
        created_at=datetime.now(),
    )
    return relation


@pytest.fixture
def relation_employer_interest_view(db_setup, candidate_profile, store_with_questionnaire):
    """Create relation in EMPLOYER_INTEREST_VIEW state"""
    relation = Relation.objects.create(
        organization=db_setup,
        candidate_profile=candidate_profile,
        store=store_with_questionnaire["store"],
        state=Relation.STATE_EMPLOYER_INTEREST_VIEW,
        created_at=datetime.now(),
    )
    return relation


@pytest.fixture
def relation_matched(db_setup, candidate_profile, store_with_questionnaire):
    """Create relation in MATCHED state"""
    relation = Relation.objects.create(
        organization=db_setup,
        candidate_profile=candidate_profile,
        store=store_with_questionnaire["store"],
        state=Relation.STATE_MATCHED,
        created_at=datetime.now(),
    )
    return relation


# ============================================================================
# PERFORMANCE MEASUREMENT
# ============================================================================

@pytest.fixture
def measure_load_time():
    """Measure page load time"""
    def _measure(page, url, selector_to_wait=None):
        start = time.time()
        page.goto(url)

        if selector_to_wait:
            page.wait_for_selector(selector_to_wait, timeout=5000)

        duration_ms = (time.time() - start) * 1000
        return {
            "url": url,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(),
        }

    return _measure


@pytest.fixture
def measure_query_count():
    """Measure database query count for a request"""
    def _measure(func):
        with CaptureQueriesContext(connection) as ctx:
            result = func()

        return {
            "query_count": len(ctx.captured_queries),
            "queries": ctx.captured_queries,
            "result": result,
        }

    return _measure


@pytest.fixture
def measure_api_latency():
    """Measure API endpoint latency"""
    async def _measure(client, method, url, data=None, count=10):
        latencies = []

        for _ in range(count):
            start = time.time()

            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, data=data)

            duration_ms = (time.time() - start) * 1000
            latencies.append(duration_ms)

        import statistics
        import numpy as np

        return {
            "endpoint": url,
            "method": method,
            "count": count,
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "mean_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p99_ms": np.percentile(latencies, 99),
            "all_latencies": latencies,
        }

    return _measure


# ============================================================================
# TEST MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line("markers", "e2e: mark test as E2E")
    config.addinivalue_line("markers", "performance: mark test as performance")
    config.addinivalue_line("markers", "regression: mark test as regression")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "browser: mark test for specific browser")


# ============================================================================
# HOOKS
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on test failure"""
    outcome = yield
    rep = outcome.get_result()

    # Attach screenshots for Playwright tests
    if rep.failed and hasattr(item, "funcargs"):
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            screenshot_path = f"screenshots/{item.name}.png"
            page.screenshot(path=screenshot_path)
            rep.sections.append(("screenshot", f"Screenshot: {screenshot_path}"))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running any tests"""
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matchco.settings")

    import django
    django.setup()

    yield

    # Cleanup after all tests
    pass
