"""Fase 2 — Opportunity versionada + Pre-Interest Set + material change bump."""
from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase

from recruitment.models import (
    CanonicalCatalog, CanonicalFunctionMapping, CanonicalTerm,
    Position as Opportunity,
    OpportunityCriterion,
    OpportunityVersionHistory,
)
from recruitment.domain_models import (
    RecruitmentOrganization,
    RecruitmentCompany,
    RecruitmentStore,
    RecruitmentJobFunction,
)


class OpportunityLifecycleTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='org-o', slug='org-o', name='Org O',
        )
        self.company = RecruitmentCompany.objects.create(
            organization=self.org, name='Comp',
        )
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=self.company, name='Loja 1',
        )
        self.func = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.company, name='Repositor',
        )
        catalog = CanonicalCatalog.objects.create(code='opportunity-catalog', name='Varejo', version=1, status=CanonicalCatalog.STATUS_PUBLISHED)
        term = CanonicalTerm.objects.create(catalog=catalog, term_type=CanonicalTerm.TYPE_FUNCTION, code='repositor', label='Repositor', normalized_label='repositor')
        CanonicalFunctionMapping.objects.create(term=term, job_function=self.func, organization=self.org)

    def _min_opportunity(self, **kwargs):
        defaults = dict(
            organization=self.org,
            business_unit=self.store,
            job_function=self.func,
            title='Repositor de loja',
            workplace='Loja 1 — Piso Térreo',
            schedule='Segunda a sábado, 12h-20h',
            work_format=Opportunity.FORMAT_FIXO,
            starts_at=date(2026, 10, 15),
            tag=Opportunity.TAG_PRECISA,
        )
        defaults.update(kwargs)
        return Opportunity.objects.create(**defaults)

    def test_defaults(self):
        opp = self._min_opportunity()
        self.assertEqual(opp.version, 1)
        self.assertEqual(opp.state, Opportunity.STATE_STRUCTURED)
        self.assertEqual(opp.mode, Opportunity.MODE_MATCH)
        self.assertEqual(opp.tag, Opportunity.TAG_PRECISA)

    def test_pre_interest_complete_requires_all_fields_and_criterion(self):
        opp = self._min_opportunity()
        # Sem critério REQUIRED ainda.
        self.assertFalse(opp.compute_pre_interest_complete())

        OpportunityCriterion.objects.create(
            opportunity=opp, label='Falar bem', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        self.assertTrue(opp.compute_pre_interest_complete())

    def test_pre_interest_incomplete_when_missing_field(self):
        opp = self._min_opportunity(schedule='')
        OpportunityCriterion.objects.create(
            opportunity=opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        self.assertFalse(opp.compute_pre_interest_complete())

    def test_can_activate_gates_on_structured_and_complete(self):
        opp = self._min_opportunity()
        OpportunityCriterion.objects.create(
            opportunity=opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        opp.pre_interest_set_complete = True
        opp.save()
        self.assertTrue(opp.can_activate())

        opp.state = Opportunity.STATE_ACTIVATED
        opp.save()
        self.assertFalse(opp.can_activate(), 'ativada não pode reativar')

    def test_opportunity_rejects_cross_organization_unit(self):
        other_org = RecruitmentOrganization.objects.create(
            external_id='org-other', slug='org-other', name='Outra org',
        )
        other_company = RecruitmentCompany.objects.create(
            organization=other_org, name='Outra empresa',
        )
        other_store = RecruitmentStore.objects.create(
            organization=other_org, company=other_company, name='Outra loja',
        )
        opp = self._min_opportunity(business_unit=other_store)
        with self.assertRaises(ValidationError) as caught:
            opp.full_clean()
        self.assertIn('business_unit', caught.exception.message_dict)

    def test_opportunity_rejects_cross_organization_function(self):
        other_org = RecruitmentOrganization.objects.create(
            external_id='org-function-other', slug='org-function-other', name='Outra org',
        )
        other_company = RecruitmentCompany.objects.create(
            organization=other_org, name='Outra empresa',
        )
        other_function = RecruitmentJobFunction.objects.create(
            organization=other_org, company=other_company, name='Outra função',
        )
        opp = self._min_opportunity(job_function=other_function)
        with self.assertRaises(ValidationError) as caught:
            opp.full_clean()
        self.assertIn('job_function', caught.exception.message_dict)


class MaterialChangeVersioningTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='org-m', slug='org-m', name='Org M',
        )
        self.company = RecruitmentCompany.objects.create(
            organization=self.org, name='C',
        )
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=self.company, name='L1',
        )

    def _activated(self, **kwargs):
        opp = Opportunity.objects.create(
            organization=self.org,
            business_unit=self.store,
            title='Teste',
            workplace='X',
            schedule='Y',
            work_format=Opportunity.FORMAT_FIXO,
            starts_at=date(2026, 11, 1),
            tag=Opportunity.TAG_PRECISA,
            state=Opportunity.STATE_ACTIVATED,
        )
        return opp

    def test_material_change_after_activation_bumps_version(self):
        opp = self._activated()
        self.assertEqual(opp.version, 1)

        opp.workplace = 'Novo local'
        opp.save()

        opp.refresh_from_db()
        self.assertEqual(opp.version, 2)
        hist = OpportunityVersionHistory.objects.get(opportunity=opp)
        self.assertEqual(hist.from_version, 1)
        self.assertEqual(hist.to_version, 2)
        self.assertIn('workplace', hist.changed_fields)

    def test_non_material_change_does_not_bump(self):
        opp = self._activated()
        opp.description = 'Descrição atualizada'
        opp.save()
        opp.refresh_from_db()
        self.assertEqual(opp.version, 1)
        self.assertFalse(OpportunityVersionHistory.objects.filter(opportunity=opp).exists())

    def test_structured_edit_never_bumps(self):
        opp = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, title='X',
            state=Opportunity.STATE_STRUCTURED, tag=Opportunity.TAG_PRECISA,
        )
        opp.workplace = 'Loja A'
        opp.schedule = '9-18'
        opp.save()
        opp.refresh_from_db()
        self.assertEqual(opp.version, 1)

    def test_multiple_material_changes_bump_once(self):
        opp = self._activated()
        opp.workplace = 'Novo'
        opp.schedule = 'Outro'
        opp.tag = Opportunity.TAG_SERIA_BOM
        opp.save()
        opp.refresh_from_db()
        self.assertEqual(opp.version, 2)
        hist = OpportunityVersionHistory.objects.get(opportunity=opp)
        self.assertEqual(sorted(hist.changed_fields), sorted(['workplace', 'schedule', 'tag']))
