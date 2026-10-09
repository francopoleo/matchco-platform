"""Fase 2 — unidade física participando de programas sem duplicação."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from recruitment.domain_models import RecruitmentCompany, RecruitmentOrganization, RecruitmentStore
from recruitment.models import Program, ProgramUnitScope


class ProgramUnitScopeTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='phase-2-org', slug='phase-2-org', name='Phase 2',
        )
        company = RecruitmentCompany.objects.create(organization=self.org, name='Rede')
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=company, name='Unidade compartilhada',
        )

    def test_one_unit_can_participate_in_multiple_programs(self):
        first = Program.objects.create(
            organization=self.org, name='Shopping', kind=Program.KIND_RECRUITMENT,
        )
        second = Program.objects.create(
            organization=self.org, name='Rede nacional', kind=Program.KIND_RECRUITMENT,
        )

        ProgramUnitScope.objects.create(program=first, business_unit=self.store)
        ProgramUnitScope.objects.create(program=second, business_unit=self.store)

        self.assertEqual(self.store.program_scopes.count(), 2)

    def test_scope_rejects_cross_organization_program(self):
        other = RecruitmentOrganization.objects.create(
            external_id='phase-2-other', slug='phase-2-other', name='Outra organização',
        )
        program = Program.objects.create(
            organization=other, name='Programa externo', kind=Program.KIND_RECRUITMENT,
        )
        scope = ProgramUnitScope(program=program, business_unit=self.store)

        with self.assertRaises(ValidationError):
            scope.full_clean()

