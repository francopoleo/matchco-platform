"""Fase 3 — entrada controlada, aprovação e auditoria."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from recruitment.domain_models import RecruitmentOrganization, RecruitmentStore, RecruitmentCompany
from recruitment.models import (
    AccessApprovalEvent, ControlledAccessRequest, Program, ProgramMembership,
)
from recruitment.services import approve_controlled_access, create_controlled_access_request


class ControlledAccessTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='phase-3-org', slug='phase-3-org', name='Phase 3',
        )
        company = RecruitmentCompany.objects.create(organization=self.org, name='Rede')
        self.unit = RecruitmentStore.objects.create(
            organization=self.org, company=company, name='Unidade aprovada',
        )
        self.program = Program.objects.create(
            organization=self.org, name='Talk controlado', kind=Program.KIND_COMMUNICATION,
            status=Program.STATUS_ACTIVE, access_level=Program.ACCESS_MEMBERS,
        )
        User = get_user_model()
        self.person = User.objects.create_user(username='person@example.com', email='person@example.com')
        self.manager = User.objects.create_superuser(
            username='manager@example.com', email='manager@example.com', password='secret123',
        )

    def test_invitation_starts_pending_and_does_not_activate_membership(self):
        access_request = create_controlled_access_request(
            organization=self.org,
            request_type=ControlledAccessRequest.TYPE_PROGRAM,
            email=self.person.email,
            user=self.person,
            program=self.program,
            requested_by=self.person,
        )

        self.assertEqual(access_request.state, ControlledAccessRequest.STATE_PENDING_APPROVAL)
        self.assertFalse(ProgramMembership.objects.filter(user_id=self.person.pk).exists())
        self.assertEqual(access_request.approval_events.count(), 1)

    def test_only_approval_provisions_active_program_membership(self):
        access_request = create_controlled_access_request(
            organization=self.org,
            request_type=ControlledAccessRequest.TYPE_PROGRAM,
            email=self.person.email,
            user=self.person,
            program=self.program,
            requested_by=self.person,
        )

        approve_controlled_access(access_request=access_request, actor=self.manager, reason='Escopo confirmado')

        membership = ProgramMembership.objects.get(user_id=self.person.pk, program=self.program)
        self.assertTrue(membership.active)
        self.assertEqual(membership.state, ProgramMembership.STATE_ACTIVE)
        self.assertEqual(access_request.state, ControlledAccessRequest.STATE_ACTIVE)
        self.assertEqual(
            access_request.approval_events.values_list('action', flat=True).last(),
            AccessApprovalEvent.ACTION_APPROVED,
        )
