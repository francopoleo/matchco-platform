"""Seed demo MatchCo — cenário completo para demonstração comercial.

Cria: 1 shopping (org), 3 lojas com geo, 2 EntryPoints por loja,
20 candidatos com sinais F0/F1, 8 Opportunities em vários estados do fluxo
bilateral (inclui MATCHED, CONTACT_ENABLED, CLOSED com RC).

Uso:
    python manage.py seed_matchco_demo
    python manage.py seed_matchco_demo --reset    # apaga demo antes
"""
from datetime import date, timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.integrations.signals import (
    on_certification_granted, on_course_completed,
)
from recruitment.models import (
    AuthorityScope, CandidateConsent, CandidateIdentity, CandidateProfile,
    CandidateCanonicalResponse, CanonicalFunctionMapping, CanonicalTerm,
    EmployerActor, EntryPoint, OpportunityCanonicalRequirement,
    OpportunityCriterion,
    Position as Opportunity, Relation,
)
from recruitment.services import (
    create_response, deliver_opportunity_notice, employer_interested,
    enable_contact, person_interested, request_negotiation,
)

User = get_user_model()

SLUG = 'bourbon-shopping'
DEMO_PASSWORD = 'demo123'
DEMO_AUTHORITY_SCOPES = [
    AuthorityScope.AA1_DECLARE_NEED,
    AuthorityScope.AA2_STRUCTURE_OPPORTUNITY,
    AuthorityScope.AA3_ACTIVATE_OPPORTUNITY,
    AuthorityScope.AA4_MODIFY_OPPORTUNITY,
    AuthorityScope.AA5_CLOSE_OPPORTUNITY,
    # AA-6 é necessário para a demonstração mostrar os candidatos interessados.
    AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW,
    AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
    AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
]
STORES_SPEC = [
    ('Farmácia Saúde+', -23.564, -46.652, 'Farmácias BR'),
    ('SuperMerc Central', -23.560, -46.658, 'SuperMerc Rede'),
    ('Moda Rápida', -23.567, -46.647, 'Moda Rápida BR'),
]
FUNCTIONS = [
    'Atendente de caixa', 'Repositor de mercadoria', 'Vendedor(a)',
    'Auxiliar de farmácia', 'Estoquista',
]
FIRST_NAMES = ['Ana', 'Bia', 'Carla', 'Diego', 'Eva', 'Felipe', 'Gabriela',
               'Hugo', 'Ivo', 'Julia', 'Kaike', 'Luana', 'Maria', 'Nina',
               'Otávio', 'Paula', 'Quesia', 'Rafa', 'Sabrina', 'Tiago']


