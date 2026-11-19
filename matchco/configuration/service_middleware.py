"""Enforce the configured service entitlement at each routed entry point.

The menu is a navigation aid, not an authorization boundary. This middleware
maps operational routes to the existing service catalog and checks the same
organization/company subscription used by the Console menu.
"""

from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.deprecation import MiddlewareMixin

from .models import BusinessUnit, Company, Organization, OrganizationServiceSubscription
from .services import service_enabled


_CONSOLE_CONTENT_NAMES = (
    'publication-', 'document-', 'media-',
)
_CONSOLE_TRAINING_NAMES = (
    'course-', 'course_editor-', 'course-editor-', 'module-', 'text-', 'video-',
    'file-', 'quiz-', 'question-', 'answer-', 'trail-', 'content-delete',
    'content-reorder',
)
_CONSOLE_EMPTY_CATALOG_NAMES = {
    'publication-list', 'document-list', 'media-list', 'media-collection-list',
    'course-list', 'quiz-list', 'trail-list', 'certification-list',
}
_APP_EMPTY_CATALOG_NAMES = {'courses', 'trails'}

_PUBLIC_RECRUITMENT_NAMES = (
    'candidato_', 'candidate_', 'lojista_', 'shopping_',
)
_ENTRY_POINT_PURPOSE_SERVICE = {
    'recruitment': 'recruitment',
    'training': 'training',
    'certification': 'certification',
    'communication': 'content',
    'campaign': 'campaigns',
    'partner_access': 'partners',
}
_PROGRAM_KIND_SERVICE = {
    'training': 'training',
    'certification': 'certification',
    'campaign': 'campaigns',
    'communication': 'content',
    'recruitment': 'recruitment',
}


def _safe_first(queryset):
    """Treat malformed URL/session identifiers as absent context, not 500s."""
    try:
        return queryset.first()
    except (TypeError, ValueError, ValidationError):
        return None


def required_service_for_request(request):
    """Return the existing service code required by this routed request."""
    resolver = getattr(request, 'resolver_match', None)
    if resolver is None:
        return None
    namespace = resolver.namespace or resolver.app_name or ''
    namespaces = set(namespace.split(':'))
    name = resolver.url_name or ''
    path = request.path_info

    if 'console' in namespaces:
        # The certification catalog is intentionally available for every
        # organization.  An organization without certification records must
        # see the empty state, not a tenant/service 404.  The public
        # verification endpoint below remains protected by certification.
        if name.startswith(('content-metrics', 'media-metrics', 'learning-metrics', 'engagement-funnel')):
            return 'analytics'
        if name.startswith(_CONSOLE_CONTENT_NAMES) or name in {
            'content-audit', 'content-questions', 'latest-changes',
        }:
            return 'content'
        if name.startswith(_CONSOLE_TRAINING_NAMES) or name in {
            'compliance-dashboard', 'admin-org-courses',
        }:
            return 'training'
        if name.startswith('questionnaire-') or name == 'business_unit_match_functions':
            return 'recruitment'

    if 'recruitment' in namespaces:
        return 'recruitment'

    if 'app' in namespaces:
        if name in {'courses', 'course_detail', 'course_play', 'course_progress', 'trails'}:
            return 'training'
        if name in {'feed', 'wiki'}:
            return 'content'
        if name in {'opportunities', 'matches', 'match_detail'}:
            return 'recruitment'

    if 'courses' in namespaces:
        return 'training'

    if 'api' in namespaces and name in {
        'course-list', 'course-detail', 'course-contents', 'course-enroll',
        'subject_list', 'subject_detail',
    }:
        return 'training'

    if 'learning_api' in namespaces and name.startswith('gamification-'):
        return 'training'

    if 'chat' in namespaces:
        return 'talk'

    if 'learning_api' in namespaces:
        if name.startswith('document-') or name == 'documents':
            return 'content'
        if name == 'analytics-engagement':
            return 'analytics'
        if name == 'partner-me':
            return 'partners'

    # These application URLconfs are included without an explicit namespace.
    if path.startswith(('/documents/', '/feed/', '/wiki/', '/publication/', '/media/')):
        return 'content'
    if path.startswith('/partner/'):
        return 'partners'
    if path.startswith('/certificacoes/verificar/'):
        return 'certification'
    if path.startswith('/gamification/'):
        return 'training'
    if path.startswith('/notifications/'):
        return 'content'
    if path == '/latest-changes/':
        return 'content'
    if path.startswith(('/recommendations/', '/feedback/', '/questions/')):
        return 'content'

    if 'recruitment_public' in namespaces:
        if name.startswith(_PUBLIC_RECRUITMENT_NAMES):
            return 'recruitment'
        if name in {
            'entry_point_choice', 'program_entry', 'program_direct',
            'program_invite_accept', 'entry_point_resolve',
            'entry_point_qr_image', 'entry_point_print',
        }:
            entry_point = _entry_point_for_request(request)
            if entry_point:
                return _ENTRY_POINT_PURPOSE_SERVICE.get(entry_point.purpose, 'recruitment')
            program = _program_for_request(request)
            return _PROGRAM_KIND_SERVICE.get(getattr(program, 'kind', ''), 'recruitment')

    return None


