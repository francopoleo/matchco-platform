from types import SimpleNamespace

from django.test import SimpleTestCase

from .services import EligibilityService


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