class Command(BaseCommand):
    help = 'Popula um cenário completo MatchCo para demonstração.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true')

    @transaction.atomic
    def handle(self, *args, **opts):
        rnd = random.Random(42)

        if opts['reset']:
            self.stdout.write('Resetando demo...')
            RecruitmentOrganization.objects.filter(slug=SLUG).delete()

        org, _ = RecruitmentOrganization.objects.get_or_create(
            external_id=SLUG, slug=SLUG,
            defaults={'name': 'Shopping MatchCo Demo', 'active': True},
        )
        if not org.active:
            org.active = True
            org.save(update_fields=['active'])
        company, _ = RecruitmentCompany.objects.get_or_create(
            organization=org, name='Demo Holdings',
        )

        # Lojas
        stores = []
        for index, (name, lat, lng, network) in enumerate(STORES_SPEC):
            s, _ = RecruitmentStore.objects.get_or_create(
                organization=org, company=company, name=name,
                defaults={'latitude': lat, 'longitude': lng, 'postal_code': f'013{10 + index:03d}00'},
            )
            if not s.postal_code:
                s.postal_code = f'013{10 + index:03d}00'
                s.save(update_fields=['postal_code'])
            stores.append(s)

        # Funções
        funcs = []
        for fname in FUNCTIONS:
            f, _ = RecruitmentJobFunction.objects.get_or_create(
                organization=org, company=company, name=fname,
            )
            funcs.append(f)

        # De-para por loja: o nome usado pela operação é mantido em
        # ``local_label`` e aponta para o termo canônico usado pelo candidato.
        canonical_by_local = {
            'Atendente de caixa': 'caixa-de-loja',
            'Repositor de mercadoria': 'repositor-de-loja',
            'Vendedor(a)': 'vendedor-de-loja',
            'Auxiliar de farmácia': 'atendente-de-farmacia',
            'Estoquista': 'estoquista-de-loja',
        }
        for store in stores:
            for function in funcs:
                term = CanonicalTerm.objects.filter(
                    catalog__code='market-default', catalog__version=1,
                    code=canonical_by_local[function.name], active=True,
                ).first()
                if term:
                    CanonicalFunctionMapping.objects.update_or_create(
                        term=term, job_function=function, organization=org,
                        business_unit=store,
                        defaults={'local_label': function.name, 'source': 'demo_store_catalog', 'active': True},
                    )

        # Users empregador (um por loja) + EmployerActor completo
        managers = []
        for i, store in enumerate(stores):
            username = f'gerente_{SLUG}_{i}'
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@matchco.demo', 'is_active': True},
            )
            user.set_password(DEMO_PASSWORD)
            user.is_staff = True
            user.is_active = True
            user.save()
            # Membership em uma Organization real do tenant (necessário para
            # o console middleware não redirecionar para /no-access/).
            try:
                from configuration.models import Organization as ConfigOrg, Membership
                console_org = ConfigOrg.objects.filter(active=True).first()
                if console_org:
                    Membership.objects.get_or_create(
                        user=user, organization=console_org,
                        defaults={'role': 'admin', 'active': True, 'is_primary': True},
                    )
            except Exception:
                pass
            EmployerActor.objects.update_or_create(
                user=user, organization=org, business_unit=store,
                defaults={
                    'authority_scopes': DEMO_AUTHORITY_SCOPES,
                    'human_verified_at': timezone.now(),
                    'active': True,
                },
            )
            managers.append((user, store))

        # O usuário usado na demonstração precisa navegar pelas três lojas.
        # O ator sem business_unit funciona como escopo da organização e
        # evita "Sem AA-6" ao abrir uma necessidade de outra loja.
        demo_manager = managers[0][0]
        EmployerActor.objects.update_or_create(
            user=demo_manager, organization=org, business_unit=None,
            defaults={
                'authority_scopes': DEMO_AUTHORITY_SCOPES,
                'human_verified_at': timezone.now(),
                'active': True,
            },
        )

        # Cada loja possui uma única porta Match reutilizável para funções de
        # alto giro.
        entry_points_spec = [
            (f'QR Match · {store.name}', EntryPoint.KIND_STORE, EntryPoint.MODE_MATCH, store, EntryPoint.STATE_ACTIVE)
            for store in stores
        ]
        for label, kind, mode, store, state in entry_points_spec:
            ep, _ = EntryPoint.objects.get_or_create(
                organization=org, label=label,
                defaults={
                    'kind': kind,
                    'scope_store': store,
                    'scope_shopping_id': SLUG if kind == EntryPoint.KIND_SHOPPING else '',
                    'mode': mode,
                    'canonical_destination_url': 'https://direct.ddns.net/qr/pending/',
                    'activation_tested_at': timezone.now() if state in (EntryPoint.STATE_ACTIVE, EntryPoint.STATE_TESTED) else None,
                    'state': state,
                },
            )
            ep.kind = kind
            ep.scope_store = store
            ep.scope_shopping_id = SLUG if kind == EntryPoint.KIND_SHOPPING else ''
            ep.mode = mode
            ep.state = state
            ep.activation_tested_at = timezone.now() if state in (EntryPoint.STATE_ACTIVE, EntryPoint.STATE_TESTED) else None
            ep.canonical_destination_url = f'https://direct.ddns.net/qr/{ep.pk}/'
            ep.save(update_fields=[
                'kind', 'scope_store', 'scope_shopping_id', 'mode', 'state',
                'activation_tested_at', 'canonical_destination_url', 'updated_at',
            ])

        # Candidatos com Identity + Consent + alguns sinais
        candidates = []
        for i, name in enumerate(FIRST_NAMES):
            email = f'{name.lower()}@matchco.demo'
            identity, _ = CandidateIdentity.objects.get_or_create(
                email_normalized=email,
                defaults={'phone_normalized': f'1190000{i:04d}'},
            )
            profile, created = CandidateProfile.objects.get_or_create(
                organization=org, email=email,
                defaults={
                    'identity': identity,
                    'first_name': name,
                    'last_name': f'Silva{i}',
                    'phone': f'1190000{i:04d}',
                    'cep': f'013{10 + i % 3:03d}00',
                    'city': rnd.choice(['Pinheiros', 'Vila Madalena', 'Perdizes']),
                    'state': 'SP',
                    'latitude': -23.560 + rnd.uniform(-0.02, 0.02),
                    'longitude': -46.650 + rnd.uniform(-0.02, 0.02),
                    'experience_years': rnd.choice([0, 1, 2, 3, 5]),
                    'availability_days': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'],
                    'availability_period': 'any',
                    'preferred_work_format': Opportunity.FORMAT_FIXO,
                    'available_from': date.today(),
                    'preferred_store': rnd.choice(stores),
                    'visibility_match': True,
                },
            )
            candidates.append(profile)
            profile.job_functions.add(funcs[i % len(funcs)])
            profile.availability_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            profile.availability_period = 'any'
            profile.preferred_work_format = Opportunity.FORMAT_FIXO
            profile.available_from = date.today()
            profile.save(update_fields=['availability_days', 'availability_period', 'preferred_work_format', 'available_from', 'updated_at'])
            for term in CanonicalTerm.objects.filter(
                function_mappings__job_function=funcs[i % len(funcs)],
                function_mappings__business_unit=profile.preferred_store,
                function_mappings__active=True, active=True,
            ).distinct():
                if not CandidateCanonicalResponse.objects.filter(
                    candidate=profile, term=term,
                    purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
                    source_reference=f'demo:{profile.qr_id}', revoked_at__isnull=True,
                ).exists():
                    CandidateCanonicalResponse.objects.create(
                        candidate=profile, term=term, organization=org,
                        business_unit=profile.preferred_store,
                        scope=CandidateCanonicalResponse.SCOPE_UNIT,
                        purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
                        origin=CandidateCanonicalResponse.ORIGIN_QR,
                        catalog_version=term.catalog.version,
                        value={'experience': 'experienced' if profile.experience_years else 'first_job', 'work_format': Opportunity.FORMAT_FIXO},
                        consented_at=timezone.now(), source_reference=f'demo:{profile.qr_id}',
                    )

            # Consent granular
            for purpose in (
                CandidateConsent.PURPOSE_CIRCULATION_STORE,
                CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
                CandidateConsent.PURPOSE_TRANSACTIONAL_MESSAGING,
            ):
                CandidateConsent.objects.get_or_create(
                    identity=identity, organization=org, purpose=purpose,
                    defaults={
                        'granted': True, 'policy_version': 'v1',
                        'legal_basis': CandidateConsent.BASIS_CONSENT,
                    },
                )
            # Alguns têm consent de integrações
            if i % 3 == 0 and created:
                CandidateConsent.objects.get_or_create(
                    identity=identity, organization=org,
                    purpose=CandidateConsent.PURPOSE_INTEGRATION_COURSES,
                    defaults={'granted': True, 'policy_version': 'v1'},
                )
                on_course_completed(
                    candidate_id=profile.pk, course_key='atendimento_basico',
                    course_name='Atendimento básico ao cliente',
                )
            if i % 5 == 0 and created:
                CandidateConsent.objects.get_or_create(
                    identity=identity, organization=org,
                    purpose=CandidateConsent.PURPOSE_INTEGRATION_CERTIFICATIONS,
                    defaults={'granted': True, 'policy_version': 'v1'},
                )
                on_certification_granted(
                    candidate_id=profile.pk, cert_key='nr35', cert_name='NR-35',
                    valid_until=timezone.now() + timedelta(days=365),
                )

        # Opportunities em vários estados
        opps_spec = [
            (stores[0], funcs[3], 'PRECISA', 'STRUCTURED', 0),
            (stores[0], funcs[0], 'PRECISA', 'ACTIVATED', 3),   # 3 interessados pendentes
            (stores[1], funcs[1], 'SERIA_BOM', 'ACTIVATED', 2),
            (stores[1], funcs[4], 'PODE_APRENDER', 'ACTIVATED', 4),
            (stores[2], funcs[2], 'PRECISA', 'ACTIVATED', 2),   # 1 já em MATCH
            (stores[2], funcs[0], 'PRECISA', 'CLOSED', 0),
            (stores[0], funcs[2], 'SERIA_BOM', 'STRUCTURED', 0),
            (stores[1], funcs[0], 'PRECISA', 'ACTIVATED', 1),   # 1 em CONTACT_ENABLED
        ]

        opps = []
        for i, (store, func, tag, state_key, n_interested) in enumerate(opps_spec):
            title = f'{func.name} — {store.name}'
            opp, _ = Opportunity.objects.get_or_create(
                organization=org, business_unit=store, job_function=func,
                title=title,
                defaults={
                    'workplace': f'{store.name} · Piso térreo',
                    'schedule': 'Seg-sáb, 12h-20h',
                    'work_format': Opportunity.FORMAT_FIXO,
                    'starts_at': date.today() + timedelta(days=rnd.randint(7, 30)),
                    'tag': tag, 'mode': Opportunity.MODE_MATCH,
                    'state': Opportunity.STATE_STRUCTURED,
                },
            )
            OpportunityCriterion.objects.get_or_create(
                opportunity=opp, label='Disponibilidade nos horários',
                defaults={'weight': OpportunityCriterion.WEIGHT_REQUIRED},
            )
            if state_key != 'STRUCTURED':
                opp.pre_interest_set_complete = True
                opp.state = Opportunity.STATE_CLOSED if state_key == 'CLOSED' else Opportunity.STATE_ACTIVATED
                opp.required_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
                opp.required_period = Opportunity.PERIOD_ANY
                opp.required_experience = Opportunity.EXPERIENCE_ANY
                opp.requested_slots = 2
                opp.invite_batch_size = 4
                opp.negotiable_fields = ['period', 'start_date', 'work_format', 'learn']
                opp.activated_at = timezone.now()
                if state_key == 'CLOSED':
                    opp.closed_at = timezone.now()
                opp.save()
            mapping_terms = CanonicalFunctionMapping.objects.filter(
                organization=org, job_function=func, business_unit=store,
                active=True, term__active=True,
            ).values_list('term_id', flat=True).distinct()
            for term_id in mapping_terms:
                OpportunityCanonicalRequirement.objects.get_or_create(
                    position=opp, term_id=term_id,
                    defaults={'requirement': OpportunityCanonicalRequirement.REQUIRED, 'source': 'demo_store_catalog'},
                )
            opps.append((opp, n_interested, state_key))

        # Gera relações
        for opportunity_index, (opp, n, state_key) in enumerate(opps):
            if state_key != 'ACTIVATED' and state_key != 'CLOSED':
                continue
            manager_user = next(u for u, s in managers if s == opp.business_unit)
            interested = rnd.sample(candidates, k=min(n, len(candidates)))
            for j, cand in enumerate(interested):
                rel = deliver_opportunity_notice(candidate=cand, opportunity=opp)
                if rel.state != Relation.STATE_NOTICE_DELIVERED:
                    continue

                # O seed deixa cada estágio visível no painel sem exigir
                # cliques manuais: convite, expiração, interesse, negociação,
                # Match, contato e encerramento.
                if state_key == 'CLOSED':
                    person_interested(relation=rel)
                    employer_interested(relation=rel, actor=manager_user)
                    enable_contact(relation=rel, actor=manager_user)
                    create_response(
                        relation=rel, actor=manager_user,
                        response_class='RC-02', note='Escolhemos outra pessoa',
                    )
                    continue

                stage = {
                    0: ('view', 'notice'),
                    1: ('view', 'matched', 'contact'),
                    2: ('negotiation', 'notice'),
                    3: ('expired', 'view', 'matched', 'contact'),
                    4: ('matched', 'contact'),
                    7: ('contact',),
                }.get(opportunity_index, ('view',))
                current_stage = stage[j % len(stage)]
                if current_stage == 'notice':
                    continue
                if current_stage == 'expired':
                    rel.notice_expires_at = timezone.now() - timedelta(hours=2)
                    rel.save(update_fields=['notice_expires_at', 'updated_at'])
                    rel.transition(Relation.STATE_NOTICE_EXPIRED)
                    continue

                person_interested(relation=rel)
                rel.refresh_from_db()
                if current_stage == 'negotiation':
                    request_negotiation(
                        relation=rel, fields=['period'],
                        proposal={'period': 'afternoon'}, actor_type='employer_actor',
                    )
                elif current_stage in ('matched', 'contact'):
                    employer_interested(relation=rel, actor=manager_user)
                    rel.refresh_from_db()
                    if current_stage == 'contact':
                        enable_contact(relation=rel, actor=manager_user)
                        rel.refresh_from_db()

        self.stdout.write(self.style.SUCCESS(
            f'Demo criada: org={org.slug} · {len(stores)} lojas · '
            f'{len(candidates)} candidatos · {len(opps)} oportunidades.'
        ))
        stage_counts = {}
        for state, count in Relation.objects.filter(opportunity__organization=org).values_list('state').annotate(total=Count('id')):
            stage_counts[state] = count
        self.stdout.write(f'Estágios Match: {stage_counts}')
        self.stdout.write(f'Login lojista/shopping: gerente_{SLUG}_0 / {DEMO_PASSWORD}')
        self.stdout.write('Escopos demo: AA-1 a AA-8 · AA-6 habilitado para mostrar candidatos')
        self.stdout.write('Candidato demo: ana@matchco.demo · use o OTP exibido no ambiente de desenvolvimento')
        self.stdout.write('QR demo: 1 por loja — Match para funções de alto giro, sem CV')
        self.stdout.write('Portais: /matchco/ · /matchco/entrar/ · /portal/ · /portal/entrar/ · /candidato/')
