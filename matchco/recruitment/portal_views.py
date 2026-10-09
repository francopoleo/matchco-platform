"""Views dos portais externos MatchCo (candidato, lojista, shopping).

Cada portal tem shell própria (não usa o console). Autenticação:
- Candidato: sessão `matchco_profile_id` via OTP (passwordless).
- Lojista/Shopping: Django auth (login/senha).
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseGone, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .models import (
    AuthorityError, AuthorityScope, CandidateConsent, CandidateProfile,
    CandidateProfileSurveyResponse,
    ContactChannel, EntryPoint, OpportunityCriterion,
    Position, Relation, ResponseValidationError,
)


# =============================================================================
# Candidato (sessão OTP; sem Django auth)
# =============================================================================

def _get_candidate(request):
    pid = request.session.get('matchco_profile_id')
    if pid:
        return CandidateProfile.objects.filter(pk=pid).first()
    return None


def _candidate_profiles(request, candidate=None):
    """Perfis da mesma pessoa, separados por organização.

    A identidade é global para evitar duplicar a pessoa, mas o perfil e o
    consentimento são organizacionais. O perfil ativo da sessão é o único
    contexto usado para ações no feed.
    """
    candidate = candidate or _get_candidate(request)
    if candidate is None or not candidate.identity_id:
        return CandidateProfile.objects.none()
    return CandidateProfile.objects.filter(
        identity_id=candidate.identity_id,
    ).select_related('organization').order_by('organization__name', 'id')


def _candidate_context(request, candidate=None):
    candidate = candidate or _get_candidate(request)
    profiles = _candidate_profiles(request, candidate)
    return {
        'candidate_profiles': profiles,
        'candidate_profile_count': profiles.count(),
    }


class CandidatoHomeView(View):
    """Home do candidato — redireciona pro feed se logado, senão landing."""

    def get(self, request):
        c = _get_candidate(request)
        if c:
            return redirect('recruitment_public:candidato_feed')
        return redirect('recruitment_public:candidato_entrar')


class CandidatoLogoutView(View):
    def post(self, request):
        request.session.pop('matchco_profile_id', None)
        request.session.pop('otp_mobile', None)
        request.session.pop('_dev_otps', None)
        request.session.pop('matchco_identity_id', None)
        messages.success(request, 'Você saiu.')
        return redirect('recruitment_public:candidato_entrar')


class CandidatoFeedView(View):
    template_name = 'recruitment/portal/candidato_feed.html'

    def get(self, request):
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')

        from .feed import build_feed
        ep_id = request.session.get('ep_id')
        ep = EntryPoint.objects.filter(pk=ep_id).first() if ep_id else None
        items = build_feed(c, entry_point=ep)

        opp_ids = [it['opportunity_id'] for it in items]
        opps = {p.pk: p for p in Position.objects.filter(pk__in=opp_ids).select_related('business_unit', 'organization')}
        for it in items:
            opp = opps.get(it['opportunity_id'])
            if opp:
                it['store_name'] = opp.business_unit.name if opp.business_unit else opp.organization.name

        return render(request, self.template_name, {
            'candidate': c, 'items': items, **_candidate_context(request, c),
        })


class CandidatoInteresseView(View):
    def post(self, request, opportunity_id):
        from .services import (
            deliver_opportunity_notice, person_interested,
            RelationStateError,
        )
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')
        opp = get_object_or_404(Position, pk=opportunity_id, organization=c.organization)
        rel = deliver_opportunity_notice(candidate=c, opportunity=opp)
        try:
            person_interested(relation=rel)
            messages.success(request, 'Interesse registrado. Agora é a vez da loja.')
        except RelationStateError as e:
            messages.error(request, str(e))
        return redirect('recruitment_public:candidato_feed')


class CandidatoRecusarView(View):
    def post(self, request, opportunity_id):
        from .services import deliver_opportunity_notice, candidate_declined
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')
        opp = get_object_or_404(Position, pk=opportunity_id, organization=c.organization)
        rel = deliver_opportunity_notice(candidate=c, opportunity=opp)
        candidate_declined(relation=rel)
        messages.success(request, 'Ok, essa não te interessa.')
        return redirect('recruitment_public:candidato_feed')


class CandidatoMatchesView(View):
    template_name = 'recruitment/portal/candidato_matches.html'

    def get(self, request):
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')
        profiles = _candidate_profiles(request, c)
        rels = Relation.objects.filter(
            candidate__in=profiles,
            state__in=[Relation.STATE_EMPLOYER_INTEREST_VIEW, Relation.STATE_EMPLOYER_INTERESTED,
                       Relation.STATE_MATCHED, Relation.STATE_CONTACT_ENABLED,
                       Relation.STATE_RESPONSE_CREATED, Relation.STATE_CLOSED],
        ).select_related(
            'candidate', 'candidate__organization', 'opportunity',
            'opportunity__organization', 'opportunity__business_unit',
        ).order_by('-matched_at')
        return render(request, self.template_name, {
            'candidate': c, 'relations': rels, **_candidate_context(request, c),
        })


class CandidatoPerfilView(View):
    template_name = 'recruitment/portal/candidato_perfil.html'

    def get(self, request):
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')
        consents = c.identity.consents.filter(revoked_at__isnull=True) if c.identity_id else []
        return render(request, self.template_name, {
            'candidate': c,
            'consents': consents,
            'consent_choices': CandidateConsent.PURPOSE_CHOICES,
            **_candidate_context(request, c),
        })

    def post(self, request):
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')

        # Update basic fields
        c.first_name = request.POST.get('first_name', c.first_name)
        c.last_name = request.POST.get('last_name', c.last_name)
        c.city = request.POST.get('city', c.city)
        c.availability_days = request.POST.getlist('availability_days') or c.availability_days
        c.interested_in = request.POST.get('interested_in', c.interested_in)
        c.save()
        messages.success(request, 'Perfil atualizado.')
        return redirect('recruitment_public:candidato_perfil')


class CandidatoConsentToggleView(View):
    """Revoga ou concede consent granular por purpose."""

    def post(self, request):
        c = _get_candidate(request)
        if c is None or c.identity_id is None:
            return redirect('recruitment_public:candidato_entrar')
        purpose = request.POST.get('purpose')
        action = request.POST.get('action')  # 'grant' or 'revoke'
        if purpose not in dict(CandidateConsent.PURPOSE_CHOICES):
            messages.error(request, 'Finalidade inválida')
            return redirect('recruitment_public:candidato_perfil')

        if action == 'revoke':
            from .services import revoke_consent
            revoke_consent(identity=c.identity, purpose=purpose, organization=c.organization)
            messages.success(request, 'Consentimento revogado.')
        elif action == 'grant':
            CandidateConsent.objects.create(
                identity=c.identity, organization=c.organization,
                purpose=purpose, granted=True, policy_version='matchco-v1',
                legal_basis=CandidateConsent.BASIS_CONSENT,
                source='candidato_perfil',
            )
            if purpose == CandidateConsent.PURPOSE_VISIBILITY_MATCH:
                CandidateProfile.objects.filter(
                    identity=c.identity, organization=c.organization,
                ).update(
                    visibility_match=True,
                    circulation_state=CandidateProfile.CIRCULATION_ALLOWED,
                    updated_at=timezone.now(),
                )
            elif purpose == CandidateConsent.PURPOSE_CIRCULATION_SHOPPING:
                c.identity.pool_opt_in = True
                c.identity.save(update_fields=['pool_opt_in', 'updated_at'])
            messages.success(request, 'Consentimento concedido.')
        return redirect('recruitment_public:candidato_perfil')


class CandidatoCirculacaoToggleView(View):
    def post(self, request):
        c = _get_candidate(request)
        if c is None:
            return redirect('recruitment_public:candidato_entrar')
        want = request.POST.get('state', '')
        if want in (CandidateProfile.CIRCULATION_ALLOWED, CandidateProfile.CIRCULATION_PAUSED):
            c.circulation_state = want
            c.save(update_fields=['circulation_state', 'updated_at'])
            messages.success(request, 'Circulação atualizada.')
        return redirect('recruitment_public:candidato_feed')


class CandidatoContextoView(View):
    """Troca o perfil organizacional ativo do candidato.

    A pessoa pode ter perfis em várias organizações, mas toda ação de
    interesse permanece vinculada ao perfil/organização atualmente escolhido.
    """

    def post(self, request):
        current = _get_candidate(request)
        if current is None or not current.identity_id:
            return redirect('recruitment_public:candidato_entrar')
        profile_id = request.POST.get('profile_id')
        profile = _candidate_profiles(request, current).filter(pk=profile_id).first()
        if profile is None:
            return HttpResponseForbidden('Perfil organizacional inválido.')
        request.session['matchco_profile_id'] = profile.pk
        request.session.modified = True
        messages.success(request, f'Contexto alterado para {profile.organization.name}.')
        return redirect(request.POST.get('next') or 'recruitment_public:candidato_feed')


# =============================================================================
# Lojista (Django auth)
# =============================================================================

def _lojista_available_organizations(request):
    """Retorna apenas organizações ativas que o usuário pode operar no Portal."""
    from .domain_models import RecruitmentOrganization

    if request.user.is_superuser:
        return list(RecruitmentOrganization.objects.filter(active=True).order_by('name'))

    actors = request.user.employer_actor_profiles.filter(
        active=True,
    ).select_related('organization').order_by('organization__name')
    organizations = []
    seen = set()
    for actor in actors:
        if actor.organization_id not in seen:
            organizations.append(actor.organization)
            seen.add(actor.organization_id)
    return organizations


def _lojista_org(request):
    """Resolve o contexto escolhido; nunca troca silenciosamente para outra org."""
    organizations = _lojista_available_organizations(request)
    selected_org_id = request.session.get('matchco_portal_recruitment_organization_id')
    selected = next(
        (organization for organization in organizations if str(organization.pk) == str(selected_org_id)),
        None,
    ) if selected_org_id else None

    # Um usuário com apenas uma organização pode entrar diretamente.
    # Com mais de uma, a escolha precisa ser explícita para evitar vazamento
    # de contexto (por exemplo, permanecer no Bourbon).
    if selected is None and len(organizations) == 1:
        selected = organizations[0]
    if selected is None:
        return None, None

    actor = None
    if not request.user.is_superuser:
        actor = request.user.employer_actor_profiles.filter(
            active=True, organization_id=selected.pk,
        ).select_related('organization').first()
        if actor is None:
            return None, None
    return actor, selected


def _portal_actor_for_relation(request, relation, scope=AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW):
    """Valida relação no tenant e na unidade do ator antes de carregá-la."""
    from .services import _resolve_employer_actor

    actor, org = _lojista_org(request)
    if org is None or relation.opportunity.organization_id != org.pk:
        raise AuthorityError('Relação fora da organização ativa.')
    _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
    if selected_store is not None and relation.opportunity.business_unit_id != selected_store.pk:
        raise AuthorityError('Relação fora do filtro de unidade.')
    return _resolve_employer_actor(request.user, relation.opportunity, scope)


def _portal_store_is_visible(request, store):
    actor, org = _lojista_org(request)
    if org is None or store.organization_id != org.pk:
        return False
    if request.user.is_superuser:
        return True
    return bool(actor and actor.active and actor.has_scope(AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW)
                and (actor.business_unit_id is None or actor.business_unit_id == store.pk))


def _portal_store_scope(request, actor=None, org=None):
    """Resolve the store filter shared by every authenticated portal page.

    A unit-bound actor can never broaden this scope. Organization-level users
    may explicitly choose one authorized store or ``__all__`` in the session.
    The browser value is only a selector; every queryset must still use the
    returned organization/store objects on the server.
    """
    from .models import BusinessUnit

    actor = actor or _lojista_org(request)[0]
    org = org or _lojista_org(request)[1]
    stores = BusinessUnit.objects.filter(organization=org, active=True).order_by('name') if org else BusinessUnit.objects.none()
    if actor and actor.business_unit_id and not request.user.is_superuser:
        stores = stores.filter(pk=actor.business_unit_id)
        selected = stores.first()
        return stores, selected, False

    selected_id = request.session.get('matchco_portal_store_id')
    selected = None
    if selected_id and selected_id != '__all__':
        selected = stores.filter(pk=selected_id).first()
        if selected is None:
            request.session.pop('matchco_portal_store_id', None)
    return stores, selected, bool(selected)


def _portal_store_queryset(request, queryset, field='business_unit'):
    """Apply the selected portal store to a queryset with a matching FK."""
    _, selected, _ = _portal_store_scope(request)
    if selected is not None:
        return queryset.filter(**{f'{field}_id': selected.pk})
    return queryset


def _portal_context(request):
    """Resolve a marca e o mercado da porta de acesso sem criar templates por setor."""
    from configuration.models import Organization

    from .models import EntryPoint

    entry_id = request.GET.get('entry') or request.GET.get('entry_point') or request.POST.get('entry') or request.POST.get('entry_point')
    entry = None
    if entry_id:
        entry = EntryPoint.objects.select_related('organization', 'scope_store').filter(
            pk=entry_id, state__in=[EntryPoint.STATE_ACTIVE, EntryPoint.STATE_TESTED],
        ).first()

    organization = entry.organization if entry else None
    organization_slug = request.GET.get('organization') or request.GET.get('org') or request.POST.get('organization') or request.POST.get('org')
    if organization is None and organization_slug:
        organization = Organization.objects.filter(
            slug=organization_slug, active=True,
        ).first()

    session = getattr(request, 'session', {})
    if organization is None and session.get('matchco_portal_organization_id'):
        organization = Organization.objects.filter(
            pk=session['matchco_portal_organization_id'], active=True,
        ).first()

    labels = {
        Organization.MARKET_SHOPPING: ('Portal do Shopping', 'lojas, equipes e operações do shopping'),
        Organization.MARKET_RETAIL: ('Portal da Rede de Lojas', 'unidades, gestores e equipes da rede'),
        Organization.MARKET_MANUFACTURER: ('Portal da Rede de Canais', 'distribuidores, revendedores e equipes parceiras'),
        Organization.MARKET_DISTRIBUTOR: ('Portal do Canal', 'parceiros, clientes e equipes de distribuição'),
        Organization.MARKET_PHARMA: ('Portal da Rede de Saúde', 'representantes, farmácias, hospitais e parceiros'),
        Organization.MARKET_HOSPITAL: ('Portal da Organização de Saúde', 'unidades, equipes e profissionais da organização'),
        Organization.MARKET_LOGISTICS: ('Portal da Operação Logística', 'hubs, equipes e parceiros da operação'),
        Organization.MARKET_EDUCATION: ('Portal da Comunidade', 'equipes, parceiros e participantes da organização'),
        Organization.MARKET_SERVICES: ('Portal da Rede', 'unidades, franqueados e equipes da rede'),
        Organization.MARKET_GENERAL: ('Portal da Organização', 'pessoas autorizadas pela organização'),
    }
    market = organization.market if organization else Organization.MARKET_GENERAL
    portal_title, audience_description = labels.get(market, labels[Organization.MARKET_GENERAL])
    brand_name = (entry.brand_name if entry else '') or (organization.brand_name if organization else '') or (organization.name if organization else 'MatchCo')
    logo_url = (entry.brand_logo_url if entry else '') or (organization.logo_url if organization else '')
    accent = (entry.accent_color if entry else '') or (organization.primary_color if organization else '') or '#f97316'
    if not re.match(r'^#[0-9a-fA-F]{3,8}$', accent):
        accent = '#f97316'
    return {
        'portal_title': portal_title,
        'portal_role_label': portal_title.replace('Portal ', ''),
        'portal_audience_description': audience_description,
        'portal_brand_name': brand_name,
        'portal_logo_url': logo_url,
        'portal_accent': accent,
        'portal_organization': organization,
        'portal_entry_point': entry,
        'portal_context_query': request.GET.urlencode(),
    }


class LojistaEntrarView(TemplateView):
    """Login dedicado do lojista — usa Django auth por trás."""
    template_name = 'recruitment/portal/lojista_entrar.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('recruitment_public:lojista_home')
        return self.render_to_response(_portal_context(request))

    def post(self, request):
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        context = _portal_context(request)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, self.template_name, {
                **context,
                'error': 'Usuário ou senha inválidos.',
                'username': username,
            })
        # Só permite entrar se tiver EmployerActor
        if not user.employer_actor_profiles.filter(active=True).exists() and not user.is_superuser:
            return render(request, self.template_name, {
                **context,
                'error': 'Sua conta não tem permissão de lojista.',
                'username': username,
            })
        organization = context.get('portal_organization')
        actor_qs = user.employer_actor_profiles.filter(active=True).select_related('organization')
        selected_actor = None
        if organization is not None:
            selected_actor = actor_qs.filter(organization__legacy_id=organization.pk).first()
        elif actor_qs.values('organization_id').distinct().count() == 1:
            selected_actor = actor_qs.first()
        if selected_actor is not None:
            request.session['matchco_portal_recruitment_organization_id'] = selected_actor.organization_id
            request.session.pop('matchco_portal_store_id', None)
        if context.get('portal_entry_point') is not None:
            request.session['matchco_portal_entry_point_id'] = str(context['portal_entry_point'].pk)
            if context['portal_entry_point'].scope_store_id:
                request.session['matchco_portal_store_id'] = context['portal_entry_point'].scope_store_id
        login(request, user)
        if context.get('portal_organization') is None and actor_qs.values('organization_id').distinct().count() > 1:
            return redirect('recruitment_public:lojista_contexto')
        return redirect('recruitment_public:lojista_home')


class LojistaContextoView(LoginRequiredMixin, View):
    """Escolha explícita quando o mesmo usuário opera mais de uma empresa."""
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_contexto.html'

    def get(self, request):
        return render(request, self.template_name, {
            'organizations': _lojista_available_organizations(request),
            'selected_id': request.session.get('matchco_portal_recruitment_organization_id'),
        })

    def post(self, request):
        organization_id = request.POST.get('organization_id', '').strip()
        organization = next(
            (item for item in _lojista_available_organizations(request) if str(item.pk) == organization_id),
            None,
        )
        if organization is None:
            return HttpResponseForbidden('Organização fora do seu acesso.')
        request.session['matchco_portal_recruitment_organization_id'] = organization.pk
        request.session.pop('matchco_portal_store_id', None)
        request.session.pop('matchco_portal_entry_point_id', None)
        # A marca da porta pública é apenas uma referência de entrada. Ela não
        # pode continuar influenciando o contexto depois da troca de empresa.
        if organization.legacy_id:
            request.session['matchco_portal_organization_id'] = organization.legacy_id
        else:
            request.session.pop('matchco_portal_organization_id', None)
        request.session.modified = True
        return redirect('recruitment_public:lojista_home')


class LojistaUnidadeContextoView(LoginRequiredMixin, View):
    """Troca o filtro de unidade sem trocar a organização do Portal."""
    login_url = '/portal/entrar/'

    def post(self, request):
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        stores, _, _ = _portal_store_scope(request, actor=actor, org=org)
        store_id = request.POST.get('store_id', '').strip()
        if actor and actor.business_unit_id and not request.user.is_superuser:
            if store_id not in ('', str(actor.business_unit_id)):
                return HttpResponseForbidden('Unidade fora do seu escopo.')
            request.session['matchco_portal_store_id'] = actor.business_unit_id
        elif store_id in ('', '__all__'):
            request.session['matchco_portal_store_id'] = '__all__'
        else:
            store = stores.filter(pk=store_id).first()
            if store is None:
                return HttpResponseForbidden('Unidade fora do seu escopo.')
            request.session['matchco_portal_store_id'] = store.pk
        request.session.modified = True
        next_url = request.POST.get('next') or ''
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = ''
        return redirect(next_url or 'recruitment_public:lojista_home')


class LojistaHomeView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'

    def get(self, request):
        _, organization = _lojista_org(request)
        if organization is None:
            return redirect('recruitment_public:lojista_contexto')
        return redirect('recruitment_public:lojista_necessidades')


class LojistaNecessidadesView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_necessidades.html'

    def get(self, request):
        from django.db.models import Count, Q
        from .models import CanonicalFunctionMapping
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        qs = Position.objects.filter(
            organization=org, mode=Position.MODE_MATCH,
        ).select_related('business_unit', 'job_function').annotate(
            n_interested=Count('relations', filter=Q(
                relations__state__in=[
                    Relation.STATE_EMPLOYER_INTEREST_VIEW,
                    Relation.STATE_EMPLOYER_INTERESTED,
                ],
            )),
            n_matched=Count('relations', filter=Q(
                relations__state__in=[
                    Relation.STATE_MATCHED, Relation.STATE_CONTACT_ENABLED,
                ],
            )),
            n_awaiting_response=Count('relations', filter=Q(
                relations__state=Relation.STATE_NOTICE_DELIVERED,
            )),
            n_sent=Count('relations', filter=Q(relations__state=Relation.STATE_NOTICE_DELIVERED)),
            n_expired=Count('relations', filter=Q(relations__state=Relation.STATE_NOTICE_EXPIRED)),
            n_person_interested=Count('relations', filter=Q(relations__state=Relation.STATE_PERSON_INTERESTED)),
            n_employer_review=Count('relations', filter=Q(relations__state=Relation.STATE_EMPLOYER_INTEREST_VIEW)),
        ).order_by('-created_at')
        if actor and actor.business_unit_id and not request.user.is_superuser:
            qs = qs.filter(business_unit_id=actor.business_unit_id)
        qs = _portal_store_queryset(request, qs)

        state = request.GET.get('state', '')
        if state:
            qs = qs.filter(state=state)
        qs = qs[:100]
        opportunities = list(qs)
        function_ids = {opp.job_function_id for opp in opportunities if opp.job_function_id}
        mappings = CanonicalFunctionMapping.objects.filter(
            organization=org, active=True, term__active=True,
            job_function_id__in=function_ids,
        ).select_related('term')
        for opp in opportunities:
            labels = [m.term.label for m in mappings if m.job_function_id == opp.job_function_id and (m.business_unit_id == opp.business_unit_id or m.business_unit_id is None)]
            opp.canonical_labels = list(dict.fromkeys(labels))

        return render(request, self.template_name, {
            'opportunities': opportunities,
            'state_filter': state,
            'state_choices': Position.STATE_CHOICES,
            'org': org,
        })


class LojistaDeclararView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_declarar.html'

    def get(self, request):
        from .models import BusinessUnit, JobFunction, CanonicalFunctionMapping
        from .services import recruitment_defaults
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        stores, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if selected_store is not None:
            stores = stores.filter(pk=selected_store.pk)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            stores = stores.filter(pk=actor.business_unit_id)
        functions = JobFunction.objects.filter(
            organization=org, active=True,
            canonical_mappings__active=True,
        ).filter(
            Q(canonical_mappings__business_unit__in=stores) |
            Q(canonical_mappings__business_unit__isnull=True)
        ).distinct()
        for store in stores:
            store.sla_defaults = recruitment_defaults(organization=org, business_unit=store)
        return render(request, self.template_name, {
            'stores': stores, 'functions': functions,
            'selected_store': selected_store,
            'fixed_store': bool(actor and actor.business_unit_id and not request.user.is_superuser),
            'tag_choices': Position.TAG_CHOICES,
            'format_choices': Position.FORMAT_CHOICES,
            'period_choices': Position.PERIOD_CHOICES,
            'experience_choices': Position.EXPERIENCE_CHOICES,
            'day_choices': [('mon', 'Segunda'), ('tue', 'Terça'), ('wed', 'Quarta'),
                            ('thu', 'Quinta'), ('fri', 'Sexta'), ('sat', 'Sábado'), ('sun', 'Domingo')],
            'sla_defaults': recruitment_defaults(organization=org),
            'org': org,
        })

    def post(self, request):
        from .models import BusinessUnit, JobFunction, CanonicalFunctionMapping, OpportunityCanonicalRequirement
        from .services import can_declare_new_opportunity, ledger_record, recruitment_defaults, open_invitation_round
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')

        if not can_declare_new_opportunity(organization=org):
            messages.error(request, 'Há matches sem resposta há muito tempo. Responda antes de declarar nova.')
            return redirect('recruitment_public:lojista_declarar')

        store = get_object_or_404(BusinessUnit, pk=request.POST['store_id'], organization=org)
        _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if selected_store is not None and store.pk != selected_store.pk:
            return HttpResponseForbidden('Altere o filtro de unidade antes de operar outra loja.')
        if actor and actor.business_unit_id and not request.user.is_superuser and store.pk != actor.business_unit_id:
            return HttpResponseForbidden('Unidade fora do seu escopo.')
        func = get_object_or_404(JobFunction, pk=request.POST['function_id'], organization=org)
        if not CanonicalFunctionMapping.objects.filter(
            organization=org, job_function=func, active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).exists():
            messages.error(request, 'Esta função da loja ainda não foi mapeada para uma função canônica do cadastro do candidato.')
            return redirect('recruitment_public:lojista_declarar')
        mapping = CanonicalFunctionMapping.objects.filter(
            pk=request.POST.get('mapping_id'), organization=org, job_function=func, active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).first() or CanonicalFunctionMapping.objects.filter(
            organization=org, job_function=func, active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).order_by('business_unit_id', 'pk').first()
        defaults = recruitment_defaults(organization=org, business_unit=store)
        required_days = request.POST.getlist('required_days')
        starts_at_raw = (request.POST.get('starts_at') or '').strip()
        try:
            starts_at = date.fromisoformat(starts_at_raw) if starts_at_raw else None
        except ValueError:
            messages.error(request, 'A data de início é inválida.')
            return redirect('recruitment_public:lojista_declarar')
        requested_slots = max(1, min(999, int(request.POST.get('requested_slots') or 1)))
        invite_batch_size = max(1, min(999, int(request.POST.get('invite_batch_size') or defaults['invite_batch_size'])))
        candidate_response_hours = max(1, min(720, int(request.POST.get('candidate_response_hours') or defaults['candidate_response_hours'])))
        employer_decision_hours = max(1, min(720, int(request.POST.get('employer_decision_hours') or defaults['employer_decision_hours'])))

        opp = Position.objects.create(
            organization=org, business_unit=store, job_function=func,
            title=request.POST.get('title', func.name),
            description=request.POST.get('description', '').strip() or (mapping.job_description if mapping else ''),
            requirements='\n'.join(mapping.requirements or []) if mapping else '',
            benefits=mapping.benefits or [] if mapping else [],
            workplace=request.POST.get('workplace', ''),
            schedule=request.POST.get('schedule', ''),
            work_format=request.POST.get('work_format', Position.FORMAT_FIXO),
            starts_at=starts_at,
            required_days=required_days,
            required_period=request.POST.get('required_period', Position.PERIOD_ANY),
            required_experience=request.POST.get('required_experience', Position.EXPERIENCE_ANY),
            salary_min=mapping.salary_min if mapping else None,
            salary_max=mapping.salary_max if mapping else None,
            salary_period=mapping.salary_period if mapping else '',
            employment_type=mapping.employment_type if mapping else '',
            payment_method=mapping.payment_method if mapping else '',
            requested_slots=requested_slots,
            invite_batch_size=invite_batch_size,
            candidate_response_hours=candidate_response_hours,
            employer_decision_hours=employer_decision_hours,
            negotiable_fields=request.POST.getlist('negotiable_fields'),
            tag=request.POST.get('tag', Position.TAG_PRECISA),
            mode=Position.MODE_MATCH,
            state=Position.STATE_STRUCTURED,
        )
        # Congela no momento da necessidade o conjunto canônico do cargo local.
        # Alterações futuras no de-para da loja não mudam uma necessidade já criada.
        mapping_terms = CanonicalFunctionMapping.objects.filter(
            organization=org, job_function=func,
        ).filter(
            Q(business_unit=store) | Q(business_unit__isnull=True),
            local_label=mapping.local_label if mapping else '', active=True,
        ).values_list('term_id', flat=True).distinct()
        for term_id in mapping_terms:
            OpportunityCanonicalRequirement.objects.create(
                position=opp, term_id=term_id,
                requirement=OpportunityCanonicalRequirement.REQUIRED,
                source='store_function_mapping',
            )
        for wkey, wval in [('required', OpportunityCriterion.WEIGHT_REQUIRED),
                           ('desirable', OpportunityCriterion.WEIGHT_DESIRABLE),
                           ('can_learn', OpportunityCriterion.WEIGHT_CAN_LEARN)]:
            for i, lbl in enumerate([l.strip() for l in request.POST.getlist(f'criteria_{wkey}') if l.strip()]):
                OpportunityCriterion.objects.create(opportunity=opp, label=lbl, weight=wval, order=i)

        # A elegibilidade agora vem dos filtros estruturados acima. Mantemos
        # uma linha interna para preservar o contrato histórico de publicação,
        # sem transformar o formulário em um segundo filtro de texto livre.
        if not opp.criteria.filter(weight=OpportunityCriterion.WEIGHT_REQUIRED).exists():
            OpportunityCriterion.objects.create(
                opportunity=opp,
                label='Compatibilidade com os filtros estruturados da necessidade',
                weight=OpportunityCriterion.WEIGHT_REQUIRED,
                order=0,
            )

        opp.pre_interest_set_complete = opp.compute_pre_interest_complete()
        if opp.pre_interest_set_complete:
            opp.state = Position.STATE_ACTIVATED
            opp.activated_at = timezone.now()
        opp.save()
        ledger_record('OPPORTUNITY_STRUCTURED', actor=request.user,
                      actor_type='employer_actor', authority_scope='AA-2',
                      opportunity=opp, metadata={'title': opp.title, 'tag': opp.tag})
        if opp.state == Position.STATE_ACTIVATED:
            ledger_record('OPPORTUNITY_ACTIVATED', actor=request.user,
                          actor_type='employer_actor', authority_scope='AA-3',
                          opportunity=opp)
            opp.state = Position.STATE_CIRCULATED
            opp.save(update_fields=['state', 'updated_at'])
            open_invitation_round(opportunity=opp)
        messages.success(request, f'Necessidade declarada (v{opp.version}, {opp.get_state_display()}).')
        return redirect('recruitment_public:lojista_oportunidade_pilha', opportunity_id=opp.pk)


class LojistaJobFunctionsView(LoginRequiredMixin, View):
    """Funções cadastradas na loja, já resolvidas para o catálogo canônico."""
    login_url = '/portal/entrar/'

    def get(self, request, business_unit_id):
        from .models import BusinessUnit, CanonicalFunctionMapping
        store = get_object_or_404(BusinessUnit, pk=business_unit_id)
        if not _portal_store_is_visible(request, store):
            return HttpResponseForbidden('Unidade fora do escopo da organização.')
        mappings = CanonicalFunctionMapping.objects.filter(
            organization=store.organization, active=True,
            term__active=True, job_function__active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).select_related(
            'job_function', 'term'
        ).order_by('local_label', 'job_function__name', 'term__label')
        grouped = {}
        for mapping in mappings:
            local_label = (mapping.local_label or '').strip() or mapping.job_function.name
            key = (mapping.job_function_id, local_label)
            group = grouped.setdefault(key, {'id': mapping.job_function_id, 'mapping_id': mapping.pk, 'name': local_label, 'labels': [],
                                             'job_description': mapping.job_description, 'requirements': mapping.requirements or [],
                                             'benefits': mapping.benefits or [], 'salary_min': mapping.salary_min,
                                             'salary_max': mapping.salary_max, 'salary_period': mapping.salary_period,
                                             'employment_type': mapping.employment_type, 'payment_method': mapping.payment_method})
            if mapping.term.label not in group['labels']:
                group['labels'].append(mapping.term.label)
        function_rows = [
            {'id': group['id'], 'mapping_id': group['mapping_id'], 'name': group['name'], 'canonical_label': ', '.join(group['labels']),
             'job_description': group.get('job_description', ''), 'requirements': group.get('requirements', []),
             'benefits': group.get('benefits', []), 'salary_min': group.get('salary_min'),
             'salary_max': group.get('salary_max'), 'salary_period': group.get('salary_period', ''),
             'employment_type': group.get('employment_type', ''), 'payment_method': group.get('payment_method', '')}
            for group in grouped.values()
        ]
        return JsonResponse({'business_unit': store.name, 'job_functions': function_rows})


class LojistaFunctionCatalogView(LoginRequiredMixin, View):
    """Administra o catálogo operacional da loja e seu de-para canônico."""
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_funcoes.html'

    def get(self, request):
        from .models import BusinessUnit, CanonicalFunctionMapping, CanonicalTerm, JobFunction
        from configuration.models import BusinessUnit as ConfigBusinessUnit
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        store_id = request.GET.get('store_id') or (selected_store.pk if selected_store else None) or (actor.business_unit_id if actor and actor.business_unit_id else None)
        store = get_object_or_404(BusinessUnit, pk=store_id, organization=org) if store_id else None
        if store and not _portal_store_is_visible(request, store):
            return HttpResponseForbidden('Unidade fora do escopo da organização.')
        if selected_store is not None and store and store.pk != selected_store.pk:
            return HttpResponseForbidden('Altere o filtro de unidade antes de operar outra loja.')
        stores = BusinessUnit.objects.filter(organization=org, active=True)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            stores = stores.filter(pk=actor.business_unit_id)
        functions = JobFunction.objects.filter(organization=org, active=True).order_by('name')
        config_store = ConfigBusinessUnit.objects.filter(pk=store.legacy_id).select_related('company').first() if store else None
        structure_functions = list(config_store.company.job_functions.filter(active=True).order_by('name')) if config_store else []
        terms = CanonicalTerm.objects.filter(
            catalog__code='market-default', catalog__status='published',
            term_type=CanonicalTerm.TYPE_FUNCTION, active=True,
        ).order_by('label')
        mappings = CanonicalFunctionMapping.objects.filter(
            organization=org, business_unit=store, active=True,
        ).select_related('job_function', 'term').order_by('local_label', 'job_function__name') if store else []
        mapping_groups = {}
        for mapping in mappings:
            key = (mapping.local_label, mapping.job_function_id, mapping.job_function.name)
            group = mapping_groups.setdefault(key, {
                'id': mapping.pk, 'local_label': mapping.local_label,
                'structure_function_id': mapping.job_function.legacy_id or next((item.pk for item in structure_functions if item.name == mapping.job_function.name), None),
                'job_function': mapping.job_function.name,
                'term_ids': [], 'terms': [],
                'job_description': mapping.job_description,
                'requirements': mapping.requirements or [],
                'benefits': mapping.benefits or [],
                'salary_min': mapping.salary_min,
                'salary_max': mapping.salary_max,
                'salary_period': mapping.salary_period,
                'employment_type': mapping.employment_type,
                'payment_method': mapping.payment_method,
            })
            group['term_ids'].append(str(mapping.term_id))
            group['terms'].append(mapping.term.label)
        edit_id = request.GET.get('edit_mapping_id')
        edit_group = next((group for group in mapping_groups.values() if str(group['id']) == str(edit_id)), None)
        return render(request, self.template_name, {
            'org': org, 'actor': actor, 'stores': stores, 'store': store,
            'terms': terms, 'mappings': mappings, 'structure_functions': structure_functions,
            'mapping_groups': mapping_groups.values(), 'edit_group': edit_group,
            'salary_period_choices': Position.SALARY_PERIOD_CHOICES,
            'employment_type_choices': Position.EMPLOYMENT_TYPE_CHOICES,
            'payment_method_choices': Position.PAYMENT_METHOD_CHOICES,
        })

    def post(self, request):
        from .models import BusinessUnit, CanonicalFunctionMapping, CanonicalTerm, JobFunction
        from configuration.models import BusinessUnit as ConfigBusinessUnit
        actor, org = _lojista_org(request)
        store = get_object_or_404(BusinessUnit, pk=request.POST.get('store_id'), organization=org)
        if not _portal_store_is_visible(request, store):
            return HttpResponseForbidden('Unidade fora do escopo da organização.')
        _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if selected_store is not None and store.pk != selected_store.pk:
            return HttpResponseForbidden('Altere o filtro de unidade antes de operar outra loja.')
        config_store = ConfigBusinessUnit.objects.filter(pk=store.legacy_id).select_related('company').first()
        structure_function = (
            config_store.company.job_functions.filter(pk=request.POST.get('structure_function_id'), active=True).first()
            if config_store and request.POST.get('structure_function_id') else None
        )
        if structure_function is None:
            messages.error(request, 'Selecione um cargo já cadastrado na estrutura da empresa.')
            return redirect(f'{reverse("recruitment_public:lojista_funcoes")}?store_id={store.pk}')
        term_ids = request.POST.getlist('term_ids')
        terms = CanonicalTerm.objects.filter(
            pk__in=term_ids, term_type=CanonicalTerm.TYPE_FUNCTION, active=True,
        )
        if not terms.exists():
            messages.error(request, 'Selecione pelo menos uma função canônica do candidato.')
            return redirect(f'{reverse("recruitment_public:lojista_funcoes")}?store_id={store.pk}')

        def decimal_value(name):
            raw = (request.POST.get(name) or '').strip().replace(',', '.')
            if not raw:
                return None
            try:
                value = Decimal(raw)
            except InvalidOperation:
                raise ValueError(f'Valor inválido para {name}.')
            if value < 0:
                raise ValueError(f'Valor inválido para {name}.')
            return value

        try:
            salary_min = decimal_value('salary_min')
            salary_max = decimal_value('salary_max')
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect(f'{reverse("recruitment_public:lojista_funcoes")}?store_id={store.pk}')
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            messages.error(request, 'A faixa máxima não pode ser menor que a mínima.')
            return redirect(f'{reverse("recruitment_public:lojista_funcoes")}?store_id={store.pk}')
        profile_defaults = {
            'job_description': request.POST.get('job_description', '').strip(),
            'requirements': [line.strip() for line in request.POST.get('requirements', '').splitlines() if line.strip()],
            'benefits': [line.strip() for line in request.POST.get('benefits', '').splitlines() if line.strip()],
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_period': request.POST.get('salary_period', '').strip(),
            'employment_type': request.POST.get('employment_type', '').strip(),
            'payment_method': request.POST.get('payment_method', '').strip(),
        }
        from .integrations.organization import _sync_job_function
        function = _sync_job_function(structure_function, org)
        local_label = structure_function.name
        edit_mapping_id = request.POST.get('edit_mapping_id')
        if edit_mapping_id:
            anchor = get_object_or_404(CanonicalFunctionMapping, pk=edit_mapping_id, organization=org, business_unit=store, active=True)
            group_qs = CanonicalFunctionMapping.objects.filter(
                organization=org, business_unit=store, job_function=anchor.job_function,
                local_label=anchor.local_label, active=True,
            )
            selected_ids = {term.pk for term in terms}
            for current in group_qs:
                if current.term_id not in selected_ids:
                    current.active = False
                    current.save(update_fields=['active'])
                else:
                    for field, value in profile_defaults.items():
                        setattr(current, field, value)
                    current.save(update_fields=[*profile_defaults.keys()])
            function = anchor.job_function
        for term in terms:
            CanonicalFunctionMapping.objects.update_or_create(
                organization=org, business_unit=store, job_function=function, term=term,
                defaults={'local_label': local_label, 'source': 'store_portal', 'active': True, **profile_defaults},
            )
        messages.success(request, 'Função da loja vinculada ao catálogo canônico do candidato.')
        return redirect(f'{reverse("recruitment_public:lojista_funcoes")}?store_id={store.pk}')


class LojistaSimularView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'

    def get(self, request):
        from .models import BusinessUnit, JobFunction, Position
        from .services import estimate_candidate_pool
        store_id = request.GET.get('store_id')
        if not store_id:
            return JsonResponse({'estimate': 0})
        store = BusinessUnit.objects.filter(pk=store_id).first()
        if not store:
            return JsonResponse({'estimate': 0})
        if not _portal_store_is_visible(request, store):
            return HttpResponseForbidden('Unidade fora do escopo da organização.')
        _, selected_store, _ = _portal_store_scope(request)
        if selected_store is not None and store.pk != selected_store.pk:
            return HttpResponseForbidden('Altere o filtro de unidade antes de simular outra loja.')
        function = JobFunction.objects.filter(
            pk=request.GET.get('function_id'), organization=store.organization,
        ).first() if request.GET.get('function_id') else None
        n = estimate_candidate_pool(
            organization=store.organization,
            business_unit=store,
            job_function=function,
            required_days=request.GET.getlist('required_days'),
            required_period=request.GET.get('required_period', Position.PERIOD_ANY),
            work_format=request.GET.get('work_format', ''),
            required_experience=request.GET.get('required_experience', Position.EXPERIENCE_ANY),
        )
        return JsonResponse({'estimate': n})


class LojistaOportunidadePilhaView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_pilha.html'

    def get(self, request, opportunity_id):
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        if not Position.objects.filter(pk=opportunity_id, organization=org, mode=Position.MODE_MATCH).exists():
            return HttpResponseGone(
                'A pilha de candidaturas com currículo foi descontinuada. '
                'Use as necessidades Match de alto giro.'
            )
        from .projections import employer_interest_view
        from .services import _resolve_employer_actor
        opp = get_object_or_404(
            Position.objects.select_related('business_unit', 'organization'),
            pk=opportunity_id, organization=org,
        )
        _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if selected_store is not None and opp.business_unit_id != selected_store.pk:
            return HttpResponseForbidden('Oportunidade fora do filtro de unidade.')
        try:
            _resolve_employer_actor(request.user, opp, AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW)
        except AuthorityError:
            if not request.user.is_superuser:
                return HttpResponseForbidden('Sem AA-6')
        eligible = [
            Relation.STATE_EMPLOYER_INTEREST_VIEW, Relation.STATE_EMPLOYER_INTERESTED,
            Relation.STATE_MATCHED, Relation.STATE_CONTACT_ENABLED,
            Relation.STATE_RESPONSE_CREATED,
        ]
        rels = list(Relation.objects.filter(opportunity=opp, state__in=eligible)
                    .select_related('candidate').order_by('-person_interested_at'))
        cards = []
        for r in rels:
            v = employer_interest_view(r)
            if v: v['relation_state'] = r.state; cards.append(v)
        return render(request, self.template_name, {'opportunity': opp, 'cards': cards})


class LojistaRelationDetailView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_relation.html'

    # --- Phase 4 RBAC: States where employer can view relation details ---
    VIEWABLE_STATES = frozenset({
        Relation.STATE_EMPLOYER_INTEREST_VIEW,
        Relation.STATE_EMPLOYER_INTERESTED,
        Relation.STATE_MATCHED,
        Relation.STATE_CONTACT_ENABLED,
        Relation.STATE_RESPONSE_CREATED,
    })

    def get(self, request, relation_id):
        from .projections import contact_view, employer_interest_view
        rel = get_object_or_404(
            Relation.objects.select_related('opportunity', 'candidate'),
            pk=relation_id,
        )
        _, selected_store, _ = _portal_store_scope(request)
        if selected_store is not None and rel.opportunity.business_unit_id != selected_store.pk:
            return HttpResponseForbidden('Relação fora do filtro de unidade.')
        try:
            _portal_actor_for_relation(request, rel)
        except AuthorityError:
            return HttpResponseForbidden('Sem AA-6')

        # --- Phase 4 RBAC: Enforce state-based access control ---
        if rel.state not in self.VIEWABLE_STATES:
            return HttpResponseForbidden(
                f'Candidato não pode ser visualizado neste estágio ({rel.get_state_display()}). '
                'Aguarde o candidato manifestar interesse.'
            )

        return render(request, self.template_name, {
            'relation': rel,
            'view': employer_interest_view(rel),
            'contact': contact_view(rel),
            'rc_choices': [
                ('RC-01', 'Seguirei com esta pessoa'),
                ('RC-02', 'Seguirei com outra pessoa'),
                ('RC-03', 'Adiei ou cancelei a necessidade'),
                ('RC-04', 'Mudou o perfil que preciso'),
                ('RC-05', 'Outro motivo (nota obrigatória)'),
            ],
        })


class LojistaInteressarView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'

    def post(self, request, relation_id):
        from .services import employer_interested
        rel = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        try:
            _portal_actor_for_relation(request, rel, AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST)

            # --- Phase 4 RBAC: Verify state allows declaring interest ---
            if rel.state != Relation.STATE_EMPLOYER_INTEREST_VIEW:
                messages.error(
                    request,
                    f'Não é possível manifestar interesse neste estágio ({rel.get_state_display()})'
                )
                return redirect('recruitment_public:lojista_oportunidade_pilha',
                                opportunity_id=rel.opportunity_id)

            employer_interested(relation=rel, actor=request.user)
            messages.success(request, 'MATCH! Libere o contato para conversar.')
        except AuthorityError as e:
            messages.error(request, str(e))
        return redirect('recruitment_public:lojista_oportunidade_pilha',
                        opportunity_id=rel.opportunity_id)


class LojistaDeclinarView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'

    def post(self, request, relation_id):
        from .services import employer_declined
        rel = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        try:
            _portal_actor_for_relation(request, rel, AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST)

            # --- Phase 4 RBAC: Verify state allows declaring disinterest ---
            if rel.state != Relation.STATE_EMPLOYER_INTEREST_VIEW:
                messages.error(
                    request,
                    f'Não é possível declinar neste estágio ({rel.get_state_display()})'
                )
                return redirect('recruitment_public:lojista_oportunidade_pilha',
                                opportunity_id=rel.opportunity_id)

            employer_declined(relation=rel, actor=request.user, reason=request.POST.get('reason', ''))
        except AuthorityError as e:
            messages.error(request, str(e))
        return redirect('recruitment_public:lojista_oportunidade_pilha',
                        opportunity_id=rel.opportunity_id)


class LojistaLiberarContatoView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'

    # --- Phase 4 RBAC: Contact can only be enabled after bilateral match ---
    CONTACT_ENABLED_STATES = frozenset({
        Relation.STATE_MATCHED,
        Relation.STATE_CONTACT_ENABLED,
        Relation.STATE_RESPONSE_CREATED,
    })

    def post(self, request, relation_id):
        from .services import enable_contact
        rel = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        try:
            _portal_actor_for_relation(request, rel, AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL)

            # --- Phase 4 RBAC: Verify bilateral match before enabling contact ---
            if rel.state not in self.CONTACT_ENABLED_STATES:
                messages.error(
                    request,
                    f'Contato não pode ser liberado neste estágio. Aguarde confirmação bilateral.'
                )
                return redirect('recruitment_public:lojista_oportunidade_pilha',
                                opportunity_id=rel.opportunity_id)

            enable_contact(relation=rel, actor=request.user)
            messages.success(request, 'Contato liberado.')
        except AuthorityError as e:
            messages.error(request, str(e))
        return redirect('recruitment_public:lojista_relation', relation_id=rel.pk)


class LojistaResponderView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'

    # --- Phase 4 RBAC: Response can only be sent after contact enabled ---
    RESPONSE_ALLOWED_STATES = frozenset({
        Relation.STATE_CONTACT_ENABLED,
        Relation.STATE_RESPONSE_CREATED,
    })

    def post(self, request, relation_id):
        from .services import create_response
        rel = get_object_or_404(Relation, pk=relation_id)
        rc = request.POST.get('response_class', '')
        note = request.POST.get('note', '')
        try:
            _portal_actor_for_relation(request, rel, AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL)

            # --- Phase 4 RBAC: Verify contact channel was enabled ---
            if rel.state not in self.RESPONSE_ALLOWED_STATES:
                messages.error(
                    request,
                    f'Resposta não pode ser enviada neste estágio. Libere o contato primeiro.'
                )
                return redirect('recruitment_public:lojista_oportunidade_pilha',
                                opportunity_id=rel.opportunity_id)

            create_response(relation=rel, actor=request.user, response_class=rc, note=note)
            messages.success(request, f'Resposta {rc} enviada.')
        except ResponseValidationError as e:
            messages.error(request, str(e))
        return redirect('recruitment_public:lojista_relation', relation_id=rel.pk)


class LojistaPontosView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_pontos.html'

    def get(self, request):
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        eps = EntryPoint.objects.filter(organization=org).select_related('scope_store').order_by('-created_at')
        if actor and actor.business_unit_id and not request.user.is_superuser:
            eps = eps.filter(scope_store_id=actor.business_unit_id)
        eps = _portal_store_queryset(request, eps, field='scope_store')
        return render(request, self.template_name, {'entry_points': eps, 'org': org})


class LojistaPontoDetalheView(LoginRequiredMixin, View):
    """Detalhe de EntryPoint no portal do lojista — mostra QR PNG + link imprimível."""
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_ponto_detalhe.html'

    def get(self, request, entry_point_id):
        from .views import _qr_png_b64
        actor, org = _lojista_org(request)
        ep = get_object_or_404(EntryPoint, pk=entry_point_id)
        if org is None or (ep.organization_id != org.pk and not request.user.is_superuser):
            return HttpResponseForbidden()
        if actor and actor.business_unit_id and not request.user.is_superuser and ep.scope_store_id != actor.business_unit_id:
            return HttpResponseForbidden('Entrada fora do seu escopo.')
        target = request.build_absolute_uri(
            reverse('recruitment_public:entry_point_resolve', args=[str(ep.pk)]),
        )
        return render(request, self.template_name, {
            'ep': ep,
            'resolve_url': target,
            'qr_b64': _qr_png_b64(target),
            'qr_image_url': reverse('recruitment_public:entry_point_qr_image', args=[str(ep.pk)]),
            'print_url': reverse('recruitment_public:entry_point_print', args=[str(ep.pk)]),
        })


class LojistaAtoresView(LoginRequiredMixin, View):
    """Admin da rede gerencia EmployerActor + escopos AA-1..8."""
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_atores.html'

    def get(self, request):
        from .models import BusinessUnit, EmployerActor as EA
        from django.contrib.auth import get_user_model
        User = get_user_model()

        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden()

        # Só quem tem AA-1 (declarar necessidade — admin da rede) pode
        # gerenciar atores. Superuser bypass.
        if actor and not actor.has_scope(AuthorityScope.AA1_DECLARE_NEED) and not request.user.is_superuser:
            return HttpResponseForbidden('Requer AA-1 (admin da rede)')

        atores = EA.objects.filter(organization=org).select_related('user', 'business_unit').order_by('user__username')
        stores, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            atores = atores.filter(business_unit_id=actor.business_unit_id)
            stores = stores.filter(pk=actor.business_unit_id)
        elif selected_store is not None:
            atores = atores.filter(business_unit_id=selected_store.pk)
            stores = stores.filter(pk=selected_store.pk)
        aa_labels = [
            (AuthorityScope.AA1_DECLARE_NEED, 'Declarar necessidade'),
            (AuthorityScope.AA2_STRUCTURE_OPPORTUNITY, 'Estruturar oportunidade'),
            (AuthorityScope.AA3_ACTIVATE_OPPORTUNITY, 'Ativar oportunidade'),
            (AuthorityScope.AA4_MODIFY_OPPORTUNITY, 'Alterar oportunidade'),
            (AuthorityScope.AA5_CLOSE_OPPORTUNITY, 'Encerrar oportunidade'),
            (AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW, 'Ver pessoas interessadas'),
            (AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST, 'Declarar MATCH'),
            (AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL, 'Liberar contato'),
        ]
        return render(request, self.template_name, {
            'atores': atores, 'stores': stores, 'selected_store': selected_store, 'org': org,
            'aa_all': AuthorityScope.ALL, 'aa_labels': aa_labels,
        })

    def post(self, request):
        from .models import BusinessUnit, EmployerActor as EA
        from django.contrib.auth import get_user_model
        User = get_user_model()

        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden()

        action = request.POST.get('action', '')
        actor_id = request.POST.get('actor_id')

        if action == 'create':
            email = request.POST.get('email', '').strip().lower()
            if not email:
                messages.error(request, 'E-mail obrigatório')
                return redirect('recruitment_public:lojista_atores')
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'is_active': True},
            )
            store_id = request.POST.get('store_id') or None
            store = BusinessUnit.objects.filter(pk=store_id, organization=org).first() if store_id else None
            _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
            if selected_store is not None and (store is None or store.pk != selected_store.pk):
                return HttpResponseForbidden('Altere o filtro de unidade antes de operar outra loja.')
            if actor and actor.business_unit_id and not request.user.is_superuser and (store is None or store.pk != actor.business_unit_id):
                return HttpResponseForbidden('Unidade fora do seu escopo.')
            scopes = request.POST.getlist('scopes')
            ea, created = EA.objects.get_or_create(
                user=user, organization=org, business_unit=store,
                defaults={'authority_scopes': scopes},
            )
            if not created:
                ea.authority_scopes = scopes
                ea.save(update_fields=['authority_scopes', 'updated_at'])

            # Membership no configuration.Organization ativa para console middleware.
            try:
                from configuration.models import Organization as ConfigOrg, Membership
                # Atores do portal não ganham acesso ao Console. A
                # membership só é criada para o tenant correspondente ao
                # RecruitmentOrganization, nunca para a primeira empresa do
                # banco.
                console_org = ConfigOrg.objects.filter(
                    active=True, slug=org.slug,
                ).first() or ConfigOrg.objects.filter(
                    active=True, name=org.name,
                ).first()
                if console_org:
                    Membership.objects.get_or_create(
                        user=user, organization=console_org,
                        defaults={'role': 'member', 'active': True, 'is_primary': True},
                    )
            except Exception:
                pass

            messages.success(request, f'Ator {email} {"criado" if created else "atualizado"}.')

        elif action == 'update_scopes' and actor_id:
            ea = get_object_or_404(EA, pk=actor_id, organization=org)
            ea.authority_scopes = request.POST.getlist('scopes')
            ea.save(update_fields=['authority_scopes', 'updated_at'])
            messages.success(request, 'Escopos atualizados.')

        elif action == 'verify_human' and actor_id:
            ea = get_object_or_404(EA, pk=actor_id, organization=org)
            ea.human_verified_at = timezone.now()
            ea.save(update_fields=['human_verified_at', 'updated_at'])
            messages.success(request, 'Ator verificado como humano — AA-7/AA-8 liberados.')

        elif action == 'deactivate' and actor_id:
            ea = get_object_or_404(EA, pk=actor_id, organization=org)
            ea.active = False
            ea.save(update_fields=['active', 'updated_at'])
            messages.success(request, 'Ator desativado.')

        elif action == 'activate' and actor_id:
            ea = get_object_or_404(EA, pk=actor_id, organization=org)
            ea.active = True
            ea.save(update_fields=['active', 'updated_at'])
            messages.success(request, 'Ator reativado.')

        return redirect('recruitment_public:lojista_atores')


class LojistaInvitesView(LoginRequiredMixin, View):
    """Sponsor cria convites para novos lojistas. Só quem tem AA-1."""
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_invites.html'

    def get(self, request):
        from .models import BusinessUnit, LojistaInvite
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden()
        if actor and not actor.has_scope(AuthorityScope.AA1_DECLARE_NEED) and not request.user.is_superuser:
            return HttpResponseForbidden('Requer AA-1')
        invites = LojistaInvite.objects.filter(organization=org).select_related('business_unit').order_by('-created_at')[:50]
        stores, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            stores = stores.filter(pk=actor.business_unit_id)
            invites = invites.filter(business_unit_id=actor.business_unit_id)
        elif selected_store is not None:
            stores = stores.filter(pk=selected_store.pk)
            invites = invites.filter(business_unit_id=selected_store.pk)
        return render(request, self.template_name, {
            'invites': invites, 'stores': stores, 'selected_store': selected_store, 'org': org,
            'aa_all': AuthorityScope.ALL,
        })

    def post(self, request):
        import secrets
        from datetime import timedelta as _td
        from .models import BusinessUnit, LojistaInvite
        from django.core.mail import send_mail
        from django.conf import settings as _s
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden()

        email = request.POST.get('email', '').strip().lower()
        store_id = request.POST.get('store_id') or None
        scopes = request.POST.getlist('scopes')
        if not email:
            messages.error(request, 'E-mail obrigatório')
            return redirect('recruitment_public:lojista_invites')
        store = BusinessUnit.objects.filter(pk=store_id, organization=org).first() if store_id else None
        _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        if selected_store is not None and (store is None or store.pk != selected_store.pk):
            return HttpResponseForbidden('Altere o filtro de unidade antes de operar outra loja.')
        if actor and actor.business_unit_id and not request.user.is_superuser and (store is None or store.pk != actor.business_unit_id):
            return HttpResponseForbidden('Unidade fora do seu escopo.')

        token = secrets.token_urlsafe(32)
        invite = LojistaInvite.objects.create(
            organization=org, business_unit=store, email=email,
            scopes=scopes, token=token, invited_by=request.user,
            expires_at=timezone.now() + _td(days=7),
        )

        accept_url = request.build_absolute_uri(
            reverse('recruitment_public:lojista_invite_accept', args=[token]),
        )
        try:
            send_mail(
                subject=f'Convite MatchCo — {org.name}',
                message=(
                    f'Você foi convidado(a) por {org.name} a usar o MatchCo.\n\n'
                    f'Crie sua conta em: {accept_url}\n\nLink válido por 7 dias.'
                ),
                from_email=getattr(_s, 'DEFAULT_FROM_EMAIL', 'noreply@matchco.example'),
                recipient_list=[email], fail_silently=True,
            )
            messages.success(request, f'Convite enviado para {email}.')
        except Exception:
            messages.warning(request, f'Convite criado, envio falhou. Link: {accept_url}')
        return redirect('recruitment_public:lojista_invites')


class LojistaInviteAcceptView(View):
    """Público — lojista clica no link e solicita acesso; gestor aprova depois."""
    template_name = 'recruitment/portal/lojista_invite_accept.html'

    def _find(self, token):
        from .models import LojistaInvite
        return LojistaInvite.objects.filter(token=token).first()

    def get(self, request, token):
        inv = self._find(token)
        if inv is None or not inv.is_valid():
            return render(request, self.template_name, {'error': 'Convite inválido ou expirado.'})
        return render(request, self.template_name, {'invite': inv})

    def post(self, request, token):
        from django.contrib.auth import get_user_model
        from .models import LojistaInvite
        from .services import create_controlled_access_request
        User = get_user_model()
        inv = self._find(token)
        if inv is None or not inv.is_valid():
            return render(request, self.template_name, {'error': 'Convite inválido ou expirado.'})

        password = request.POST.get('password', '')
        if len(password) < 8:
            return render(request, self.template_name, {
                'invite': inv, 'error': 'Senha precisa de ao menos 8 caracteres.',
            })

        user, _c = User.objects.get_or_create(
            username=inv.email,
            defaults={'email': inv.email, 'is_active': True},
        )
        user.set_password(password)
        user.save(update_fields=['password'])

        access_request = create_controlled_access_request(
            organization=inv.organization,
            request_type='employer',
            email=inv.email,
            user=user,
            business_unit=inv.business_unit,
            role='employer_actor',
            scopes=inv.scopes or [],
            requested_by=user,
            state='pending_approval',
        )

        inv.state = LojistaInvite.STATE_PENDING_APPROVAL
        inv.accepted_at = timezone.now()
        inv.save(update_fields=['state', 'accepted_at'])
        return render(request, 'recruitment/portal/lojista_invite_pending.html', {
            'invite': inv, 'access_request': access_request,
        })


class LojistaMetricasView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/lojista_metricas.html'

    def get(self, request):
        from .metrics import dashboard
        actor, org = _lojista_org(request)
        if org is None:
            return HttpResponseForbidden()
        days = int(request.GET.get('days', 30))
        _, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        return render(request, self.template_name, {
            'data': dashboard(
                organization=org,
                business_unit=selected_store or (actor.business_unit if actor and not request.user.is_superuser else None),
                days=days,
            ),
            'org': org, 'selected_store': selected_store,
        })


# =============================================================================
# Shopping / sponsor
# =============================================================================

class ShoppingCadastrarView(TemplateView):
    """Signup do sponsor: cria RecruitmentOrganization + primeiro admin."""
    template_name = 'recruitment/portal/shopping_cadastrar.html'

    def post(self, request):
        from django.contrib.auth import authenticate, login
        from django.contrib.auth import get_user_model
        from django.utils.text import slugify
        from .domain_models import (
            RecruitmentOrganization, RecruitmentCompany, RecruitmentStore,
        )
        from .models import EmployerActor as EA
        User = get_user_model()

        org_name = request.POST.get('org_name', '').strip()
        admin_email = request.POST.get('admin_email', '').strip().lower()
        admin_password = request.POST.get('admin_password', '')
        first_store_name = request.POST.get('first_store_name', '').strip()
        first_store_postal_code = re.sub(r'\D', '', request.POST.get('first_store_postal_code', ''))[:8]

        errors = {}
        if not org_name: errors['org_name'] = 'Obrigatório'
        if not admin_email: errors['admin_email'] = 'Obrigatório'
        if not admin_password or len(admin_password) < 8:
            errors['admin_password'] = 'Mínimo 8 caracteres'

        if not errors and User.objects.filter(username=admin_email).exists():
            errors['admin_email'] = 'Já existe usuário com este e-mail — use outro ou faça login.'

        if errors:
            return render(request, self.template_name, {
                'errors': errors, 'form': request.POST,
            })

        base_slug = slugify(org_name)[:150] or 'organizacao'
        slug = base_slug
        i = 1
        while RecruitmentOrganization.objects.filter(slug=slug).exists():
            i += 1
            slug = f'{base_slug}-{i}'

        org = RecruitmentOrganization.objects.create(
            external_id=slug, slug=slug, name=org_name, active=True,
        )
        company = RecruitmentCompany.objects.create(organization=org, name=org_name)
        if first_store_name:
            RecruitmentStore.objects.create(
                organization=org, company=company, name=first_store_name,
                postal_code=first_store_postal_code,
            )

        user = User.objects.create_user(
            username=admin_email, email=admin_email,
            password=admin_password, is_staff=True,
        )
        EA.objects.create(
            user=user, organization=org,
            authority_scopes=AuthorityScope.ALL,
            human_verified_at=timezone.now(),
        )
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

        authed = authenticate(request, username=admin_email, password=admin_password)
        if authed:
            login(request, authed)
        messages.success(request, f'{org_name} criado. Bem-vindo(a) ao MatchCo!')
        return redirect('recruitment_public:lojista_home')


class ShoppingEntrarView(TemplateView):
    template_name = 'recruitment/portal/shopping_entrar.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('recruitment_public:lojista_home')
        return super().get(request, *args, **kwargs)

    def post(self, request):
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, self.template_name, {
                'error': 'Usuário ou senha inválidos.', 'username': username,
            })
        login(request, user)
        return redirect('recruitment_public:lojista_home')


class ShoppingHomeView(LoginRequiredMixin, View):
    login_url = '/portal/entrar/'
    template_name = 'recruitment/portal/shopping_home.html'

    def get(self, request):
        from .metrics import dashboard
        from .models import CandidateProfile, EntryPoint, Position, Program
        actor, org = _lojista_org(request)  # mesma resolução (por Membership)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        stores, selected_store, _ = _portal_store_scope(request, actor=actor, org=org)
        funnel_labels = {
            'notice_delivered': ('Necessidade comunicada', 'A oportunidade chegou às pessoas elegíveis.'),
            'person_interested': ('Pessoa demonstrou interesse', 'Alguém respondeu que quer conhecer a oportunidade.'),
            'employer_interest_view': ('Loja visualizou o interesse', 'A loja recebeu o sinal de interesse para avaliar.'),
            'employer_interested': ('Loja demonstrou interesse', 'A loja confirmou que quer avançar com a pessoa.'),
            'matched': ('Match realizado', 'Os dois lados demonstraram interesse.'),
            'contact_enabled': ('Contato liberado', 'O contato foi liberado após o match.'),
            'response_created': ('Resposta registrada', 'A conversa teve uma resposta registrada.'),
            'closed': ('Encerrado', 'A oportunidade foi concluída ou encerrada.'),
            'declined': ('Recusado', 'Uma das partes decidiu não seguir.'),
            'no_employer_interest': ('Sem interesse da loja', 'A loja não avançou nesta oportunidade.'),
        }
        data = dashboard(organization=org, business_unit=selected_store, days=30)
        data_funnel = data['funnel']
        funnel_max = max((row['count'] for row in data_funnel), default=1)
        funnel_rows = [
            {
                **row,
                'position': index + 1,
                'label': funnel_labels.get(row['state'], (row['state'], ''))[0],
                'description': funnel_labels.get(row['state'], (row['state'], ''))[1],
                'percent': round((row['count'] / funnel_max) * 100) if funnel_max else 0,
            }
            for index, row in enumerate(data_funnel)
        ]
        data['funnel'] = funnel_rows
        summary = {
            'stores': stores.count() if hasattr(stores, 'count') else len(stores),
            'companies': org.companies.filter(active=True).count() if hasattr(org, 'companies') else 0,
            'people': CandidateProfile.objects.filter(organization=org).count(),
            'opportunities': _portal_store_queryset(request, Position.objects.filter(organization=org, state__in=[Position.STATE_ACTIVATED, Position.STATE_CIRCULATED])).count(),
            'entry_points': _portal_store_queryset(request, EntryPoint.objects.filter(organization=org, state=EntryPoint.STATE_ACTIVE), field='scope_store').count(),
            'programs': Program.objects.filter(organization=org, status=Program.STATUS_ACTIVE).count(),
        }
        return render(request, self.template_name, {
            'data': data,
            'org': org, 'stores': stores, 'selected_store': selected_store, 'summary': summary,
        })
