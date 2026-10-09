from types import SimpleNamespace

from django.test import SimpleTestCase

from .services import EligibilityService
from .selectors import eligible_items


class EligibilityServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = EligibilityService()
        membership = SimpleNamespace(
            organization_id=1,
            company_id=10,
            business_unit_id=100,
            operational_unit_id=None,
            channels=SimpleNamespace(all=lambda: [SimpleNamespace(pk=30)]),
            functions=SimpleNamespace(all=lambda: [SimpleNamespace(pk=20)]),
        )
        self.user = SimpleNamespace(
            is_authenticated=True,
            memberships=SimpleNamespace(
                filter=lambda **kwargs: SimpleNamespace(
                    prefetch_related=lambda *args: [membership]
                )
            ),
        )

    def test_requires_authentication(self):
        decision = self.service.can_view(SimpleNamespace(is_authenticated=False), SimpleNamespace())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, 'authentication_required')

    def test_public_content_is_allowed(self):
        decision = self.service.can_view(self.user, SimpleNamespace(is_published=True, audience_policy=None))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.code, 'organization_content')

    def test_all_policy_requires_every_rule(self):
        policy = SimpleNamespace(
            active=True,
            match_mode='all',
            ALL='all',
            rules=SimpleNamespace(all=lambda: [
                SimpleNamespace(dimension='company', values=[10], negate=False),
                SimpleNamespace(dimension='function', values=[20], negate=False),
            ]),
        )
        decision = self.service.can_view(self.user, SimpleNamespace(is_published=True, audience_policy=policy))
        self.assertTrue(decision.allowed)

    def test_mismatched_policy_is_denied(self):
        policy = SimpleNamespace(
            active=True,
            match_mode='all',
            ALL='all',
            rules=SimpleNamespace(all=lambda: [
                SimpleNamespace(dimension='company_id', values=[999], negate=False),
            ]),
        )
        decision = self.service.can_view(self.user, SimpleNamespace(is_published=True, audience_policy=policy))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, 'audience_mismatch')

    def test_recruitment_context_restricts_platform_organization(self):
        self.user._active_organization_id = 99
        decision = self.service.can_view_with_recruitment_context(
            self.user,
            SimpleNamespace(is_published=True, audience_policy=None),
            {'platform_organization_ids': [1]},
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, 'recruitment_context_mismatch')

    def test_recruitment_context_delegates_to_audience(self):
        self.user._active_organization_id = None
        decision = self.service.can_view_with_recruitment_context(
            self.user,
            SimpleNamespace(is_published=True, audience_policy=None),
            {'platform_organization_ids': [1]},
        )
        self.assertTrue(decision.allowed)

    def test_selector_accepts_recruitment_context(self):
        self.user._active_organization_id = None
        item = SimpleNamespace(is_published=True, audience_policy=None)
        self.assertEqual(
            eligible_items([item], self.user, {'platform_organization_ids': [1]}),
            [item],
        )