def _entry_point_for_request(request):
    from recruitment.models import EntryPoint

    entry_id = (
        request.resolver_match.kwargs.get('entry_point_id')
        or request.session.get('ep_id')
        or request.GET.get('entry_point')
        or request.GET.get('entry')
        or request.POST.get('entry_point')
        or request.POST.get('entry')
    )
    entry = _safe_first(
        EntryPoint.objects.select_related('organization', 'scope_store').filter(pk=entry_id)
    ) if entry_id else None
    if entry:
        return entry

    program = _program_for_request(request)
    if program:
        entry = _safe_first(EntryPoint.objects.filter(program_id=program.pk))
        if entry:
            return entry
    return None


def _program_for_request(request):
    from recruitment.models import Program, ProgramInvite

    program_id = request.resolver_match.kwargs.get('program_id')
    if program_id:
        program = _safe_first(Program.objects.filter(pk=program_id))
        if program:
            return program
    token = request.resolver_match.kwargs.get('token')
    invite = _safe_first(
        ProgramInvite.objects.select_related('program').filter(token=token)
    ) if token else None
    if invite:
        return invite.program
    return None


def _legacy_organization(legacy_id):
    if not legacy_id:
        return None
    return _safe_first(Organization.objects.filter(pk=legacy_id, active=True))


def _organization_for_request(request, required_service):
    organization = getattr(request, 'active_organization', None)
    if organization is not None:
        return organization

    session = request.session
    # Public candidate pages are contextual to a QR/profile when one exists.
    profile_id = session.get('matchco_profile_id')
    if profile_id:
        from recruitment.models import CandidateProfile
        profile = _safe_first(
            CandidateProfile.objects.select_related('organization').filter(pk=profile_id)
        )
        organization = _legacy_organization(getattr(profile, 'organization_id', None) and profile.organization.legacy_id)
        if organization:
            return organization

    portal_org_id = session.get('matchco_portal_organization_id')
    organization = _safe_first(
        Organization.objects.filter(pk=portal_org_id, active=True)
    ) if portal_org_id else None
    if organization:
        return organization

    recruitment_org_id = session.get('matchco_portal_recruitment_organization_id')
    if recruitment_org_id:
        from recruitment.domain_models import RecruitmentOrganization
        recruitment_org = _safe_first(RecruitmentOrganization.objects.filter(pk=recruitment_org_id))
        organization = _legacy_organization(getattr(recruitment_org, 'legacy_id', None))
        if organization:
            return organization

    is_public_recruitment = 'recruitment_public' in (request.resolver_match.namespace or '').split(':')
    entry = _entry_point_for_request(request) if is_public_recruitment else None
    organization = _legacy_organization(getattr(getattr(entry, 'organization', None), 'legacy_id', None))
    if organization:
        return organization

    slug = request.GET.get('organization') or request.GET.get('org') or request.POST.get('organization')
    organization = Organization.objects.filter(slug=slug, active=True).first() if slug else None
    return organization


