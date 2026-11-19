"""Fase 1 — identidade única e histórico de contexto do QR."""

from django.test import TestCase

from recruitment.domain_models import (
    RecruitmentCompany,
    RecruitmentOrganization,
    RecruitmentStore,
)
from django.contrib.auth import get_user_model

from recruitment.models import CandidateAccountLink, CandidateContextEntry, CandidateProfile, EntryPoint
from recruitment.services import (
    IdentityConflict,
    record_candidate_context,
    resolve_or_create_identity,
)


class CandidateIdentityContextTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='phase-1-org', slug='phase-1-org', name='Phase 1',
        )
        company = RecruitmentCompany.objects.create(organization=self.org, name='Lojas')
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=company, name='Unidade A',
        )
        self.entry_point = EntryPoint.objects.create(
            organization=self.org,
            kind=EntryPoint.KIND_STORE,
            scope_store=self.store,
            mode=EntryPoint.MODE_MATCH,
            campaign_name='QR Unidade A',
        )
        self.candidate = CandidateProfile.objects.create(
            organization=self.org,
            first_name='Ana', last_name='Silva',
            email='ana@example.com', phone='5511999990000',
        )

    def test_email_and_phone_reuse_one_identity(self):
        first = resolve_or_create_identity(
            email=' ANA@EXAMPLE.COM ', phone='(11) 99999-0000',
        )
        second = resolve_or_create_identity(
            email='ana@example.com', phone='5511999990000',
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.email_normalized, 'ana@example.com')
        self.assertEqual(first.phone_normalized, '11999990000')

    def test_conflicting_contacts_are_not_merged(self):
        resolve_or_create_identity(email='one@example.com', phone='5511999990001')
        resolve_or_create_identity(email='two@example.com', phone='5511999990002')

        with self.assertRaises(IdentityConflict):
            resolve_or_create_identity(
                email='one@example.com', phone='5511999990002',
            )

    def test_phone_only_identities_do_not_collide_on_empty_email(self):
        first = resolve_or_create_identity(phone='5511999990011')
        second = resolve_or_create_identity(phone='5511999990012')

        self.assertNotEqual(first.pk, second.pk)
        self.assertIsNone(first.email_normalized)
        self.assertIsNone(second.email_normalized)
        self.assertEqual(first.phone_normalized, '5511999990011')

    def test_repeated_qr_updates_one_context_entry(self):
        identity = resolve_or_create_identity(
            email=self.candidate.email, phone=self.candidate.phone,
        )
        self.candidate.identity = identity
        self.candidate.save(update_fields=['identity', 'updated_at'])

        record_candidate_context(candidate=self.candidate, entry_point=self.entry_point)
        context = record_candidate_context(
            candidate=self.candidate,
            entry_point=self.entry_point,
            metadata={'channel': 'qr'},
        )

        self.assertEqual(CandidateContextEntry.objects.count(), 1)
        self.assertEqual(context.visit_count, 2)
        self.assertEqual(context.metadata['channel'], 'qr')

    def test_internal_account_link_preserves_candidate_identity_history(self):
        identity = resolve_or_create_identity(email=self.candidate.email, phone=self.candidate.phone)
        self.candidate.identity = identity
        self.candidate.save(update_fields=['identity'])
        user = get_user_model().objects.create_user(
            username='ana-internal', email='ana-internal@example.com', password='password',
        )
        link = CandidateAccountLink.objects.create(
            user=user, identity=identity, linked_by=user,
            evidence={'verified': True},
        )

        self.assertEqual(link.identity_id, identity.pk)
        self.assertEqual(CandidateProfile.objects.get(pk=self.candidate.pk).identity_id, identity.pk)
        self.assertEqual(identity.account_links.count(), 1)
