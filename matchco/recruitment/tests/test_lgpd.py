"""Fase 6 — LGPD granular + RightsCase + Age gate + Retention."""
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from recruitment.models import (
    CandidateConsent, CandidateIdentity, Ledger, RetentionClass, RightsCase,
)
from recruitment.services import (
    AgeGateFailure, apply_retention_policy, enforce_age_gate,
    open_rights_case,
)


class AgeGateTests(TestCase):
    def test_18_or_older_passes(self):
        self.assertTrue(enforce_age_gate(date(2000, 1, 1)))

    def test_under_18_blocks_and_logs(self):
        n = Ledger.objects.count()
        with self.assertRaises(AgeGateFailure):
            enforce_age_gate(date.today() - timedelta(days=365 * 10))
        # RT-06: nenhum dado do requerente é armazenado, mas o gate falho vira evento anônimo.
        self.assertEqual(Ledger.objects.count(), n + 1)
        ev = Ledger.objects.order_by('-occurred_at').first()
        self.assertTrue(ev.metadata.get('gate_failed'))
        self.assertIsNone(ev.candidate)

    def test_missing_birth_date_blocks(self):
        with self.assertRaises(AgeGateFailure):
            enforce_age_gate(None)


class RightsCaseTests(TestCase):
    def test_create_generates_ref_and_ledger(self):
        n_ledger = Ledger.objects.count()
        case = open_rights_case(
            requester_email='titular@ex.com',
            request_type=RightsCase.TYPE_ACCESS,
        )
        self.assertTrue(case.case_ref.startswith('RC-'))
        self.assertEqual(case.action_state, RightsCase.ACTION_OPEN)
        self.assertEqual(case.verification_state, RightsCase.VERIFICATION_PENDING)
        self.assertEqual(Ledger.objects.count(), n_ledger + 1)
        self.assertTrue(
            Ledger.objects.filter(event_type='RIGHTS_REQUEST').exists()
        )

    def test_case_ref_unique(self):
        with patch('recruitment.services._generate_case_ref', side_effect=['RC-FIXED', 'RC-OTHER']):
            open_rights_case(requester_email='a@ex.com', request_type='access')
            open_rights_case(requester_email='b@ex.com', request_type='access')
        refs = list(RightsCase.objects.values_list('case_ref', flat=True))
        self.assertEqual(sorted(refs), ['RC-FIXED', 'RC-OTHER'])


class ConsentGranularityTests(TestCase):
    def test_new_purposes_available(self):
        identity = CandidateIdentity.objects.create(email_normalized='a@ex.com')
        for purpose in [
            CandidateConsent.PURPOSE_CIRCULATION_STORE,
            CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
            CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
            CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
            CandidateConsent.PURPOSE_VISIBILITY_MATCH,
            CandidateConsent.PURPOSE_INTEGRATION_COURSES,
            CandidateConsent.PURPOSE_INTEGRATION_CERTIFICATIONS,
        ]:
            CandidateConsent.objects.create(
                identity=identity, purpose=purpose,
                policy_version='v1', granted=True,
                legal_basis=CandidateConsent.BASIS_CONSENT,
            )
        self.assertEqual(identity.consents.count(), 7)

    def test_legal_basis_captured(self):
        identity = CandidateIdentity.objects.create(email_normalized='b@ex.com')
        c = CandidateConsent.objects.create(
            identity=identity,
            purpose=CandidateConsent.PURPOSE_TRANSACTIONAL_MESSAGING,
            legal_basis=CandidateConsent.BASIS_CONTRACT_EXECUTION,
            policy_version='v1', granted=True,
        )
        self.assertEqual(c.legal_basis, CandidateConsent.BASIS_CONTRACT_EXECUTION)

    def test_revoke_match_visibility_pauses_profiles(self):
        from recruitment.domain_models import RecruitmentOrganization
        from recruitment.models import CandidateProfile
        from recruitment.services import revoke_consent

        organization = RecruitmentOrganization.objects.create(
            external_id='consent-org', slug='consent-org', name='Consent Org',
        )
        identity = CandidateIdentity.objects.create(email_normalized='visible@ex.com')
        profile = CandidateProfile.objects.create(
            organization=organization, identity=identity,
            first_name='Pessoa', email='visible@ex.com',
            visibility_match=True,
            circulation_state=CandidateProfile.CIRCULATION_ALLOWED,
        )
        CandidateConsent.objects.create(
            identity=identity, organization=organization,
            purpose=CandidateConsent.PURPOSE_VISIBILITY_MATCH,
            policy_version='v1', granted=True,
        )

        revoke_consent(
            identity=identity,
            organization=organization,
            purpose=CandidateConsent.PURPOSE_VISIBILITY_MATCH,
        )

        profile.refresh_from_db()
        self.assertFalse(profile.visibility_match)
        self.assertEqual(profile.circulation_state, CandidateProfile.CIRCULATION_PAUSED)


class RetentionTests(TestCase):
    def test_dry_run_reports_without_side_effects(self):
        n_ledger = Ledger.objects.count()
        report = apply_retention_policy(dry_run=True)
        self.assertTrue(report['dry_run'])
        self.assertIn('RT-02', report['actions'])
        self.assertIn('RT-03', report['actions'])
        # Nenhum evento novo em dry-run.
        self.assertEqual(Ledger.objects.count(), n_ledger)

    def test_defaults_have_expected_classes(self):
        self.assertIsNone(RetentionClass.DEFAULT_DAYS[RetentionClass.RT01_ACTIVE_RELATION])
        self.assertEqual(RetentionClass.DEFAULT_DAYS[RetentionClass.RT06_AGE_GATE_FAILURE], 0)
        self.assertGreaterEqual(RetentionClass.DEFAULT_DAYS[RetentionClass.RT04_SECURITY_INCIDENT], 5 * 365)
