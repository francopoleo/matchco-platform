"""Fase 2 — Opportunity versionada + Pre-Interest Set + material change bump."""
from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from recruitment.models import (
    CanonicalCatalog, CanonicalFunctionMapping, CanonicalTerm,
    CandidateProfile, Relation,
    Position as Opportunity,
    OpportunityCriterion,
    OpportunityVersionHistory,
    CandidateIdentity, CandidateConsent, EntryPoint,
)
from recruitment.domain_models import (
    RecruitmentOrganization,
    RecruitmentCompany,
    RecruitmentStore,
    RecruitmentJobFunction,
)
from recruitment.services import (
    deliver_opportunity_notice, expire_invitation_rounds, open_invitation_round,
    person_interested, request_negotiation, record_candidate_context,
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


class InvitationRoundLifecycleTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='round-org', slug='round-org', name='Rodadas',
        )
        self.company = RecruitmentCompany.objects.create(organization=self.org, name='Rede')
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=self.company, name='Unidade',
        )
        self.function = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.company, name='Caixa',
        )
        catalog = CanonicalCatalog.objects.create(
            code='round-catalog', name='Varejo', version=1,
            status=CanonicalCatalog.STATUS_PUBLISHED,
        )
        term = CanonicalTerm.objects.create(
            catalog=catalog, term_type=CanonicalTerm.TYPE_FUNCTION,
            code='round-cashier', label='Caixa de loja', normalized_label='caixa de loja',
        )
        CanonicalFunctionMapping.objects.create(
            term=term, job_function=self.function, organization=self.org,
        )
        self.position = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.function,
            title='Caixa', state=Opportunity.STATE_ACTIVATED,
            pre_interest_set_complete=True, requested_slots=4, invite_batch_size=2,
            candidate_response_hours=1, negotiable_fields=['period'],
        )
        self.candidates = [
            CandidateProfile.objects.create(
                organization=self.org, first_name=f'Pessoa {index}',
                email=f'round-{index}@example.com',
            )
            for index in range(3)
        ]
        for candidate in self.candidates:
            candidate.job_functions.add(self.function)
            identity = CandidateIdentity.objects.create(
                email_normalized=candidate.email.lower(),
            )
            candidate.identity = identity
            candidate.save(update_fields=['identity', 'updated_at'])
            entry_point = EntryPoint.objects.create(
                organization=self.org, kind=EntryPoint.KIND_STORE,
                scope_store=self.store, label=f'QR {candidate.pk}',
                canonical_destination_url=f'https://matchco.test/qr/{candidate.pk}',
            )
            record_candidate_context(candidate=candidate, entry_point=entry_point)
            CandidateConsent.objects.create(
                identity=identity, organization=self.org,
                purpose=CandidateConsent.PURPOSE_CIRCULATION_STORE,
                granted=True, policy_version='round-test',
                source=f'entry_point:{entry_point.pk}',
            )

    def test_round_is_batched_and_does_not_rank_people(self):
        result = open_invitation_round(opportunity=self.position)
        self.assertEqual(result['created'], 2)
        self.assertEqual(
            list(Relation.objects.filter(opportunity=self.position).order_by('candidate_id').values_list('candidate_id', flat=True)),
            [candidate.pk for candidate in self.candidates[:2]],
        )

    def test_expired_round_waits_then_invites_only_new_eligible_people(self):
        now = timezone.now()
        open_invitation_round(opportunity=self.position, now=now)
        expired = expire_invitation_rounds(now=now + timezone.timedelta(hours=2))
        self.assertEqual(expired['expired_notices'], 2)

        waiting = open_invitation_round(
            opportunity=self.position, now=now + timezone.timedelta(hours=2),
        )
        self.assertTrue(waiting['waiting'])
        next_round = open_invitation_round(
            opportunity=self.position, now=now + timezone.timedelta(hours=26),
        )
        self.assertEqual(next_round['created'], 1)
        self.assertEqual(
            Relation.objects.filter(opportunity=self.position, state=Relation.STATE_NOTICE_DELIVERED).count(),
            1,
        )

    def test_store_decision_deadline_expires_and_only_declared_fields_can_be_negotiated(self):
        now = timezone.now()
        relation = deliver_opportunity_notice(
            candidate=self.candidates[0], opportunity=self.position,
        )
        person_interested(relation=relation)
        Relation.objects.filter(pk=relation.pk).update(
            employer_decision_expires_at=now - timezone.timedelta(minutes=1),
        )
        expired = expire_invitation_rounds(now=now)
        self.assertEqual(expired['expired_decisions'], 1)
        relation.refresh_from_db()
        self.assertEqual(relation.state, Relation.STATE_NO_EMPLOYER_INTEREST)

        relation = deliver_opportunity_notice(
            candidate=self.candidates[1], opportunity=self.position,
        )
        person_interested(relation=relation)
        request_negotiation(
            relation=relation, fields=['period'],
            proposal={'period': 'evening'}, actor_type='candidate',
        )
        self.assertEqual(relation.negotiation_fields, ['period'])
        with self.assertRaises(ValueError):
            request_negotiation(
                relation=relation, fields=['start_date'],
                proposal={'start_date': '2026-11-01'}, actor_type='candidate',
            )