def _company_for_request(request, organization):
    membership = getattr(request, 'active_membership', None)
    company_id = (
        getattr(request, 'active_company_id', None)
        or getattr(membership, 'company_id', None)
        or request.session.get('active_company_id')
        or request.GET.get('company_id')
    )
    if company_id and company_id != '__all__':
        return _safe_first(Company.objects.filter(
            pk=company_id, organization=organization, active=True,
        ))

    # Portal operations select a real unit; its owning company carries the
    # commercial override for the service.
    store_id = request.session.get('matchco_portal_store_id')
    if store_id and store_id != '__all__':
        from recruitment.domain_models import RecruitmentStore
        store = _safe_first(RecruitmentStore.objects.select_related('company').filter(pk=store_id))
        business_unit = BusinessUnit.objects.filter(
            pk=getattr(store, 'legacy_id', None), company__organization=organization,
        ).select_related('company').first() if store else None
        return business_unit.company if business_unit else None

    # A QR scoped to a store also resolves company-specific service overrides.
    if 'recruitment_public' in (request.resolver_match.namespace or '').split(':'):
        entry = _entry_point_for_request(request)
        store_legacy_id = getattr(getattr(entry, 'scope_store', None), 'legacy_id', None)
        business_unit = BusinessUnit.objects.filter(
            pk=store_legacy_id, company__organization=organization,
        ).select_related('company').first() if store_legacy_id else None
        if business_unit:
            return business_unit.company
    return None


def _has_company_context(request):
    membership = getattr(request, 'active_membership', None)
    if (
        getattr(request, 'active_company_id', None)
        or getattr(membership, 'company_id', None)
        or request.session.get('active_company_id')
        or request.GET.get('company_id')
    ) not in (None, '', '__all__'):
        return True
    store_id = request.session.get('matchco_portal_store_id')
    if store_id and store_id != '__all__':
        return True
    if 'recruitment_public' in (request.resolver_match.namespace or '').split(':'):
        entry = _entry_point_for_request(request)
        return bool(getattr(entry, 'scope_store_id', None))
    return False


class ServiceAccessMiddleware(MiddlewareMixin):
    """Reject direct URL/API access when the active tenant lacks the service."""

    @staticmethod
    def _unavailable_response(request):
        """Keep Console navigation usable without weakening service checks."""
        resolver = getattr(request, 'resolver_match', None)
        namespace = getattr(resolver, 'namespace', '') or getattr(resolver, 'app_name', '')
        if 'console' in namespace.split(':') and getattr(request.user, 'is_authenticated', False):
            return redirect('console:organization-home')
        return HttpResponseNotFound()

    def process_view(self, request, view_func, view_args, view_kwargs):
        service_code = required_service_for_request(request)
        if not service_code:
            return None

        organization = _organization_for_request(request, service_code)
        if organization is None:
            # Unauthenticated entry/login pages without a tenant context do
            # not expose tenant data. Their data-bearing continuation is gated
            # once a Profile, QR or organization has been resolved.
            if not request.user.is_authenticated and 'recruitment_public' in (request.resolver_match.namespace or '').split(':'):
                return None
            return HttpResponseNotFound()

        company = _company_for_request(request, organization)
        if _has_company_context(request) and company is None:
            return self._unavailable_response(request)
        if not service_enabled(organization, service_code, company=company):
            if (
                request.method == 'GET'
                and (
                    request.resolver_match.url_name in _CONSOLE_EMPTY_CATALOG_NAMES
                    or (
                        'app' in (request.resolver_match.namespace or '').split(':')
                        and request.resolver_match.url_name in _APP_EMPTY_CATALOG_NAMES
                    )
                )
            ):
                label = dict(OrganizationServiceSubscription.SERVICE_CHOICES).get(service_code, service_code)
                messages.warning(
                    request,
                    f'O serviço "{label}" está desativado para a organização ou empresa selecionada.',
                    fail_silently=True,
                )
                return None
            return self._unavailable_response(request)
        return None
