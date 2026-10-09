from django.utils.translation import gettext_lazy as gettext_lazy
import io
import base64
import re
from functools import wraps
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import Http404, HttpResponseForbidden, HttpResponseGone, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import TemplateView, View
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .forms import EntryPointForm, MatchcoSignupForm
from .models import (
    CandidateProfile, Position, CandidateOnboardingTrail,
    CandidateProfileSurveyResponse,
    CandidateSignupAnswer,
    CandidateIdentity,
    CandidateConsent,
    EnrichmentInvite,
    Program, ProgramInvite, ProgramMembership, ProgramResource,
    EntryPoint,
    Relation,
    RelationStateError,
    ContactChannel,
    AuthorityError,
    AuthorityScope,
)
from .integrations.organization import (
    active_organizations,
    find_organization,
    find_store,
    job_functions_for_organization,
    job_functions_for_store,
    employee_store_for_request,
    has_recruitment_access,
)
from .services import (
    register_candidate,
    revoke_consent,
    export_identity_data,
    anonymize_identity,
    audit_event,
    set_cpf,
    resolve_or_create_identity,
    record_candidate_context,
    IdentityConflict,
    create_controlled_access_request,
)
from .questionnaires import questionnaire_questions, resolve_questionnaire


def _optional_ratelimit(**kwargs):
    """Apply public endpoint limits outside local development."""
    def decorate(view):
        limited_view = ratelimit(**kwargs)(view)

        @wraps(view)
        def wrapped(*args, **inner_kwargs):
            if not getattr(settings, 'RATELIMIT_ENABLE', True):
                return view(*args, **inner_kwargs)
            return limited_view(*args, **inner_kwargs)

        return wrapped

    return decorate


class HTMXMixin:
    """No-op mixin. HTMX handling done via hx-select on the client side."""
    pass


class EnrichmentCampaignView(View):
    """Public optional questionnaire; the opaque invite is the only identity."""
    template_name = 'recruitment/enrichment_campaign.html'

    def _invite(self, token):
        return EnrichmentInvite.objects.select_related(
            'campaign', 'campaign__questionnaire_template', 'candidate',
        ).filter(token=token).first()

    def _questions(self, invite):
        return questionnaire_questions(invite.campaign.questionnaire_template)

    def get(self, request, token):
        invite = self._invite(token)
        if invite is None or invite.state in (EnrichmentInvite.STATE_REVOKED, EnrichmentInvite.STATE_DECLINED, EnrichmentInvite.STATE_EXPIRED):
            return render(request, self.template_name, {'error': 'Este convite não está mais disponível.'}, status=410)
        if invite.expires_at < timezone.now():
            invite.state = EnrichmentInvite.STATE_EXPIRED
            invite.save(update_fields=['state'])
            return render(request, self.template_name, {'error': 'Este convite expirou.'}, status=410)
        if invite.state == EnrichmentInvite.STATE_INVITED:
            invite.state = EnrichmentInvite.STATE_STARTED
            invite.started_at = timezone.now()
            invite.save(update_fields=['state', 'started_at'])
        return render(request, self.template_name, {
            'invite': invite, 'campaign': invite.campaign,
            'questions': self._questions(invite),
        })

    def post(self, request, token):
        invite = self._invite(token)
        if invite is None:
            return render(request, self.template_name, {'error': 'Convite não encontrado.'}, status=404)
        if request.POST.get('action') == 'decline':
            invite.state = EnrichmentInvite.STATE_DECLINED
            invite.declined_at = timezone.now()
            invite.save(update_fields=['state', 'declined_at'])
            return render(request, self.template_name, {'declined': True})
        if request.POST.get('consent') != 'on':
            return render(request, self.template_name, {
                'invite': invite, 'campaign': invite.campaign,
                'questions': self._questions(invite),
                'error': 'É necessário aceitar o uso dessas respostas para continuar.',
            })
        responses = {}
        for question in self._questions(invite):
            value = request.POST.getlist(question['id']) if question['type'] == 'checkbox' else request.POST.get(question['id'], '')
            if value:
                responses[question['id']] = value
        from .services import record_enrichment_response
        try:
            record_enrichment_response(invite=invite, responses=responses, consented_at=timezone.now())
        except ValueError as exc:
            return render(request, self.template_name, {'error': str(exc)}, status=400)
        return render(request, self.template_name, {'completed': True})


class CandidateDataExportView(View):
    def get(self, request, *args, **kwargs):
        candidate_id = request.session.get('recruitment_last_candidate_id')
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        if not candidate.identity:
            return JsonResponse({'error': 'identity_not_available'}, status=404)
        return JsonResponse(export_identity_data(identity=candidate.identity, request=request))


class CandidateDataCorrectionView(View):
    def post(self, request, *args, **kwargs):
        candidate_id = request.session.get('recruitment_last_candidate_id')
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        allowed = ('phone', 'address', 'city', 'state', 'bio', 'linkedin_url')
        changed = []
        for field in allowed:
            if field in request.POST:
                setattr(candidate, field, request.POST.get(field, '').strip())
                changed.append(field)
        if changed:
            candidate.save(update_fields=changed + ['updated_at'])
            audit_event(action='data_corrected', identity=candidate.identity, organization=candidate.organization, request=request, object_type='CandidateProfile', object_id=candidate.pk, metadata={'fields': changed})
        return JsonResponse({'updated': changed})


class CandidateAnonymizeView(View):
    def post(self, request, *args, **kwargs):
        candidate_id = request.session.get('recruitment_last_candidate_id')
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        if not candidate.identity:
            return JsonResponse({'error': 'identity_not_available'}, status=404)
        anonymize_identity(identity=candidate.identity, request=request, reason=request.POST.get('reason', 'LGPD request'))
        request.session.pop('recruitment_last_candidate_id', None)
        return JsonResponse({'status': 'anonymized'})


# ---------- Console (staff-only) ----------

class OrgScopedMixin(HTMXMixin, LoginRequiredMixin):
    """Restrict queryset to the active organization on the request."""

    def get_active_org(self):
        org_id = getattr(self.request, 'active_organization_id', None)
        if not org_id:
            org_id = self.request.session.get('active_organization_id')
        if not org_id:
            return None
        return find_organization(pk=org_id)

    def dispatch(self, request, *args, **kwargs):
        self.active_org = self.get_active_org()
        if not self.active_org:
            messages.error(request, gettext_lazy('No active organization selected.'))
            return redirect('home')
        if not has_recruitment_access(request, self.active_org):
            return HttpResponseForbidden('Você não tem acesso ao recrutamento desta organização.')
        self.access_store = employee_store_for_request(request, self.active_org)
        return super().dispatch(request, *args, **kwargs)

    def require_write_access(self):
        if not has_recruitment_access(self.request, self.active_org, write=True):
            return HttpResponseForbidden('Você não tem permissão para alterar o recrutamento desta organização.')
        return None


class _QRCodeContextMixin(OrgScopedMixin):
    """Shared context for the active Match QR pages."""

    template_name = 'recruitment/console/qr_code.html'

    def build_qr_context(self, store=None):
        import qrcode
        from django.conf import settings
        from .url_builders import URLBuilder
        filters = dict(
            organization=self.active_org,
            purpose=EntryPoint.PURPOSE_RECRUITMENT,
            mode=EntryPoint.MODE_MATCH,
            state__in=[EntryPoint.STATE_ACTIVE, EntryPoint.STATE_TESTED],
        )
        if store is not None:
            filters.update(scope_store=store, kind=EntryPoint.KIND_STORE)
        else:
            filters.update(scope_store__isnull=True)
        entry_points = list(EntryPoint.objects.filter(**filters).order_by('-created_at'))
        entry_point = entry_points[0] if entry_points else None

        signup_url = ''
        if entry_point:
            qr_code_url = getattr(settings, 'QR_CODE_BASE_URL', None)
            if qr_code_url:
                signup_url = f'{qr_code_url.rstrip("/")}{reverse("recruitment_public:entry_point_resolve", args=[str(entry_point.pk)])}'
            else:
                signup_url = self.request.build_absolute_uri(
                    reverse('recruitment_public:entry_point_resolve', args=[str(entry_point.pk)])
                )

        # Optional: Add UTM parameters from query string
        # Usage: ?utm_source=flyer&utm_campaign=bourbon_store5&utm_content=reception_area
        campaign_name = self.request.GET.get('campaign_name')
        utm_source = self.request.GET.get('utm_source')
        utm_medium = self.request.GET.get('utm_medium')
        utm_campaign = self.request.GET.get('utm_campaign')
        utm_content = self.request.GET.get('utm_content') or (store.name if store else self.active_org.name)
        utm_term = self.request.GET.get('utm_term')
        qr_id = self.request.GET.get('qr_id')

        if (campaign_name or utm_source) and signup_url:
            signup_url = URLBuilder.add_utm_params(
                signup_url,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_content=utm_content,
                utm_term=utm_term,
                qr_id=qr_id,
            )

        img = qrcode.make(signup_url, box_size=10, border=2) if signup_url else None
        buf = io.BytesIO()
        if img:
            img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii') if img else ''

        return {
            'active_org': self.active_org,
            'store': store,
            'entry_points': entry_points,
            'entry_point': entry_point,
            'qr_mode': EntryPoint.MODE_MATCH,
            'signup_url': signup_url,
            'qr_data_url': f'data:image/png;base64,{b64}',
            'page_title': f'QR Code - {store.name}' if store else f'QR Code - {self.active_org.name}',
        }


class QRCodeView(_QRCodeContextMixin, TemplateView):
    """QR institucional da organização para a porta Match."""

    template_name = 'recruitment/console/qr_code.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.build_qr_context())
        return context


class QRCodeStoreView(_QRCodeContextMixin, TemplateView):
    """QR específico de uma loja/unidade, sempre escopado à organização ativa."""

    template_name = 'recruitment/console/qr_code_store.html'

    def get_context_data(self, **kwargs):
        self.store = find_store(store_id=self.kwargs.get('store_id'), organization=self.active_org)
        if not self.store:
            raise Http404('Loja/unidade não encontrada')
        context = super().get_context_data(**kwargs)
        context.update(self.build_qr_context(store=self.store))
        return context


# ---------- Candidate onboarding trail ----------

class CandidateOnboardingJobFunctionsView(TemplateView):
    """Step 1: Candidate selects job functions of interest."""
    template_name = 'recruitment/onboarding/job_functions.html'

    def get_organization(self):
        slug = self.request.GET.get('org') or self.request.POST.get('org')
        if not slug:
            return None
        return find_organization(slug=slug)

    def dispatch(self, request, *args, **kwargs):
        self.organization = self.get_organization()
        if not self.organization:
            return render(request, 'recruitment/no_organization.html')
        candidate_id = request.GET.get('candidate_id') or request.POST.get('candidate_id')
        if not candidate_id or str(request.session.get('recruitment_last_candidate_id')) != str(candidate_id):
            return HttpResponseForbidden('Sessão de candidato inválida.')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job_functions = job_functions_for_organization(self.organization)

        ctx['organization'] = self.organization
        ctx['job_functions'] = job_functions
        ctx['candidate_id'] = self.request.GET.get('candidate_id')
        return ctx

    def post(self, request, *args, **kwargs):
        org_slug = request.POST.get('org')
        candidate_id = request.POST.get('candidate_id')
        selected_functions = request.POST.getlist('job_functions')

        try:
            candidate = CandidateProfile.objects.get(pk=candidate_id, organization__slug=org_slug)
            candidate.job_functions.set(selected_functions)

            # Redirect to profile survey
            return redirect(
                'recruitment_public:candidate_survey',
                candidate_id=candidate_id,
            )
        except CandidateProfile.DoesNotExist:
            messages.error(request, gettext_lazy('Candidate not found.'))
            return redirect('recruitment_public:candidato_signup')


class CandidateProfileSurveyView(TemplateView):
    """Step 2: Candidate completes profile survey."""
    template_name = 'recruitment/onboarding/profile_survey.html'

    def get_candidate(self):
        candidate_id = self.kwargs.get('candidate_id')
        try:
            return CandidateProfile.objects.get(pk=candidate_id)
        except CandidateProfile.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        if str(request.session.get('recruitment_last_candidate_id')) != str(self.kwargs.get('candidate_id')):
            return HttpResponseForbidden('Sessão de candidato inválida.')
        self.candidate = self.get_candidate()
        if not self.candidate:
            raise Http404('Candidate not found')
        # The resolver uses the entry-point audience role without coupling the
        # domain model to Django's request object.
        self.candidate._matchco_request = request
        return super().dispatch(request, *args, **kwargs)

    def get_entry_point(self):
        entry_point_id = self.request.session.get('ep_id')
        if not entry_point_id:
            return None
        return EntryPoint.objects.filter(pk=entry_point_id).first()

    def get_questionnaire(self):
        if not hasattr(self, '_resolved_questionnaire'):
            self._resolved_questionnaire = resolve_questionnaire(
                self.candidate,
                entry_point=self.get_entry_point(),
            )
        return self._resolved_questionnaire

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['candidate'] = self.candidate
        ctx['questionnaire'] = self.get_questionnaire()
        ctx['survey_questions'] = self.get_survey_questions()

        return ctx

    def post(self, request, *args, **kwargs):
        responses = {}
        for question in self.get_survey_questions():
            if question['type'] == 'checkbox':
                value = request.POST.getlist(question['id'])
            else:
                value = request.POST.get(question['id'], '').strip()
            if value:
                responses[question['id']] = value

        # Keep the legacy summary for compatibility, but preserve every
        # contextual submission separately. A new visit is never prefilled.
        survey, _ = CandidateProfileSurveyResponse.objects.get_or_create(
            candidate=self.candidate,
            organization=self.candidate.organization,
        )
        survey.responses = responses
        survey.questionnaire_template = self.get_questionnaire()
        survey.save()

        entry_point = self.get_entry_point()
        CandidateSignupAnswer.objects.create(
            candidate=self.candidate,
            organization=self.candidate.organization,
            business_unit=entry_point.scope_store if entry_point else None,
            entry_point=entry_point,
            questionnaire_template=self.get_questionnaire(),
            created_via_questionnaire_version=(self.get_questionnaire().version if self.get_questionnaire() else 1),
            relation_state_at_response='not_interested',
            responses=responses,
        )

        # Mark trail as completed
        trail, _ = CandidateOnboardingTrail.objects.get_or_create(
            candidate=self.candidate,
            organization=self.candidate.organization,
        )
        trail.survey_completed = True
        trail.status = CandidateOnboardingTrail.STATUS_COMPLETED
        trail.mark_completed()

        # Mark candidate as onboarding completed
        self.candidate.onboarding_completed = True
        self.candidate.save(update_fields=['onboarding_completed', 'updated_at'])

        return redirect('recruitment_public:candidate_onboarding_complete', candidate_id=self.candidate.pk)

    def get_survey_questions(self):
        questionnaire = self.get_questionnaire()
        if questionnaire:
            return questionnaire_questions(questionnaire)

        # Compatibility fallback for organizations that have not bootstrapped
        # a template yet. The seed command replaces this list with editable
        # versions without changing the candidate journey.
        return [
            {
                'id': 'experience',
                'label': 'Qual é sua experiência anterior em vendas ou atendimento?',
                'type': 'textarea',
                'required': True,
            },
            {
                'id': 'interests',
                'label': 'Em qual tipo de loja você mais gostaria de trabalhar?',
                'type': 'select',
                'options': ['Moda e vestuário', 'Eletrônicos', 'Alimentação', 'Beleza', 'Serviços', 'Aberto a oportunidades'],
            },
            {
                'id': 'skills',
                'label': 'Quais são suas principais habilidades profissionais?',
                'type': 'textarea',
                'required': True,
            },
            {
                'id': 'availability',
                'label': 'Qual é sua disponibilidade de horários? (dias e turnos)',
                'type': 'textarea',
            },
            {
                'id': 'work_model',
                'label': 'Você tem disponibilidade para trabalhar presencialmente?',
                'type': 'radio',
                'options': ['Sim', 'Não', 'Depende da localização'],
            },
            {
                'id': 'customer_scenario',
                'label': 'Como você atenderia uma pessoa indecisa ou insatisfeita?',
                'type': 'textarea',
                'required': True,
            },
            {
                'id': 'start_date',
                'label': 'Quando você poderia começar?',
                'type': 'select',
                'options': ['Imediatamente', 'Em até 15 dias', 'Em até 30 dias', 'A combinar'],
            },
        ]


class CandidateOnboardingCompleteView(TemplateView):
    """Step 3: Confirmation page after onboarding completion."""
    template_name = 'recruitment/onboarding/complete.html'

    def get_candidate(self):
        candidate_id = self.kwargs.get('candidate_id')
        try:
            return CandidateProfile.objects.get(pk=candidate_id)
        except CandidateProfile.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        if str(request.session.get('recruitment_last_candidate_id')) != str(self.kwargs.get('candidate_id')):
            return HttpResponseForbidden('Sessão de candidato inválida.')
        self.candidate = self.get_candidate()
        if not self.candidate:
            raise Http404('Candidate not found')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['candidate'] = self.candidate

        return ctx


class JobFunctionsForBusinessUnitView(OrgScopedMixin, View):
    """API endpoint returning valid job functions for a business unit (for dynamic form filtering)."""

    def get(self, request, business_unit_id, *args, **kwargs):
        from django.http import JsonResponse
        from .models import CanonicalFunctionMapping

        try:
            business_unit = find_store(
                store_id=business_unit_id,
                organization=self.active_org,
            )
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Business unit not found'}, status=404)

        if not business_unit:
            return JsonResponse({'error': 'Business unit not found'}, status=404)

        mappings = CanonicalFunctionMapping.objects.filter(
            organization=business_unit.organization, active=True,
            term__active=True, job_function__active=True,
        ).filter(Q(business_unit=business_unit) | Q(business_unit__isnull=True)).select_related(
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
        return JsonResponse({
            'business_unit': business_unit.name,
            'channel': business_unit.channel.name if business_unit.channel else None,
            'job_functions': function_rows,
        })


# ---------------------------------------------------------------------------
# Porta Match — resolução de EntryPoint (Fase 1)
# ---------------------------------------------------------------------------

def _qr_png_b64(url, box_size=10, border=2):
    """Gera QR code PNG e retorna base64 pronto pra <img src>."""
    import qrcode
    img = qrcode.make(url, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


def _entry_experience(entry_point=None):
    """Build the public experience context without creating tenant templates."""
    if not entry_point:
        return {
            'template': EntryPoint.EXPERIENCE_GENERIC,
            'brand_name': 'MatchCo',
            'display_name': 'MatchCo',
            'headline': 'Crie seu perfil e encontre o próximo passo.',
            'subheadline': 'Uma entrada simples para oportunidades, programas e relações profissionais.',
            'accent_color': '#f97316',
            'scope_label': '',
        }

    defaults = {
        EntryPoint.EXPERIENCE_SHOPPING: (
            'Entre no território e encontre oportunidades nas operações participantes.',
            'O shopping conecta lojas, pessoas, conteúdo e oportunidades.',
        ),
        EntryPoint.EXPERIENCE_MANUFACTURER: (
            'Faça parte da rede de parceiros e acesse oportunidades e conhecimento da marca.',
            'Fabricantes podem conectar distribuidores, revendedores, lojas e profissionais.',
        ),
        EntryPoint.EXPERIENCE_DISTRIBUTOR: (
            'Acesse os programas e oportunidades do canal.',
            'Um espaço para parceiros, equipes comerciais, técnicos e clientes profissionais.',
        ),
        EntryPoint.EXPERIENCE_RETAIL: (
            'Encontre oportunidades e programas da rede.',
            'A mesma entrada conecta lojas, equipes, candidatos e conteúdos da operação.',
        ),
        EntryPoint.EXPERIENCE_HOSPITAL: (
            'Acesse oportunidades e programas da organização de saúde.',
            'Cada unidade e função recebe o contexto adequado para sua jornada.',
        ),
        EntryPoint.EXPERIENCE_CORPORATE: (
            'Acesse a experiência profissional da organização.',
            'Conteúdo, programas, oportunidades e relacionamentos em um só lugar.',
        ),
        EntryPoint.EXPERIENCE_GENERIC: (
            'Crie seu perfil e encontre o próximo passo.',
            'Uma entrada simples para oportunidades, programas e relações profissionais.',
        ),
    }
    template_key = entry_point.experience_template
    organization_template = getattr(entry_point.organization, 'default_entry_template', '')
    if template_key == EntryPoint.EXPERIENCE_GENERIC and organization_template:
        template_key = organization_template
    default_headline, default_subheadline = defaults.get(
        template_key, defaults[EntryPoint.EXPERIENCE_GENERIC],
    )
    organization_brand = getattr(entry_point.organization, 'brand_name', '')
    organization_logo = getattr(entry_point.organization, 'logo_url', '')
    organization_color = getattr(entry_point.organization, 'primary_color', '')
    display_name = entry_point.brand_name or organization_brand or entry_point.organization.name
    scope_label = entry_point.organization.name
    if entry_point.scope_store:
        scope_label = f'{entry_point.scope_store.name} · {entry_point.organization.name}'
    return {
        'template': template_key,
        'brand_name': entry_point.brand_name or organization_brand or entry_point.organization.name,
        'display_name': display_name,
        'brand_logo_url': entry_point.brand_logo_url or organization_logo,
        'headline': entry_point.headline or default_headline,
        'subheadline': entry_point.subheadline or default_subheadline,
        'accent_color': (organization_color if entry_point.accent_color == '#f97316' and organization_color else entry_point.accent_color) or '#f97316',
        'scope_label': scope_label,
        'audience_label': entry_point.get_audience_role_display(),
        'purpose_label': entry_point.get_purpose_display(),
    }


class EntryPointQrImageView(View):
    """Retorna PNG do QR pronto pra download (imprimir)."""
    def get(self, request, entry_point_id):
        from django.http import HttpResponse
        import qrcode
        ep = get_object_or_404(
            EntryPoint,
            pk=entry_point_id,
            state__in=[EntryPoint.STATE_ACTIVE, EntryPoint.STATE_TESTED],
        )
        target = request.build_absolute_uri(
            reverse('recruitment_public:entry_point_resolve', args=[str(ep.pk)]),
        )
        img = qrcode.make(target, box_size=15, border=3)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        resp = HttpResponse(buf.getvalue(), content_type='image/png')
        resp['Content-Disposition'] = f'inline; filename="matchco-qr-{ep.pk}.png"'
        return resp


class ProgramEntryView(View):
    """Página pública de um programa acessado por QR."""
    template_name = 'recruitment/match/program_entry.html'

    def get(self, request, entry_point_id):
        ep = get_object_or_404(
            EntryPoint.objects.select_related('organization', 'scope_store', 'program'),
            pk=entry_point_id,
            state=EntryPoint.STATE_ACTIVE,
        )
        if not ep.program_id or ep.program.status != Program.STATUS_ACTIVE:
            raise Http404('Programa não está disponível')
        if ep.program.access_level == Program.ACCESS_AUTHENTICATED and not request.user.is_authenticated:
            return redirect(f'{reverse("login")}?next={request.path}')
        if ep.program.access_level == Program.ACCESS_MEMBERS:
            if not request.user.is_authenticated or not ProgramMembership.objects.filter(
                user_id=request.user.pk, program=ep.program, active=True,
                state=ProgramMembership.STATE_ACTIVE,
            ).exists():
                return HttpResponseForbidden('Este programa é privado para membros autorizados.')
        request.session['ep_id'] = str(ep.id)
        request.session['ep_mode'] = ep.mode
        request.session['ep_kind'] = ep.kind
        request.session['ep_purpose'] = ep.purpose
        request.session['ep_audience'] = ep.audience
        request.session['ep_audience_role'] = ep.audience_role
        request.session['program_id'] = str(ep.program_id)
        from .services import resolve_platform_context
        platform_context = resolve_platform_context(
            organization=ep.organization,
            business_unit=ep.scope_store,
            program=ep.program,
        )
        if platform_context['platform_organization_ids']:
            request.session['recruitment_platform_context'] = platform_context
            request.session.modified = True
        return render(request, self.template_name, {
            'entry_point': ep,
            'program': ep.program,
            'resources': ep.program.resources.all(),
            'entry_context': _entry_experience(ep),
        })


class ProgramDirectView(View):
    """Página direta de um programa, usada após convite privado aceito."""
    template_name = 'recruitment/match/program_entry.html'

    def get(self, request, program_id):
        program = get_object_or_404(Program, pk=program_id, status=Program.STATUS_ACTIVE)
        if program.access_level == Program.ACCESS_AUTHENTICATED and not request.user.is_authenticated:
            return redirect(f'{reverse("login")}?next={request.path}')
        if program.access_level == Program.ACCESS_MEMBERS:
            if not request.user.is_authenticated or not ProgramMembership.objects.filter(
                user_id=request.user.pk, program=program, active=True,
                state=ProgramMembership.STATE_ACTIVE,
            ).exists():
                return HttpResponseForbidden('Este programa é privado para membros autorizados.')
        request.session['program_id'] = str(program.pk)
        from .services import resolve_platform_context
        platform_context = resolve_platform_context(
            organization=program.organization,
            program=program,
        )
        if platform_context['platform_organization_ids']:
            request.session['recruitment_platform_context'] = platform_context
            request.session.modified = True
        return render(request, self.template_name, {
            'entry_point': None,
            'program': program,
            'resources': program.resources.all(),
            'entry_context': _entry_experience(None),
        })


class EntryPointPrintView(View):
    """Página imprimível: cartaz com QR + call-to-action MatchCo."""
    template_name = 'recruitment/portal/qr_print.html'

    def get(self, request, entry_point_id):
        ep = get_object_or_404(
            EntryPoint.objects.select_related('scope_store', 'organization'),
            pk=entry_point_id,
            state__in=[EntryPoint.STATE_ACTIVE, EntryPoint.STATE_TESTED],
        )
        target = request.build_absolute_uri(
            reverse('recruitment_public:entry_point_resolve', args=[str(ep.pk)]),
        )
        return render(request, self.template_name, {
            'ep': ep,
            'qr_b64': _qr_png_b64(target, box_size=15, border=3),
            'target': target,
        })


class EntryPointResolveView(View):
    """Resolve o QR canônico MatchCo para o destino apropriado.

    Regras (SISTEMA_MATCHCO_CANONICO §3.8, §7):
    - state ACTIVE: segue para destino canônico com contexto do EntryPoint.
    - state COMPROMISED: exibe página de aviso (não redireciona).
    - state REVOKED: 410 Gone.
    - state DRAFT/TESTED: 404 (não é público).
    """

    def get(self, request, entry_point_id):
        try:
            ep = EntryPoint.objects.select_related('organization', 'scope_store').get(
                pk=entry_point_id
            )
        except EntryPoint.DoesNotExist:
            raise Http404('EntryPoint não encontrado')

        if ep.state == EntryPoint.STATE_REVOKED:
            from django.http import HttpResponse
            return HttpResponse(
                'Este ponto de entrada foi revogado.',
                status=410,
                content_type='text/plain; charset=utf-8',
            )

        if ep.state == EntryPoint.STATE_COMPROMISED:
            return render(request, 'recruitment/entry_point_compromised.html', {
                'entry_point': ep,
            }, status=409)

        if ep.state != EntryPoint.STATE_ACTIVE:
            raise Http404('EntryPoint não está ativo')

        # Guarda contexto na sessão para o próximo passo (signup / feed).
        request.session['ep_id'] = str(ep.id)
        request.session['ep_mode'] = ep.mode
        request.session['ep_kind'] = ep.kind
        request.session['ep_purpose'] = ep.purpose
        request.session['ep_audience'] = ep.audience
        request.session['ep_audience_role'] = ep.audience_role
        if ep.program_id:
            request.session['program_id'] = str(ep.program_id)
        if ep.scope_store_id:
            request.session['ep_store_id'] = ep.scope_store_id

        # Compatibilidade com pontos antigos que apontavam para uma aplicação
        # externa. QRs MatchCo novos usam o roteador interno abaixo; destinos
        # externos continuam sendo respeitados sem quebrar integrações legadas.
        canonical = urlparse(ep.canonical_destination_url or '')
        if canonical.netloc and canonical.netloc != request.get_host():
            return redirect(ep.canonical_destination_url)

        if ep.program_id and (
            ep.purpose != EntryPoint.PURPOSE_RECRUITMENT
            or ep.program.kind != Program.KIND_RECRUITMENT
        ):
            return redirect('recruitment_public:program_entry', entry_point_id=ep.pk)
        return redirect('recruitment_public:candidato_signup')


class EntryPointChoiceView(View):
    """Entry point for the single Match journey."""
    template_name = 'recruitment/match/entry_point_choice.html'

    def get(self, request, entry_point_id):
        ep = get_object_or_404(
            EntryPoint.objects.select_related('organization', 'scope_store'),
            pk=entry_point_id,
            state=EntryPoint.STATE_ACTIVE,
        )
        request.session['ep_id'] = str(ep.id)
        request.session['ep_mode'] = ep.mode
        request.session['ep_kind'] = ep.kind
        request.session['ep_purpose'] = ep.purpose
        request.session['ep_audience'] = ep.audience
        request.session['ep_audience_role'] = ep.audience_role
        if ep.program_id:
            request.session['program_id'] = str(ep.program_id)
        if ep.scope_store_id:
            request.session['ep_store_id'] = ep.scope_store_id
        return redirect('recruitment_public:candidato_signup')


class CandidateRelationNegotiationView(View):
    """Permite à pessoa negociar somente critérios autorizados pela necessidade."""

    def post(self, request, relation_id):
        from .services import request_negotiation
        candidate_id = request.session.get('matchco_profile_id') or request.session.get('recruitment_last_candidate_id')
        relation = get_object_or_404(
            Relation.objects.select_related('opportunity'),
            pk=relation_id,
            candidate_id=candidate_id,
        )
        fields = request.POST.getlist('fields')
        proposal = {field: request.POST.get(field, '').strip() for field in fields}
        try:
            request_negotiation(
                relation=relation,
                fields=fields,
                proposal=proposal,
                actor_type='candidate',
            )
            messages.success(request, gettext_lazy('Sua proposta foi enviada para avaliação.'))
        except (RelationStateError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect('recruitment_public:candidato_matches')


# ---------------------------------------------------------------------------
# Porta Match — Fase 5: EmployerInterestView + ContactChannel endpoints
# ---------------------------------------------------------------------------

class EmployerOpportunityInterestListView(LoginRequiredMixin, View):
    """Lista pessoas interessadas em uma necessidade Match (AA-6)."""
    template_name = 'recruitment/match/employer_interest_list.html'

    def get(self, request, opportunity_id):
        from .projections import employer_interest_view
        from .services import _resolve_employer_actor

        opp = get_object_or_404(
            Position.objects.select_related('business_unit', 'organization'),
            pk=opportunity_id,
        )
        console_staff = request.path.startswith('/console/') and request.user.is_staff
        active_org_id = getattr(request, 'active_organization_id', None) or request.session.get('active_organization_id')
        same_selected_org = active_org_id and str(getattr(opp.organization, 'legacy_id', '')) == str(active_org_id)
        console_all_orgs = console_staff and request.user.is_superuser and request.session.get('selected_organization_id') == '__all__'
        if not (console_staff and (same_selected_org or console_all_orgs)):
            try:
                _resolve_employer_actor(
                    request.user, opp, AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW,
                )
            except AuthorityError:
                return HttpResponseForbidden('Sem escopo AA-6 para esta Opportunity')

        eligible_states = (
            Relation.STATE_EMPLOYER_INTEREST_VIEW,
            Relation.STATE_EMPLOYER_INTERESTED,
            Relation.STATE_MATCHED,
            Relation.STATE_CONTACT_ENABLED,
            Relation.STATE_RESPONSE_CREATED,
        )
        relations = Relation.objects.filter(
            opportunity=opp, state__in=eligible_states,
        ).select_related('candidate').order_by('-person_interested_at')
        cards = []
        for relation in relations:
            card = employer_interest_view(relation)
            if card:
                card['relation_state'] = relation.state
                cards.append(card)

        from .services import eligible_candidate_count_for_position
        eligible_count = eligible_candidate_count_for_position(position=opp)
        return render(request, self.template_name, {
            'opportunity': opp,
            'cards': cards,
            'eligible_count': eligible_count,
        })


def _candidate_is_eligible(candidate, opportunity):
    from .services import candidate_is_eligible_for_position
    return candidate_is_eligible_for_position(candidate=candidate, position=opportunity)
class EmployerRelationDetailView(LoginRequiredMixin, View):
    """Detalhe de uma Relation do lado empregador (após MATCH ou contato)."""
    template_name = 'recruitment/match/employer_relation_detail.html'

    def get(self, request, relation_id):
        from .projections import contact_view, employer_interest_view
        from .services import _resolve_employer_actor

        rel = get_object_or_404(
            Relation.objects.select_related('opportunity', 'opportunity__business_unit', 'candidate'),
            pk=relation_id,
        )
        try:
            _resolve_employer_actor(
                request.user, rel.opportunity,
                AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW,
            )
        except AuthorityError:
            return HttpResponseForbidden('Sem escopo AA-6')

        # CEPs são referência territorial e ficam disponíveis apenas para o
        # administrador da plataforma; nunca entram na projeção da loja.
        admin_geo = None
        if request.user.is_superuser or request.user.is_staff:
            from .geo import distance_candidate_to_store
            store = rel.opportunity.business_unit
            distance_km = distance_candidate_to_store(rel.candidate, store) if store else None
            admin_geo = {
                'candidate_cep': rel.candidate.cep or 'não informado',
                'store_cep': getattr(store, 'postal_code', '') or 'não informado',
                'distance_km': f'{distance_km:.1f} km em linha aproximada' if distance_km is not None else 'aguardando coordenadas',
            }

        return render(request, self.template_name, {
            'relation': rel,
            'view': employer_interest_view(rel),
            'contact': contact_view(rel),
            'admin_geo': admin_geo,
            'negotiable_fields': [
                (field, label) for field, label in (
                    ('period', 'Período'), ('start_date', 'Data de início'),
                    ('work_format', 'Formato'), ('learn', 'Aprender a atividade'),
                ) if field in (rel.opportunity.negotiable_fields or [])
            ],
            'rc_choices': [
                ('RC-01', 'Seguirei com esta pessoa'),
                ('RC-02', 'Seguirei com outra pessoa'),
                ('RC-03', 'Adiei ou cancelei a necessidade'),
                ('RC-04', 'Mudou o perfil que preciso'),
                ('RC-05', 'Outro motivo (nota obrigatória)'),
            ],
        })


class EmployerRelationContactView(LoginRequiredMixin, View):
    """Retorna ContactChannel para o empregador (AA-8, só se CONTACT_ENABLED)."""

    def get(self, request, relation_id):
        from .projections import contact_view
        from .services import _resolve_employer_actor

        rel = get_object_or_404(
            Relation.objects.select_related('candidate', 'opportunity'),
            pk=relation_id,
        )
        try:
            _resolve_employer_actor(
                request.user, rel.opportunity,
                AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
            )
        except AuthorityError:
            return HttpResponseForbidden('Sem escopo AA-8 para esta Opportunity')

        view = contact_view(rel)
        if view is None:
            return HttpResponseForbidden(
                'Contato não liberado — Relation ainda não atingiu CONTACT_ENABLED'
            )
        return JsonResponse(view)


class EmployerRelationInterestView(LoginRequiredMixin, View):
    """A loja confirma interesse; o candidato já abriu a relação."""

    def post(self, request, relation_id):
        from .services import employer_interested
        relation = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        try:
            employer_interested(relation=relation, actor=request.user)
            messages.success(request, gettext_lazy('Interesse registrado. Libere o contato para iniciar a conversa.'))
        except (AuthorityError, RelationStateError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect('recruitment:employer_relation_detail', relation_id=relation.pk)


class EmployerRelationDeclineView(LoginRequiredMixin, View):
    """A loja encerra a relação sem expor dados do candidato."""

    def post(self, request, relation_id):
        from .services import employer_declined
        relation = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        try:
            employer_declined(
                relation=relation,
                actor=request.user,
                reason=request.POST.get('reason', '').strip(),
            )
            messages.success(request, gettext_lazy('Interesse encerrado.'))
        except (AuthorityError, RelationStateError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect('recruitment:employer_opportunity_interest', opportunity_id=relation.opportunity_id)


class EmployerRelationEnableContactView(LoginRequiredMixin, View):
    """Libera o canal de contato apenas depois do Match e da autorização AA-8."""

    def post(self, request, relation_id):
        from .services import enable_contact
        relation = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        try:
            enable_contact(relation=relation, actor=request.user)
            messages.success(request, gettext_lazy('Canal de contato liberado.'))
        except (AuthorityError, RelationStateError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect('recruitment:employer_relation_detail', relation_id=relation.pk)


class EmployerRelationNegotiationView(LoginRequiredMixin, View):
    """Registra proposta somente para critérios marcados como negociáveis."""

    def post(self, request, relation_id):
        from .services import request_negotiation
        relation = get_object_or_404(Relation.objects.select_related('opportunity'), pk=relation_id)
        fields = request.POST.getlist('fields')
        proposal = {field: request.POST.get(field, '').strip() for field in fields}
        try:
            request_negotiation(
                relation=relation,
                fields=fields,
                proposal=proposal,
                actor_type='employer',
            )
            messages.success(request, gettext_lazy('Proposta registrada nos critérios negociáveis.'))
        except (AuthorityError, RelationStateError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect('recruitment:employer_relation_detail', relation_id=relation.pk)


# ---------------------------------------------------------------------------
# Fase 6 — LGPD: páginas públicas de privacidade, direitos, processadores
# ---------------------------------------------------------------------------

class PrivacyPolicyView(TemplateView):
    template_name = 'recruitment/privacy/policy.html'

    def get_context_data(self, **kwargs):
        from django.conf import settings as _s
        ctx = super().get_context_data(**kwargs)
        ctx['dpo_email'] = getattr(_s, 'MATCHCO_DPO_EMAIL', 'dpo@matchco.example')
        ctx['dpo_name'] = getattr(_s, 'MATCHCO_DPO_NAME', 'Encarregado de Dados')
        ctx['controller'] = getattr(_s, 'MATCHCO_CONTROLLER_NAME', 'MatchCo')
        return ctx


class PrivacyRightsView(TemplateView):
    template_name = 'recruitment/privacy/rights.html'

    def get_context_data(self, **kwargs):
        from django.conf import settings as _s
        ctx = super().get_context_data(**kwargs)
        ctx['rights_email'] = getattr(_s, 'MATCHCO_RIGHTS_EMAIL', 'direitos@matchco.example')
        ctx['dpo_email'] = getattr(_s, 'MATCHCO_DPO_EMAIL', 'dpo@matchco.example')
        return ctx


class OpsLedgerView(LoginRequiredMixin, View):
    """Dashboard ops do Ledger com filtros. Restrito a superuser."""
    template_name = 'recruitment/match/ops_ledger.html'

    def get(self, request):
        from .models import Ledger
        if not request.user.is_superuser:
            return HttpResponseForbidden('Restrito a operações MatchCo')

        qs = Ledger.objects.all().select_related('actor').order_by('-occurred_at')
        event_type = request.GET.get('type', '')
        actor_type = request.GET.get('actor_type', '')
        if event_type:
            qs = qs.filter(event_type=event_type)
        if actor_type:
            qs = qs.filter(actor_type=actor_type)
        events = list(qs[:200])

        distinct_types = list(
            Ledger.objects.values_list('event_type', flat=True).distinct().order_by('event_type')
        )
        return render(request, self.template_name, {
            'events': events,
            'distinct_types': distinct_types,
            'event_type': event_type,
            'actor_type': actor_type,
        })


class OpsMetricsView(LoginRequiredMixin, View):
    """Dashboard de métricas (D1). Scope por organização do EmployerActor."""
    template_name = 'recruitment/match/ops_metrics.html'

    def get(self, request):
        from .metrics import dashboard
        actor = request.user.employer_actor_profiles.select_related('organization').first()
        if actor is None and not request.user.is_superuser:
            return HttpResponseForbidden('Sem organização')
        org = actor.organization if actor else None
        days = int(request.GET.get('days', 30))
        data = dashboard(organization=org, days=days)
        return render(request, self.template_name, {'data': data, 'org': org})


class ProgramInviteListCreateView(LoginRequiredMixin, View):
    """Emite convites privados para participantes de um Programa."""
    template_name = 'recruitment/match/program_invites.html'

    def get(self, request):
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização vinculada')
        return render(request, self.template_name, {
            'programs': Program.objects.filter(organization=org, status=Program.STATUS_ACTIVE),
            'invites': ProgramInvite.objects.filter(program__organization=org).select_related('program')[:100],
            'role_choices': ProgramMembership.ROLE_CHOICES,
        })

    def post(self, request):
        import secrets
        from datetime import timedelta
        from django.conf import settings
        from django.core.mail import send_mail

        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização vinculada')
        program = get_object_or_404(
            Program, pk=request.POST.get('program_id'), organization=org,
            status=Program.STATUS_ACTIVE,
        )
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, gettext_lazy('Informe o e-mail do participante.'))
            return redirect('recruitment:program_invites')
        invite = ProgramInvite.objects.create(
            program=program,
            email=email,
            role=request.POST.get('role', ProgramMembership.ROLE_PARTICIPANT),
            token=secrets.token_urlsafe(48),
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )
        accept_url = request.build_absolute_uri(
            reverse('recruitment_public:program_invite_accept', args=[invite.token]),
        )
        send_mail(
            subject=f'Convite MatchCo — {program.name}',
            message=(f'Você foi convidado(a) para o programa {program.name}.\n\n'
                     f'Acesse: {accept_url}\n\nLink válido por 7 dias.'),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@matchco.example'),
            recipient_list=[email], fail_silently=True,
        )
        messages.success(request, f'Convite criado para {email}.')
        return redirect('recruitment:program_invites')


class ProgramInviteAcceptView(View):
    """Aceite público: posse do link + solicitação; acesso exige aprovação."""
    template_name = 'recruitment/match/program_invite_accept.html'

    def get_invite(self, token):
        return ProgramInvite.objects.select_related('program').filter(token=token).first()

    def get(self, request, token):
        invite = self.get_invite(token)
        if invite is None or not invite.is_valid():
            return render(request, self.template_name, {'error': 'Convite inválido, expirado ou revogado.'})
        return render(request, self.template_name, {'invite': invite})

    def post(self, request, token):
        from django.contrib.auth import get_user_model
        invite = self.get_invite(token)
        if invite is None or not invite.is_valid():
            return render(request, self.template_name, {'error': 'Convite inválido, expirado ou revogado.'})
        password = request.POST.get('password', '')
        if len(password) < 8:
            return render(request, self.template_name, {'invite': invite, 'error': 'A senha precisa ter ao menos 8 caracteres.'})
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=invite.email,
            defaults={'email': invite.email, 'is_active': True},
        )
        user.email = invite.email
        user.set_password(password)
        user.save(update_fields=['email', 'password'])
        access_request = create_controlled_access_request(
            organization=invite.program.organization,
            request_type='program',
            email=invite.email,
            user=user,
            program=invite.program,
            invite=invite,
            role=invite.role,
            requested_by=user,
            state='pending_approval',
        )
        invite.state = ProgramInvite.STATE_PENDING_APPROVAL
        invite.accepted_at = timezone.now()
        invite.save(update_fields=['state', 'accepted_at'])
        return render(request, 'recruitment/match/program_invite_pending.html', {
            'invite': invite,
            'access_request': access_request,
        })


class ProgramListCreateView(LoginRequiredMixin, View):
    """Lista e cria programas MatchCo para a organização ativa."""
    template_name = 'recruitment/match/program_list.html'

    def get(self, request):
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização vinculada')
        return render(request, self.template_name, {
            'actor': actor, 'org': org,
            'programs': Program.objects.filter(organization=org).prefetch_related('resources'),
            'kind_choices': Program.KIND_CHOICES,
            'resource_choices': ProgramResource.RESOURCE_CHOICES,
            'access_choices': Program.ACCESS_CHOICES,
        })

    def post(self, request):
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização vinculada')
        if request.POST.get('action') == 'add_resource':
            program = get_object_or_404(
                Program, pk=request.POST.get('program_id'), organization=org,
            )
            title = request.POST.get('resource_title', '').strip()
            url = request.POST.get('resource_url', '').strip()
            if not title or not url:
                messages.error(request, gettext_lazy('Informe o título e a URL do recurso.'))
                return redirect('recruitment:program_list')
            ProgramResource.objects.create(
                program=program,
                resource_type=request.POST.get('resource_type', ProgramResource.COURSE),
                title=title,
                url=url,
                external_id=request.POST.get('resource_external_id', '').strip(),
                description=request.POST.get('resource_description', '').strip(),
                required=request.POST.get('resource_required') == 'on',
            )
            messages.success(request, gettext_lazy('Recurso ligado ao programa.'))
            return redirect('recruitment:program_list')
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, gettext_lazy('Informe o nome do programa.'))
            return redirect('recruitment:program_list')
        Program.objects.create(
            organization=org,
            name=name,
            kind=request.POST.get('kind', Program.KIND_TRAINING),
            description=request.POST.get('description', '').strip(),
            sponsor_name=request.POST.get('sponsor_name', '').strip(),
            participant_free=request.POST.get('participant_free') == 'on',
            access_level=request.POST.get('access_level', Program.ACCESS_PUBLIC),
            status=Program.STATUS_ACTIVE if request.POST.get('activate') == 'on' else Program.STATUS_DRAFT,
            created_by=request.user,
        )
        messages.success(request, gettext_lazy('Programa criado. Agora associe um QR a ele.'))
        return redirect('recruitment:program_list')


class EntryPointListView(LoginRequiredMixin, View):
    """Lista EntryPoints do operador (A5)."""
    template_name = 'recruitment/match/entry_point_list.html'

    def get(self, request):
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização vinculada')
        eps = EntryPoint.objects.filter(
            organization=org,
        ).select_related('scope_store').order_by('-created_at')
        if actor and actor.business_unit_id and not request.user.is_superuser:
            eps = eps.filter(scope_store_id=actor.business_unit_id)
        return render(request, self.template_name, {
            'entry_points': eps, 'actor': actor, 'org': org,
        })


class EntryPointCreateView(LoginRequiredMixin, View):
    """Cria EntryPoint em DRAFT (A5)."""
    template_name = 'recruitment/match/entry_point_form.html'

    def get(self, request):
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        from .models import BusinessUnit
        stores = BusinessUnit.objects.filter(organization=org, active=True)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            stores = stores.filter(pk=actor.business_unit_id)
        return render(request, self.template_name, {
            'actor': actor, 'org': org,
            'stores': stores,
            'kind_choices': EntryPoint.KIND_CHOICES,
            'mode_choices': [(EntryPoint.MODE_MATCH, 'Match · alto giro, sem currículo')],
            'purpose_choices': EntryPoint.PURPOSE_CHOICES,
            'audience_choices': EntryPoint.AUDIENCE_CHOICES,
            'audience_role_choices': EntryPoint.AUDIENCE_ROLE_CHOICES,
            'experience_choices': EntryPoint.EXPERIENCE_CHOICES,
            'programs': Program.objects.filter(organization=org, status=Program.STATUS_ACTIVE),
        })

    def post(self, request):
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        from .models import BusinessUnit

        store = None
        if request.POST.get('scope_store_id'):
            store = get_object_or_404(BusinessUnit, pk=request.POST['scope_store_id'],
                                      organization=org)
            if actor and actor.business_unit_id and not request.user.is_superuser and actor.business_unit_id != store.pk:
                return HttpResponseForbidden('Unidade fora do seu escopo.')

        accent_color = request.POST.get('accent_color', '').strip()
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', accent_color):
            accent_color = '#f97316'
        experience_template = request.POST.get('experience_template', EntryPoint.EXPERIENCE_GENERIC)
        if experience_template not in dict(EntryPoint.EXPERIENCE_CHOICES):
            experience_template = EntryPoint.EXPERIENCE_GENERIC

        shopping_scope = ''
        if store and store.legacy_id:
            from configuration.models import BusinessUnit as ConfigBusinessUnit
            canonical_unit = ConfigBusinessUnit.objects.filter(pk=store.legacy_id).only('shopping_name').first()
            if canonical_unit and canonical_unit.shopping_name:
                shopping_scope = slugify(canonical_unit.shopping_name)[:64]

        ep = EntryPoint.objects.create(
            organization=org,
            kind=request.POST.get('kind', EntryPoint.KIND_STORE),
            scope_store=store,
            scope_shopping_id=shopping_scope,
            scope_network_id=org.slug,
            geo_lat=store.latitude if store else None,
            geo_lng=store.longitude if store else None,
            geo_radius_m=getattr(settings, 'MATCHCO_DEFAULT_RADIUS_M', 5000),
            mode=EntryPoint.MODE_MATCH,
            experience_template=experience_template,
            brand_name=request.POST.get('brand_name', '').strip(),
            brand_logo_url=request.POST.get('brand_logo_url', '').strip(),
            headline=request.POST.get('headline', '').strip(),
            subheadline=request.POST.get('subheadline', '').strip(),
            accent_color=accent_color,
            purpose=request.POST.get('purpose', EntryPoint.PURPOSE_RECRUITMENT),
            audience=request.POST.get('audience', EntryPoint.AUDIENCE_ALL),
            audience_role=request.POST.get('audience_role', EntryPoint.AUDIENCE_ROLE_CANDIDATE),
            program=Program.objects.filter(
                pk=request.POST.get('program_id'), organization=org,
                status=Program.STATUS_ACTIVE,
            ).first() if request.POST.get('program_id') else None,
            program_name=request.POST.get('program_name', '').strip(),
            campaign_name=request.POST.get('campaign_name', '').strip(),
            channel_name=request.POST.get('channel_name', '').strip(),
            participant_free=request.POST.get('participant_free') == 'on',
            label=request.POST.get('label', ''),
            canonical_destination_url='https://placeholder.invalid/matchco/entry/',
            managed_by=request.user,
        )
        ep.canonical_destination_url = request.build_absolute_uri(
            reverse('recruitment_public:entry_point_resolve', args=[str(ep.pk)]),
        )
        ep.save(update_fields=['canonical_destination_url', 'updated_at'])
        messages.success(request, f'EntryPoint criado em DRAFT ({ep.id}). Teste a ativação antes de usar.')
        return redirect('recruitment:entry_point_detail', entry_point_id=ep.pk)


class EntryPointDetailView(LoginRequiredMixin, View):
    """Detalhe do EntryPoint com ações PIAG (A5)."""
    template_name = 'recruitment/match/entry_point_detail.html'

    def get(self, request, entry_point_id):
        actor, org = _resolve_console_org(request)
        ep = get_object_or_404(EntryPoint, pk=entry_point_id)
        if org is None or ep.organization_id != org.pk:
            if not request.user.is_superuser:
                return HttpResponseForbidden('Sem acesso a este EntryPoint')
        if actor and actor.business_unit_id and not request.user.is_superuser and ep.scope_store_id != actor.business_unit_id:
            return HttpResponseForbidden('Unidade fora do seu escopo.')
        resolve_url = request.build_absolute_uri(
            reverse('recruitment_public:entry_point_resolve', args=[str(ep.pk)]),
        )
        return render(request, self.template_name, {
            'ep': ep,
            'resolve_url': resolve_url,
            'qr_b64': _qr_png_b64(resolve_url),
            'qr_image_url': reverse('recruitment_public:entry_point_qr_image', args=[str(ep.pk)]),
        })

    def post(self, request, entry_point_id):
        from .services import ledger_record
        actor, org = _resolve_console_org(request)
        ep = get_object_or_404(EntryPoint, pk=entry_point_id)
        if org is None or (ep.organization_id != org.pk and not request.user.is_superuser):
            return HttpResponseForbidden()
        if actor and actor.business_unit_id and not request.user.is_superuser and ep.scope_store_id != actor.business_unit_id:
            return HttpResponseForbidden('Unidade fora do seu escopo.')

        action = request.POST.get('action')
        if action == 'test_activate':
            ep.activation_tested_at = timezone.now()
            ep.state = EntryPoint.STATE_TESTED
            ep.save()
        elif action == 'activate':
            if ep.can_activate():
                ep.state = EntryPoint.STATE_ACTIVE
                ep.save()
                ledger_record('POINT_ACTIVATED', actor=request.user, actor_type='ops', entry_point=ep)
            else:
                messages.error(request, gettext_lazy('PIAG não passa: precisa de HTTPS + teste de ativação.'))
        elif action == 'compromise':
            ep.state = EntryPoint.STATE_COMPROMISED
            ep.save()
            ledger_record('POINT_COMPROMISED', actor=request.user, actor_type='ops', entry_point=ep)
        elif action == 'revoke':
            ep.state = EntryPoint.STATE_REVOKED
            ep.save()
            ledger_record('POINT_REVOKED', actor=request.user, actor_type='ops', entry_point=ep)
        return redirect('recruitment:entry_point_detail', entry_point_id=ep.pk)


class EntryPointUpdateView(LoginRequiredMixin, View):
    """Edit an existing QR without changing its identity or canonical URL."""

    template_name = 'recruitment/match/entry_point_edit.html'

    def _get(self, request, entry_point_id):
        actor, org = _resolve_console_org(request)
        ep = get_object_or_404(EntryPoint, pk=entry_point_id)
        if org is None or ep.organization_id != org.pk:
            if not request.user.is_superuser:
                return None, None
        return ep, org

    def get(self, request, entry_point_id):
        ep, org = self._get(request, entry_point_id)
        if ep is None:
            return HttpResponseForbidden('Sem acesso a este EntryPoint')
        actor, _ = _resolve_console_org(request)
        if actor and actor.business_unit_id and not request.user.is_superuser and ep.scope_store_id != actor.business_unit_id:
            return HttpResponseForbidden('Unidade fora do seu escopo.')
        return render(request, self.template_name, {
            'form': EntryPointForm(instance=ep, organization=org),
            'ep': ep,
        })

    def post(self, request, entry_point_id):
        ep, org = self._get(request, entry_point_id)
        if ep is None:
            return HttpResponseForbidden('Sem acesso a este EntryPoint')
        actor, _ = _resolve_console_org(request)
        if actor and actor.business_unit_id and not request.user.is_superuser and ep.scope_store_id != actor.business_unit_id:
            return HttpResponseForbidden('Unidade fora do seu escopo.')
        form = EntryPointForm(request.POST, instance=ep, organization=org)
        if form.is_valid():
            form.save()
            messages.success(request, gettext_lazy('Configuração pública do QR atualizada.'))
            return redirect('recruitment:entry_point_detail', entry_point_id=ep.pk)
        return render(request, self.template_name, {'form': form, 'ep': ep})

class MatchcoOpportunityListView(LoginRequiredMixin, View):
    """Lista Opportunities Porta Match do operador com contadores de interesse."""
    template_name = 'recruitment/match/opportunity_list.html'

    def get(self, request):
        from django.db.models import Count, Q
        actor, org = _resolve_console_org(request)
        if org is None or (actor is None and not request.user.is_superuser):
            return HttpResponseForbidden('Sem organização ativa')
        show_all = request.user.is_superuser and request.session.get('selected_organization_id') == '__all__'

        qs = Position.objects.filter(
            mode=Position.MODE_MATCH,
        ).select_related('business_unit', 'job_function')
        if not show_all:
            qs = qs.filter(organization=org)
            if actor and actor.business_unit_id and not request.user.is_superuser:
                qs = qs.filter(business_unit_id=actor.business_unit_id)

        state = request.GET.get('state', '')
        if state:
            qs = qs.filter(state=state)

        qs = qs.annotate(
            n_interested=Count('relations', filter=Q(
                relations__state__in=[
                    Relation.STATE_EMPLOYER_INTEREST_VIEW,
                    Relation.STATE_EMPLOYER_INTERESTED,
                ],
            )),
            n_matched=Count('relations', filter=Q(
                relations__state__in=[
                    Relation.STATE_MATCHED,
                    Relation.STATE_CONTACT_ENABLED,
                ],
            )),
            n_awaiting_response=Count('relations', filter=Q(
                relations__state=Relation.STATE_CONTACT_ENABLED,
            )),
        ).order_by('-created_at')

        return render(request, self.template_name, {
            'opportunities': list(qs[:100]),
            'state_filter': state,
            'state_choices': Position.STATE_CHOICES,
            'org': org,
        })


def _resolve_console_org(request):
    """Retorna (actor, organization). Superuser cai na org ativa do middleware
    ou na primeira organização MatchCo, mesmo sem EmployerActor.
    """
    from .domain_models import RecruitmentOrganization
    active_org_id = (
        getattr(request, 'active_organization_id', None)
        or request.session.get('active_organization_id')
        or getattr(request.user, '_active_organization_id', None)
    )
    if active_org_id == '__all__':
        active_org_id = None
    active_org = find_organization(pk=active_org_id) if active_org_id else None
    actors = request.user.employer_actor_profiles.filter(active=True).select_related('organization')

    # A organização selecionada no Console é a fronteira obrigatória. Nunca
    # caímos silenciosamente na primeira organização do usuário.
    if active_org is not None:
        actor = actors.filter(organization=active_org).first()
        if actor is not None or request.user.is_superuser:
            return actor, active_org
        return None, None

    actor = actors.first()
    if actor is not None:
        return actor, actor.organization
    if request.user.is_superuser:
        return None, RecruitmentOrganization.objects.filter(active=True).first()
    return None, None


class EmployerDeclareNeedView(LoginRequiredMixin, View):
    """Loja declara nova Opportunity com tag + critérios (A4).

    GET renderiza form. POST cria em STATE_STRUCTURED. Simulação de pool
    calculada e exibida no template.
    """
    template_name = 'recruitment/match/declare_need.html'

    def _tag_choices(self):
        return Position.TAG_CHOICES

    def get(self, request):
        from .models import BusinessUnit, JobFunction
        from .services import recruitment_defaults
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem escopo de empregador')
        stores = BusinessUnit.objects.filter(organization=org, active=True)
        fixed_store = bool(actor and actor.business_unit_id and not request.user.is_superuser)
        if fixed_store:
            stores = stores.filter(pk=actor.business_unit_id)
        for store in stores:
            store.sla_defaults = recruitment_defaults(organization=org, business_unit=store)
        functions = JobFunction.objects.filter(
            organization=org, active=True,
            canonical_mappings__active=True,
        ).filter(
            Q(canonical_mappings__business_unit__in=stores) |
            Q(canonical_mappings__business_unit__isnull=True)
        ).distinct()
        return render(request, self.template_name, {
            'actor': actor, 'org': org, 'stores': stores, 'functions': functions,
            'fixed_store': fixed_store,
            'tag_choices': self._tag_choices(),
            'format_choices': Position.FORMAT_CHOICES,
            'period_choices': Position.PERIOD_CHOICES,
            'experience_choices': Position.EXPERIENCE_CHOICES,
            'sla_defaults': recruitment_defaults(organization=org),
            'day_choices': [
                ('mon', 'Segunda'), ('tue', 'Terça'), ('wed', 'Quarta'),
                ('thu', 'Quinta'), ('fri', 'Sexta'), ('sat', 'Sábado'),
                ('sun', 'Domingo'),
            ],
        })

    def post(self, request):
        from .models import BusinessUnit, JobFunction, OpportunityCriterion, CanonicalFunctionMapping
        from .services import can_declare_new_opportunity, ledger_record, recruitment_defaults, open_invitation_round

        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem escopo de empregador')

        if not can_declare_new_opportunity(organization=org):
            messages.error(request, gettext_lazy('Há Relations MATCHED sem resposta há mais que o SLA. Responda antes de declarar nova necessidade.'))
            return redirect('recruitment:employer_declare_need')

        store_qs = BusinessUnit.objects.filter(pk=request.POST['store_id'], organization=org)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            store_qs = store_qs.filter(pk=actor.business_unit_id)
        store = get_object_or_404(store_qs)
        defaults = recruitment_defaults(organization=org, business_unit=store)
        func = get_object_or_404(JobFunction, pk=request.POST['function_id'], organization=org)
        if not CanonicalFunctionMapping.objects.filter(
            organization=org, job_function=func, active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).exists():
            messages.error(request, gettext_lazy('Esta função da loja ainda não foi mapeada para uma função canônica do cadastro do candidato.'))
            return redirect('recruitment:employer_declare_need')
        mapping = CanonicalFunctionMapping.objects.filter(
            pk=request.POST.get('mapping_id'), organization=org, job_function=func, active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).first() or CanonicalFunctionMapping.objects.filter(
            organization=org, job_function=func, active=True,
        ).filter(Q(business_unit=store) | Q(business_unit__isnull=True)).order_by('business_unit_id', 'pk').first()
        required_days = request.POST.getlist('required_days')
        required_period = request.POST.get('required_period', Position.PERIOD_ANY)
        requested_slots = max(1, min(999, int(request.POST.get('requested_slots') or 1)))
        invite_batch_size = max(1, min(999, int(request.POST.get('invite_batch_size') or defaults['invite_batch_size'])))
        candidate_response_hours = max(1, min(720, int(request.POST.get('candidate_response_hours') or defaults['candidate_response_hours'])))
        employer_decision_hours = max(1, min(720, int(request.POST.get('employer_decision_hours') or defaults['employer_decision_hours'])))

        opp = Position.objects.create(
            organization=org,
            business_unit=store,
            job_function=func,
            title=request.POST.get('title', func.name),
            description=request.POST.get('description', '').strip() or (mapping.job_description if mapping else ''),
            requirements='\n'.join(mapping.requirements or []) if mapping else '',
            benefits=mapping.benefits or [] if mapping else [],
            workplace=request.POST.get('workplace', ''),
            schedule=request.POST.get('schedule', ''),
            work_format=request.POST.get('work_format', Position.FORMAT_FIXO),
            starts_at=request.POST.get('starts_at') or None,
            required_days=required_days,
            required_period=required_period,
            required_experience=request.POST.get('required_experience', Position.EXPERIENCE_ANY),
            required_experience_contexts=request.POST.getlist('required_experience_contexts'),
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

        # Critérios REQUIRED / DESIRABLE / CAN_LEARN em linhas separadas pelo form.
        for weight_key in ('required', 'desirable', 'can_learn'):
            labels = request.POST.getlist(f'criteria_{weight_key}')
            weight = {
                'required': OpportunityCriterion.WEIGHT_REQUIRED,
                'desirable': OpportunityCriterion.WEIGHT_DESIRABLE,
                'can_learn': OpportunityCriterion.WEIGHT_CAN_LEARN,
            }[weight_key]
            for i, label in enumerate([l.strip() for l in labels if l.strip()]):
                OpportunityCriterion.objects.create(
                    opportunity=opp, label=label, weight=weight, order=i,
                )

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

        ledger_record(
            'OPPORTUNITY_STRUCTURED', actor=request.user, actor_type='employer_actor',
            authority_scope='AA-2', opportunity=opp,
            metadata={'title': opp.title, 'tag': opp.tag},
        )
        if opp.state == Position.STATE_ACTIVATED:
            ledger_record(
                'OPPORTUNITY_ACTIVATED', actor=request.user, actor_type='employer_actor',
                authority_scope='AA-3', opportunity=opp,
            )
            opp.state = Position.STATE_CIRCULATED
            opp.save(update_fields=['state', 'updated_at'])
            open_invitation_round(opportunity=opp)

        messages.success(request, f'Necessidade declarada (v{opp.version}, estado {opp.get_state_display()}).')
        return redirect('recruitment:employer_opportunity_interest', opportunity_id=opp.pk)


class StoreFunctionCatalogView(LoginRequiredMixin, View):
    """Console de administração do catálogo local → função canônica."""
    template_name = 'recruitment/match/store_function_catalog.html'

    def get(self, request, store_id):
        from .models import BusinessUnit, CanonicalFunctionMapping, CanonicalTerm, JobFunction
        from configuration.models import BusinessUnit as ConfigBusinessUnit
        actor, org = _resolve_console_org(request)
        store = get_object_or_404(BusinessUnit, pk=store_id, organization=org)
        config_store = ConfigBusinessUnit.objects.filter(pk=store.legacy_id).select_related('company').first()
        structure_functions = list(config_store.company.job_functions.filter(active=True).order_by('name')) if config_store else []
        structure_function_ids = {item.name: item.pk for item in structure_functions}
        if actor and actor.business_unit_id and not request.user.is_superuser and actor.business_unit_id != store.pk:
            return HttpResponseForbidden('Unidade fora do seu escopo.')
        mappings = CanonicalFunctionMapping.objects.filter(
            organization=org, business_unit=store, active=True,
        ).select_related('job_function', 'term').order_by('local_label', 'job_function__name')
        mapping_groups = {}
        for mapping in mappings:
            key = (mapping.local_label, mapping.job_function_id, mapping.job_function.name)
            group = mapping_groups.setdefault(key, {
                'id': mapping.pk, 'local_label': mapping.local_label,
                'job_function': mapping.job_function.name,
                'structure_function_id': mapping.job_function.legacy_id or structure_function_ids.get(mapping.job_function.name),
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
            'org': org, 'store': store, 'config_store': config_store,
            'structure_functions': structure_functions,
            'terms': CanonicalTerm.objects.filter(catalog__code='market-default', catalog__status='published', term_type=CanonicalTerm.TYPE_FUNCTION, active=True).order_by('label'),
            'mappings': mappings, 'mapping_groups': mapping_groups.values(), 'edit_group': edit_group,
            'salary_period_choices': Position.SALARY_PERIOD_CHOICES,
            'employment_type_choices': Position.EMPLOYMENT_TYPE_CHOICES,
            'payment_method_choices': Position.PAYMENT_METHOD_CHOICES,
        })

    def post(self, request, store_id):
        from .models import BusinessUnit, CanonicalFunctionMapping, CanonicalTerm, JobFunction
        from configuration.models import BusinessUnit as ConfigBusinessUnit
        from .integrations.organization import _sync_job_function
        actor, org = _resolve_console_org(request)
        store = get_object_or_404(BusinessUnit, pk=store_id, organization=org)
        config_store = ConfigBusinessUnit.objects.filter(pk=store.legacy_id).select_related('company').first()
        structure_function = (
            config_store.company.job_functions.filter(
                pk=request.POST.get('structure_function_id'), active=True,
            ).first()
            if config_store and request.POST.get('structure_function_id') else None
        )
        if structure_function is None:
            messages.error(request, gettext_lazy('Selecione um cargo ou função já cadastrado na estrutura da unidade.'))
            return redirect('recruitment:store_function_catalog', store_id=store.pk)
        if actor and actor.business_unit_id and not request.user.is_superuser and actor.business_unit_id != store.pk:
            return HttpResponseForbidden('Unidade fora do seu escopo.')
        terms = CanonicalTerm.objects.filter(
            pk__in=request.POST.getlist('term_ids'),
            term_type=CanonicalTerm.TYPE_FUNCTION, active=True,
        )
        if not terms.exists():
            messages.error(request, gettext_lazy('Selecione pelo menos uma função canônica do candidato.'))
            return redirect('recruitment:store_function_catalog', store_id=store.pk)

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
            return redirect('recruitment:store_function_catalog', store_id=store.pk)
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            messages.error(request, gettext_lazy('A faixa máxima não pode ser menor que a mínima.'))
            return redirect('recruitment:store_function_catalog', store_id=store.pk)
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
        # A função estrutural é a origem do cargo. O adapter mantém a
        # representação de recrutamento sincronizada e o de-para canônico
        # continua específico da unidade.
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
                defaults={'local_label': local_label, 'source': 'console_store_catalog', 'active': True, **profile_defaults},
            )
        return redirect('recruitment:store_function_catalog', store_id=store.pk)


class EmployerNeedSimulateView(LoginRequiredMixin, View):
    """GET simples — estima quantos Perfis se qualificam para uma tag+store."""

    def get(self, request):
        from .models import BusinessUnit, JobFunction, Position
        from .services import estimate_candidate_pool
        store_id = request.GET.get('store_id')
        if not store_id:
            return JsonResponse({'estimate': 0})
        actor, org = _resolve_console_org(request)
        if org is None or (actor is None and not request.user.is_superuser):
            return JsonResponse({'error': 'organization_scope_required'}, status=403)
        store_qs = BusinessUnit.objects.filter(pk=store_id, organization=org)
        if actor and actor.business_unit_id and not request.user.is_superuser:
            store_qs = store_qs.filter(pk=actor.business_unit_id)
        store = store_qs.first()
        if store is None:
            return JsonResponse({'estimate': 0})
        function = JobFunction.objects.filter(
            pk=request.GET.get('function_id'), organization=store.organization,
        ).first() if request.GET.get('function_id') else None
        return JsonResponse({'estimate': estimate_candidate_pool(
            organization=store.organization,
            business_unit=store,
            job_function=function,
            required_days=request.GET.getlist('required_days'),
            required_period=request.GET.get('required_period', Position.PERIOD_ANY),
            work_format=request.GET.get('work_format', ''),
            required_experience=request.GET.get('required_experience', Position.EXPERIENCE_ANY),
        )})


class MatchcoLandingView(TemplateView):
    """Landing institucional ampla da plataforma MatchCo."""
    template_name = 'recruitment/matchco_site/platform.html'


class MatchcoAccessView(TemplateView):
    """Directory of public MatchCo entry points, outside the console shell."""
    template_name = 'recruitment/match/access.html'


class MatchcoRoleChooserView(TemplateView):
    """Entrada geral MatchCo, sem assumir um setor ou organização."""
    template_name = 'recruitment/match/role_chooser.html'


class ShoppingDashboardView(LoginRequiredMixin, View):
    """Painel do sponsor Shopping — só agregados, sem pessoa nominal."""
    template_name = 'recruitment/match/shopping_dashboard.html'

    def get(self, request):
        from .metrics import dashboard
        actor, org = _resolve_console_org(request)
        if org is None:
            return HttpResponseForbidden('Sem organização')
        data = dashboard(organization=org, days=30)
        stores = org.stores.filter(active=True) if hasattr(org, 'stores') else []
        return render(request, self.template_name, {
            'data': data,
            'org': org,
            'stores': stores,
        })


class LojistaHomeView(LoginRequiredMixin, View):
    """Home do lojista pós-login — direciona ao painel do MatchCo."""

    def get(self, request):
        return redirect('recruitment:matchco_opportunity_list')


def _complete_matchco_signup(*, request, ep, data, identity):
    """Persist the QR signup only after the contact OTP was confirmed."""
    from .services import ledger_record, record_candidate_context
    from .models import CandidateCanonicalResponse, CanonicalCatalog, CanonicalTerm

    org = ep.organization
    email = data['email'].lower().strip()
    term_ids = data.get('what_function_terms') or []
    terms = list(CanonicalTerm.objects.filter(
        pk__in=term_ids,
        catalog__status=CanonicalCatalog.STATUS_PUBLISHED,
        term_type=CanonicalTerm.TYPE_FUNCTION,
        active=True,
    ).order_by('label'))
    if not terms:
        raise ValueError('Nenhuma função canônica publicada foi selecionada.')
    function_labels = [term.label for term in terms]
    program_id = request.session.get('program_id')
    program = Program.objects.filter(
        pk=program_id, status=Program.STATUS_ACTIVE,
    ).first() if program_id else None
    if program:
        ProgramMembership.objects.update_or_create(
            identity=identity,
            program=program,
            defaults={
                'active': True,
                'consented_at': timezone.now(),
                'source': 'matchco_signup',
            },
        )

    profile = CandidateProfile.objects.filter(
        organization=org, identity=identity,
    ).first()
    if profile is None:
        candidates = CandidateProfile.objects.filter(organization=org).filter(
            Q(email__iexact=email) | Q(phone=data['mobile'])
        )
        if candidates.count() > 1:
            raise IdentityConflict('Mais de um Perfil compatível foi encontrado')
        profile = candidates.first()
    if profile is None:
        profile = CandidateProfile.objects.create(
            organization=org, identity=identity,
            first_name=data['first_name'], last_name=data['last_name'],
            email=email, phone=data['mobile'],
            city=data['where_neighborhoods'],
            cep=re.sub(r'\D', '', data.get('cep', ''))[:8],
            experience_years=({'first_job': 0, 'some': 1, 'experienced': 3})[data['experience']],
            availability_days=data['when_days'],
            availability_period=data.get('when_period', ''),
            preferred_work_format=data.get('work_format', ''),
            available_from=data.get('can_start'),
            interest_categories=function_labels,
            interested_in=', '.join(function_labels),
            preferred_store=ep.scope_store,
            visibility_match=True,
        )
    else:
        changed = []
        if profile.identity_id != identity.pk:
            profile.identity = identity
            changed.append('identity')
        if not profile.email:
            profile.email = email
            changed.append('email')
        if not profile.phone:
            profile.phone = data['mobile']
            changed.append('phone')
        profile_updates = {
            'availability_days': data.get('when_days') or [],
            'availability_period': data.get('when_period', ''),
            'preferred_work_format': data.get('work_format', ''),
            'available_from': data.get('can_start'),
            'experience_years': {'first_job': 0, 'some': 1, 'experienced': 3}[data['experience']],
            'city': data.get('where_neighborhoods', ''),
            'cep': re.sub(r'\D', '', data.get('cep', ''))[:8],
        }
        for field, value in profile_updates.items():
            if value != getattr(profile, field):
                setattr(profile, field, value)
                changed.append(field)
        if changed:
            changed.append('updated_at')
            profile.save(update_fields=changed)

    record_candidate_context(
        candidate=profile,
        entry_point=ep,
        metadata={'via': 'matchco_signup', 'qr_id': str(ep.pk)},
    )

    # Texto continua amigável para a pessoa, mas a distribuição usa o termo
    # aprovado quando o catálogo ofereceu uma opção canônica.
    from .services import record_canonical_response
    response_scope = (
        CandidateCanonicalResponse.SCOPE_UNIT
        if ep.scope_store_id else CandidateCanonicalResponse.SCOPE_ORGANIZATION
    )
    for term in terms:
        record_canonical_response(
            candidate=profile,
            term=term,
            scope=response_scope,
            purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
            origin=CandidateCanonicalResponse.ORIGIN_QR,
            organization=org,
            business_unit=ep.scope_store,
            value={
                'interest_mode': data.get('interest_mode'),
                'experience': data.get('experience'),
                'experience_contexts': data.get('experience_contexts', []),
                'work_format': data.get('work_format'),
            },
            consented_at=timezone.now(),
            source_reference=f'entry_point:{ep.pk}',
        )

    for field, purpose in MatchcoSignupForm.CONSENT_MAP.items():
        if data.get(field):
            CandidateConsent.objects.create(
                identity=identity, organization=org, purpose=purpose,
                granted=True, policy_version='matchco-v1',
                source=f'entry_point:{ep.pk}', legal_basis=CandidateConsent.BASIS_CONSENT,
            )

    ledger_record(
        'PROFILE_CREATED', actor_type='candidate', candidate=profile,
        entry_point=ep, metadata={'via': 'matchco_signup'},
    )
    return profile


@method_decorator(_optional_ratelimit(key='ip', rate='10/h', method='POST', block=True), name='dispatch')
class OtpRequestView(View):
    """/entrar — pede número; envia OTP."""
    template_name = 'recruitment/match/otp_request.html'

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        from .services import request_otp, OtpError, OtpRateLimitError
        mobile = request.POST.get('mobile', '')
        email = request.POST.get('email', '').strip() or None
        try:
            otp, code = request_otp(
                mobile=mobile, email=email,
                ip_address=request.META.get('REMOTE_ADDR'),
                dev_capture=request.session.setdefault('_dev_otps', []) if settings.DEBUG else None,
            )
        except OtpRateLimitError as exc:
            return render(request, self.template_name, {'error': str(exc)})
        except OtpError as exc:
            return render(request, self.template_name, {'error': str(exc)})
        request.session['otp_mobile'] = otp.mobile
        request.session.modified = True
        return redirect('recruitment_public:candidato_entrar_codigo')


@method_decorator(_optional_ratelimit(key='ip', rate='20/h', method='POST', block=True), name='dispatch')
class OtpVerifyView(View):
    template_name = 'recruitment/match/otp_verify.html'

    def get(self, request):
        return render(request, self.template_name, {
            'mobile': request.session.get('otp_mobile', ''),
            'dev_hint': (request.session.get('_dev_otps') or [None])[-1] if settings.DEBUG else None,
        })

    def post(self, request):
        from .services import (
            verify_otp, OtpInvalidError, IdentityConflict,
            normalize_identity_phone, resolve_or_create_identity,
        )
        mobile = request.session.get('otp_mobile', '')
        code = request.POST.get('code', '').strip()
        try:
            verify_otp(mobile=mobile, code=code,
                       ip_address=request.META.get('REMOTE_ADDR'))
        except OtpInvalidError as exc:
            return render(request, self.template_name, {
                'mobile': mobile, 'error': str(exc),
                'dev_hint': (request.session.get('_dev_otps') or [None])[-1] if settings.DEBUG else None,
            })

        # A identidade pode ter um perfil em várias organizações. Quando o
        # login veio de um QR, priorizamos o perfil daquela organização;
        # sem contexto, o candidato poderá trocar o contexto no cabeçalho.
        profiles = CandidateProfile.objects.filter(
            phone__endswith=mobile[-10:],
        ).select_related('identity', 'organization').order_by('organization__name', 'id')
        entry_id = request.session.get('ep_id')
        if entry_id:
            entry = EntryPoint.objects.filter(pk=entry_id).first()
            if entry:
                candidate = profiles.filter(organization=entry.organization).first()
            else:
                candidate = profiles.first()
        else:
            candidate = profiles.first()

        # O OTP comprova a posse do telefone. Registramos essa evidência na
        # identidade global para que as próximas entradas possam reutilizá-la.
        identity = candidate.identity if candidate and candidate.identity_id else None
        try:
            identity = identity or resolve_or_create_identity(phone=mobile)
        except IdentityConflict:
            return render(request, self.template_name, {
                'mobile': mobile,
                'error': 'Este celular está associado a mais de uma identidade. Fale com o suporte para corrigir o cadastro.',
                'dev_hint': (request.session.get('_dev_otps') or [None])[-1] if settings.DEBUG else None,
            })
        identity.phone_normalized = normalize_identity_phone(mobile)
        identity.verified_at = timezone.now()
        identity.save(update_fields=['phone_normalized', 'verified_at', 'updated_at'])

        # Handle old fixed-form signup (pending_matchco_signup)
        pending = request.session.get('pending_matchco_signup')
        if pending:
            pending_ep = EntryPoint.objects.select_related(
                'organization', 'scope_store',
            ).filter(
                pk=pending.get('entry_point_id'), state=EntryPoint.STATE_ACTIVE,
            ).first()
            if pending_ep and normalize_identity_phone(pending.get('mobile')) == normalize_identity_phone(mobile):
                try:
                    identity = resolve_or_create_identity(
                        email=pending.get('email'), phone=mobile,
                    )
                    identity.verified_at = timezone.now()
                    identity.save(update_fields=['verified_at', 'updated_at'])
                    candidate = _complete_matchco_signup(
                        request=request, ep=pending_ep, data=pending, identity=identity,
                    )
                except IdentityConflict:
                    return render(request, self.template_name, {
                        'mobile': mobile,
                        'error': 'O e-mail e o celular estão associados a cadastros diferentes. Fale com o suporte.',
                        'dev_hint': (request.session.get('_dev_otps') or [None])[-1] if settings.DEBUG else None,
                    })
                request.session.pop('pending_matchco_signup', None)
                request.session['matchco_profile_id'] = candidate.pk
                request.session['matchco_identity_id'] = str(identity.pk)
                request.session.pop('_dev_otps', None)
                return redirect('recruitment_public:candidato_signup_done')

        # Handle new custom questionnaire signup (pending_custom_signup)
        pending_custom = request.session.get('pending_custom_signup')
        if pending_custom:
            from .models import CandidateSignupAnswer, StoreSignupConfiguration, QuestionnaireTemplate

            if normalize_identity_phone(pending_custom.get('mobile')) == normalize_identity_phone(mobile):
                try:
                    identity = resolve_or_create_identity(
                        email=pending_custom.get('email'), phone=mobile,
                    )
                    identity.verified_at = timezone.now()
                    identity.save(update_fields=['verified_at', 'updated_at'])

                    # Get or create candidate profile
                    candidate, _ = CandidateProfile.objects.get_or_create(
                        identity=identity,
                        defaults={
                            'organization_id': StoreSignupConfiguration.objects.filter(
                                store_id=pending_custom.get('store_id')
                            ).values_list('organization_id', flat=True).first(),
                        }
                    )

                    # Save questionnaire responses
                    questionnaire = QuestionnaireTemplate.objects.filter(
                        pk=pending_custom.get('questionnaire_id')
                    ).first()

                    if questionnaire:
                        CandidateSignupAnswer.objects.create(
                            candidate=candidate,
                            organization=questionnaire.organization,
                            business_unit_id=pending_custom.get('store_id'),
                            questionnaire_template=questionnaire,
                            responses=pending_custom.get('responses', {}),
                        )

                except IdentityConflict:
                    return render(request, self.template_name, {
                        'mobile': mobile,
                        'error': 'O e-mail e o celular estão associados a cadastros diferentes. Fale com o suporte.',
                        'dev_hint': (request.session.get('_dev_otps') or [None])[-1] if settings.DEBUG else None,
                    })

                request.session.pop('pending_custom_signup', None)
                request.session['matchco_profile_id'] = candidate.pk
                request.session['matchco_identity_id'] = str(identity.pk)
                request.session.pop('_dev_otps', None)
                return redirect('recruitment_public:candidato_signup_done')

        if candidate is None:
            return redirect('recruitment_public:candidato_signup')
        if candidate.identity_id != identity.pk:
            candidate.identity = identity
            candidate.save(update_fields=['identity', 'updated_at'])
        request.session['matchco_profile_id'] = candidate.pk
        request.session['matchco_identity_id'] = str(identity.pk)
        request.session.pop('_dev_otps', None)
        return redirect('recruitment_public:candidato_feed')


# --- QR Redesign: Phase 2-3 Views (Universal QR → Store-Customizable Signup) ---


class StoreChooserView(View):
    """Allows candidate to select a store before proceeding with signup.

    Used when QR code doesn't have scope_store pre-configured, or when
    one universal QR needs to route to multiple stores.
    """

    template_name = 'recruitment/match/store_chooser.html'

    def get(self, request):
        from .models import StoreSignupConfiguration

        # Check if store already selected in session
        if request.session.get('ep_store_id'):
            return redirect('recruitment_public:candidato_action_choose')

        # Get organization from entry point or session
        org_id = request.session.get('ep_organization_id')
        if not org_id:
            return HttpResponseBadRequest('Organização não identificada.')

        # Fetch active stores with signup configurations
        configs = StoreSignupConfiguration.objects.filter(
            organization_id=org_id,
            is_active=True,
        ).select_related('store', 'profile_questionnaire', 'job_questionnaire')

        return render(request, self.template_name, {
            'stores': [cfg.store for cfg in configs],
            'configs': {cfg.store_id: cfg for cfg in configs},
        })

    def post(self, request):
        store_id = request.POST.get('store_id')
        if not store_id:
            return HttpResponseBadRequest('Loja não selecionada.')

        request.session['ep_store_id'] = int(store_id)
        request.session.modified = True
        return redirect('recruitment_public:candidato_action_choose')


class ActionChooserView(View):
    """Allows candidate to choose action: create profile or apply to job.

    Shows available actions based on store's signup configuration.
    """

    template_name = 'recruitment/match/action_chooser.html'

    def get(self, request):
        from .models import StoreSignupConfiguration

        store_id = request.session.get('ep_store_id')
        if not store_id:
            return redirect('recruitment_public:candidato_store_choose')

        config = StoreSignupConfiguration.objects.filter(
            store_id=store_id, is_active=True
        ).select_related('profile_questionnaire', 'job_questionnaire').first()

        if not config:
            return HttpResponseNotFound('Configuração de loja não encontrada.')

        actions = []
        if config.profile_questionnaire_id:
            actions.append({
                'value': 'profile',
                'label': _('Criar Meu Perfil'),
                'description': _('Responda algumas perguntas para criar seu perfil no MatchCo.'),
            })
        if config.job_questionnaire_id:
            actions.append({
                'value': 'job',
                'label': _('Candidatar para Vaga'),
                'description': _('Responda perguntas específicas para candidatar a uma oportunidade.'),
            })

        # If only one action available, skip directly to signup
        if len(actions) == 1:
            request.session['signup_action'] = actions[0]['value']
            request.session.modified = True
            return redirect('recruitment_public:candidato_custom_signup')

        return render(request, self.template_name, {
            'actions': actions,
            'store_id': store_id,
        })

    def post(self, request):
        action = request.POST.get('action')
        if action not in ('profile', 'job'):
            return HttpResponseBadRequest('Ação inválida.')

        request.session['signup_action'] = action
        request.session.modified = True
        return redirect('recruitment_public:candidato_custom_signup')


class CustomSignupView(View):
    """Dynamic signup form based on store's questionnaire configuration.

    Replaces fixed MatchcoSignupView for QR-driven candidates.
    Form fields are determined by StoreSignupConfiguration questionnaire.
    """

    template_name = 'recruitment/match/custom_signup.html'

    def _get_config(self, request):
        from .models import StoreSignupConfiguration

        store_id = request.session.get('ep_store_id')
        if not store_id:
            return None, None

        config = StoreSignupConfiguration.objects.filter(
            store_id=store_id, is_active=True
        ).select_related('profile_questionnaire', 'job_questionnaire').first()

        return config, store_id

    def get(self, request):
        config, store_id = self._get_config(request)
        if not config:
            return redirect('recruitment_public:candidato_store_choose')

        action = request.session.get('signup_action', 'profile')
        if action == 'profile':
            questionnaire = config.profile_questionnaire
        else:
            questionnaire = config.job_questionnaire

        if not questionnaire:
            return HttpResponseNotFound('Questionário não configurado.')

        # Load questions (always fresh, never pre-filled)
        questions = questionnaire.questions.filter(active=True).order_by('order')

        return render(request, self.template_name, {
            'questionnaire': questionnaire,
            'questions': questions,
            'action': action,
            'store_id': store_id,
        })

    def post(self, request):
        from .services import request_otp, OtpError, OtpRateLimitError
        from .models import CandidateSignupAnswer

        config, store_id = self._get_config(request)
        if not config:
            return redirect('recruitment_public:candidato_store_choose')

        action = request.session.get('signup_action', 'profile')
        if action == 'profile':
            questionnaire = config.profile_questionnaire
        else:
            questionnaire = config.job_questionnaire

        if not questionnaire:
            return HttpResponseNotFound('Questionário não configurado.')

        questions = questionnaire.questions.filter(active=True)
        responses = {}
        errors = {}

        # Validate and collect responses
        for question in questions:
            value = request.POST.get(f'q_{question.id}')
            if question.required and not value:
                errors[question.id] = _('Este campo é obrigatório.')
            responses[question.id] = value

        if errors:
            return render(request, self.template_name, {
                'questionnaire': questionnaire,
                'questions': questions,
                'action': action,
                'store_id': store_id,
                'errors': errors,
                'responses': responses,
            })

        # Request OTP for phone verification (mobile from form)
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()

        if not mobile:
            errors['mobile'] = _('Telefone é obrigatório.')
            return render(request, self.template_name, {
                'questionnaire': questionnaire,
                'questions': questions,
                'action': action,
                'store_id': store_id,
                'errors': errors,
                'responses': responses,
            })

        try:
            otp, _ = request_otp(
                mobile=mobile,
                email=email,
                ip_address=request.META.get('REMOTE_ADDR'),
                dev_capture=request.session.setdefault('_dev_otps', []) if settings.DEBUG else None,
            )
        except (OtpError, OtpRateLimitError) as exc:
            errors['mobile'] = str(exc)
            return render(request, self.template_name, {
                'questionnaire': questionnaire,
                'questions': questions,
                'action': action,
                'store_id': store_id,
                'errors': errors,
                'responses': responses,
            })

        # Store pending signup data in session
        request.session['otp_mobile'] = otp.mobile
        request.session['pending_custom_signup'] = {
            'store_id': store_id,
            'action': action,
            'questionnaire_id': questionnaire.id,
            'mobile': mobile,
            'email': email.lower().strip(),
            'responses': responses,
        }
        request.session.modified = True
        return redirect('recruitment_public:candidato_entrar_codigo')


class MatchcoSignupView(View):
    """Signup Porta Match — Perfil de 6 campos + gate 18+ + consent granular."""

    template_name = 'recruitment/match/signup.html'

    def _entry_point(self, request):
        ep_id = request.session.get('ep_id') or request.GET.get('entry_point') or request.POST.get('entry_point')
        if not ep_id:
            return None
        ep = EntryPoint.objects.select_related('organization', 'scope_store').filter(
            pk=ep_id, state=EntryPoint.STATE_ACTIVE,
        ).first()
        if ep and request.GET.get('entry_point'):
            request.session['ep_id'] = str(ep.pk)
            request.session['ep_mode'] = ep.mode
            request.session['ep_kind'] = ep.kind
            request.session['ep_purpose'] = ep.purpose
            request.session['ep_audience'] = ep.audience
            request.session['ep_audience_role'] = ep.audience_role
            if ep.program_id:
                request.session['program_id'] = str(ep.program_id)
            if ep.scope_store_id:
                request.session['ep_store_id'] = ep.scope_store_id
        return ep

    def get(self, request):
        from .forms import MatchcoSignupForm
        form = MatchcoSignupForm()
        return render(request, self.template_name, self._ctx(request, form))

    def post(self, request):
        from .services import enforce_age_gate, AgeGateFailure, request_otp, OtpError, OtpRateLimitError

        form = MatchcoSignupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(request, form))

        # Gate de idade (RT-06: sem retenção do requerente reprovado).
        try:
            enforce_age_gate(form.cleaned_data['birth_date'])
        except AgeGateFailure as exc:
            form.add_error('birth_date', str(exc))
            return render(request, self.template_name, self._ctx(request, form))

        # Resolve a organização pelo QR ou pelo EntryPoint informado.
        ep = self._entry_point(request)
        if ep is None:
            form.add_error(None, gettext_lazy('Escolha uma porta de entrada ou escaneie o QR da organização antes de criar o perfil.'))
            return render(request, self.template_name, self._ctx(request, form))

        data = form.cleaned_data
        try:
            otp, _ = request_otp(
                mobile=data['mobile'], email=data['email'],
                ip_address=request.META.get('REMOTE_ADDR'),
                dev_capture=request.session.setdefault('_dev_otps', []) if settings.DEBUG else None,
            )
        except (OtpError, OtpRateLimitError) as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, self._ctx(request, form))

        # O perfil só é criado após a posse do telefone ser comprovada.
        request.session['otp_mobile'] = otp.mobile
        pending_fields = {
            'first_name', 'last_name', 'mobile', 'email',
            'where_neighborhoods', 'when_days', 'what_function_terms',
            'interest_mode', 'experience', 'experience_contexts',
            *form.CONSENT_MAP.keys(),
        }
        request.session['pending_matchco_signup'] = {
            key: (list(data[key]) if key in ('when_days', 'what_function_terms', 'experience_contexts') else data[key])
            for key in pending_fields if key in data
        }
        request.session['pending_matchco_signup']['entry_point_id'] = str(ep.pk)
        request.session['pending_matchco_signup']['email'] = data['email'].lower().strip()
        request.session.modified = True
        return redirect('recruitment_public:candidato_entrar_codigo')

    def _ctx(self, request, form):
        ep = self._entry_point(request)
        return {
            'form': form,
            'entry_point': ep,
            'entry_context': _entry_experience(ep),
            'identity_fields': [form['first_name'], form['last_name'], form['mobile'],
                                form['email'], form['birth_date']],
            'when_fields': [form['when_days'], form['when_period'], form['can_start']],
            'what_fields': [form['what_function_terms'], form['interest_mode'], form['experience'], form['experience_contexts'], form['work_format']],
            'consent_scope_fields': [form['consent_store'], form['consent_shopping'],
                                     form['consent_network'], form['consent_radius']],
        }


class MatchcoSignupDoneView(TemplateView):
    template_name = 'recruitment/match/signup_done.html'


class CandidateFeedView(View):
    """GET /candidato/oportunidades/ — feed territorial do candidato (HTML).

    Sem busca, sem ranking. Ordenação efêmera por proximidade + tag.
    Contexto do EntryPoint e do profile vem da sessão.
    """
    template_name = 'recruitment/match/feed.html'

    def _get_profile(self, request):
        pid = request.session.get('matchco_profile_id')
        if pid:
            return CandidateProfile.objects.filter(pk=pid).first()
        # Fallback via user logado (piloto).
        if request.user.is_authenticated and getattr(request.user, 'email', None):
            return CandidateProfile.objects.filter(email=request.user.email).first()
        return None

    def get(self, request):
        from .feed import build_feed
        candidate = self._get_profile(request)

        # Preview no console (staff sem Perfil vinculado): render vazio com instrução.
        if candidate is None:
            preview_candidate = None
            if request.user.is_staff or request.user.is_superuser:
                preview_candidate = CandidateProfile.objects.filter(
                    visibility_match=True,
                ).order_by('-created_at').first()
            return render(request, self.template_name, {
                'items': [] if not preview_candidate else self._items_for(preview_candidate, request),
                'candidate': preview_candidate,
                'entry_point': None,
                'preview_mode': True,
                'no_profile_bound': True,
            })

        entry_point = None
        ep_id = request.session.get('ep_id')
        if ep_id:
            entry_point = EntryPoint.objects.filter(pk=ep_id).first()

        items = self._items_for(candidate, request, entry_point=entry_point)
        return render(request, self.template_name, {
            'items': items,
            'candidate': candidate,
            'entry_point': entry_point,
        })

    def _items_for(self, candidate, request, entry_point=None):
        from .feed import build_feed
        items = build_feed(candidate, entry_point=entry_point)
        opp_ids = [it['opportunity_id'] for it in items]
        opps = {p.pk: p for p in Position.objects.filter(pk__in=opp_ids).select_related('business_unit', 'organization')}
        for it in items:
            opp = opps.get(it['opportunity_id'])
            if opp:
                it['store_name'] = opp.business_unit.name if opp.business_unit else opp.organization.name
        return items


class CandidateOpportunityInterestView(View):
    """POST — candidato manifesta interesse em uma Opportunity."""

    def post(self, request, opportunity_id):
        from .services import (
            deliver_opportunity_notice, person_interested,
        )
        from .models import RelationStateError

        pid = request.session.get('matchco_profile_id')
        if not pid:
            return redirect('recruitment_public:candidato_signup')
        candidate = get_object_or_404(CandidateProfile, pk=pid)
        opp = get_object_or_404(Position, pk=opportunity_id, organization=candidate.organization)

        rel = deliver_opportunity_notice(candidate=candidate, opportunity=opp)
        try:
            person_interested(relation=rel)
        except RelationStateError as exc:
            messages.error(request, str(exc))
            return redirect('recruitment_public:candidato_feed')

        contextual_answer = CandidateSignupAnswer.objects.filter(
            candidate=candidate,
            business_unit=opp.business_unit,
            relation__isnull=True,
            gdpr_deletion_completed__isnull=True,
        ).order_by('-created_at').first()
        if contextual_answer:
            contextual_answer.relation = rel
            contextual_answer.relation_state_at_response = rel.state
            contextual_answer.save(update_fields=['relation', 'relation_state_at_response'])

        messages.success(request, gettext_lazy('Interesse registrado. Agora é a vez da loja.'))
        return redirect('recruitment_public:candidato_feed')


class CandidateOpportunityDeclineView(View):
    def post(self, request, opportunity_id):
        from .services import deliver_opportunity_notice, candidate_declined
        pid = request.session.get('matchco_profile_id')
        if not pid:
            return redirect('recruitment_public:candidato_signup')
        candidate = get_object_or_404(CandidateProfile, pk=pid)
        opp = get_object_or_404(Position, pk=opportunity_id, organization=candidate.organization)
        rel = deliver_opportunity_notice(candidate=candidate, opportunity=opp)
        candidate_declined(relation=rel)
        return redirect('recruitment_public:candidato_feed')


class CandidateCirculationToggleView(View):
    """POST — candidato pausa/retoma sua circulação."""

    def post(self, request):
        pid = request.session.get('matchco_profile_id')
        candidate = CandidateProfile.objects.filter(pk=pid).first() if pid else None
        if candidate is None and request.user.is_authenticated and getattr(request.user, 'email', None):
            candidate = CandidateProfile.objects.filter(email=request.user.email).first()
        if candidate is None:
            return redirect('recruitment_public:candidato_signup')
        want = request.POST.get('state', '')
        if want in (CandidateProfile.CIRCULATION_ALLOWED, CandidateProfile.CIRCULATION_PAUSED):
            candidate.circulation_state = want
            candidate.save(update_fields=['circulation_state', 'updated_at'])
        return redirect('recruitment_public:candidato_feed')


class EmployerRelationRespondView(LoginRequiredMixin, View):
    """POST — empregador cria Response RC-01..05 obrigatória."""

    def post(self, request, relation_id):
        from .services import create_response, _resolve_employer_actor
        from .models import ResponseValidationError

        rel = get_object_or_404(
            Relation.objects.select_related('opportunity'), pk=relation_id,
        )
        try:
            _resolve_employer_actor(
                request.user, rel.opportunity, AuthorityScope.AA5_CLOSE_OPPORTUNITY,
            )
        except AuthorityError:
            return HttpResponseForbidden('Sem escopo AA-5 para esta Opportunity')

        response_class = request.POST.get('response_class', '')
        note = request.POST.get('note', '')

        try:
            resp = create_response(
                relation=rel, actor=request.user,
                response_class=response_class, note=note,
            )
        except ResponseValidationError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        return JsonResponse({
            'response_id': str(resp.id),
            'response_class': resp.response_class,
            'relation_state': rel.state,
        })


class PrivacyProcessorsView(TemplateView):
    template_name = 'recruitment/privacy/processors.html'

    def get_context_data(self, **kwargs):
        from django.conf import settings as _s
        ctx = super().get_context_data(**kwargs)
        ctx['processors'] = getattr(_s, 'MATCHCO_PROCESSOR_REGISTER', [])
        return ctx
