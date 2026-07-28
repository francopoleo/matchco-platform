import io
import base64

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView, View,
)

from configuration.models import Organization

from .forms import CandidateSignupForm, OfferForm, PositionForm
from .models import (
    CandidateProfile, Offer, Position, CandidateOnboardingTrail,
    CandidateProfileSurveyResponse, CandidateScore,
)
from configuration.models import JobFunction, BusinessUnit


class HTMXMixin:
    """No-op mixin. HTMX handling done via hx-select on the client side."""
    pass


# ---------- Public candidate signup ----------

class CandidateSignupView(CreateView):
    """Public candidate signup accessed via QR code or direct link."""
    model = CandidateProfile
    form_class = CandidateSignupForm
    template_name = 'recruitment/candidate_signup_public.html'
    success_url = reverse_lazy('recruitment:candidate_signup_success')

    def get_organization(self):
        slug = self.request.GET.get('org') or self.request.POST.get('org')
        if not slug:
            return None
        return Organization.objects.filter(slug=slug).first()

    def get_store(self):
        """Get preferred store if coming from store-specific QR code."""
        store_id = self.request.GET.get('store') or self.request.POST.get('store')
        if not store_id:
            return None
        try:
            return BusinessUnit.objects.get(pk=store_id)
        except BusinessUnit.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        self.organization = self.get_organization()
        if not self.organization:
            return render(request, 'recruitment/no_organization.html', {
                'organizations': Organization.objects.filter(active=True).order_by('name'),
            })
        self.store = self.get_store()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.organization
        kwargs['store'] = self.store
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['organization'] = self.organization
        ctx['store'] = self.store
        # If store was selected via QR, highlight interested_in field for selection
        if self.store:
            ctx['store_focus_field'] = 'id_interested_in'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['recruitment_last_org'] = self.organization.slug
        return response

    def get_success_url(self):
        return f"{reverse('recruitment:candidate_signup_success')}?org={self.organization.slug}"


class CandidateSignupSuccessView(TemplateView):
    template_name = 'recruitment/candidate_signup_success.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = self.request.GET.get('org') or self.request.session.get('recruitment_last_org')
        ctx['organization'] = Organization.objects.filter(slug=slug).first() if slug else None
        return ctx


# ---------- Console (staff-only) ----------

class OrgScopedMixin(HTMXMixin, LoginRequiredMixin):
    """Restrict queryset to the active organization on the request."""

    def get_active_org(self):
        org_id = getattr(self.request, 'active_organization_id', None)
        if not org_id:
            org_id = self.request.session.get('active_organization_id')
        if not org_id:
            return None
        return Organization.objects.filter(pk=org_id).first()

    def dispatch(self, request, *args, **kwargs):
        self.active_org = self.get_active_org()
        if not self.active_org:
            messages.error(request, 'No active organization selected.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class CandidateListView(OrgScopedMixin, ListView):
    template_name = 'recruitment/console/candidate_list.html'
    context_object_name = 'candidates'
    paginate_by = 25

    def get_queryset(self):
        qs = CandidateProfile.objects.filter(organization=self.active_org)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                first_name__icontains=q,
            ) | qs.filter(last_name__icontains=q) | qs.filter(email__icontains=q)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_org'] = self.active_org
        ctx['status_choices'] = CandidateProfile.STATUS_CHOICES
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class CandidateDetailView(OrgScopedMixin, DetailView):
    template_name = 'recruitment/console/candidate_detail.html'
    context_object_name = 'candidate'

    def get_queryset(self):
        return CandidateProfile.objects.filter(organization=self.active_org)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_org'] = self.active_org
        ctx['offer_form'] = OfferForm(organization=self.active_org)
        ctx['offers'] = self.object.offers.select_related('position').all()
        ctx['course_enrollments'] = self.object.course_enrollments.all()
        ctx['course_completions'] = self.object.course_completions.all()
        try:
            ctx['score'] = self.object.score
        except CandidateScore.DoesNotExist:
            ctx['score'] = None
        return ctx


class PositionListView(OrgScopedMixin, ListView):
    template_name = 'recruitment/console/position_list.html'
    context_object_name = 'positions'
    paginate_by = 25

    def get_queryset(self):
        return Position.objects.filter(organization=self.active_org).order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_org'] = self.active_org
        return ctx


class PositionCreateView(OrgScopedMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'recruitment/console/position_form.html'
    success_url = reverse_lazy('recruitment:position_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.active_org
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.active_org
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_org'] = self.active_org
        return ctx


class PositionUpdateView(OrgScopedMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'recruitment/console/position_form.html'
    success_url = reverse_lazy('recruitment:position_list')

    def get_queryset(self):
        return Position.objects.filter(organization=self.active_org)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.active_org
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_org'] = self.active_org
        return ctx


class OfferCreateView(OrgScopedMixin, View):
    def post(self, request, candidate_pk):
        candidate = get_object_or_404(
            CandidateProfile,
            pk=candidate_pk,
            organization=self.active_org,
        )
        form = OfferForm(request.POST, organization=self.active_org)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.candidate = candidate
            offer.organization = self.active_org
            offer.sent_by = request.user
            offer.save()
            if candidate.status == CandidateProfile.STATUS_NEW:
                candidate.status = CandidateProfile.STATUS_CONTACTED
                candidate.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Offer sent successfully.')
        else:
            messages.error(request, 'Please fix errors on the form.')
        return redirect('recruitment:candidate_detail', pk=candidate.pk)


# ---------- QR code generator ----------

class QRCodeView(OrgScopedMixin, TemplateView):
    template_name = 'recruitment/console/qr_code.html'

    def get_context_data(self, **kwargs):
        import qrcode
        from django.conf import settings
        from .url_builders import URLBuilder

        ctx = super().get_context_data(**kwargs)
        signup_path = reverse('recruitment:candidate_signup')

        # Use configured QR_CODE_BASE_URL if available (for proxy), otherwise use request host
        qr_code_url = getattr(settings, 'QR_CODE_BASE_URL', None)
        if qr_code_url:
            base_url = qr_code_url.rstrip('/')
            signup_url = f'{base_url}{signup_path}?org={self.active_org.slug}'
        else:
            signup_url = self.request.build_absolute_uri(
                f'{signup_path}?org={self.active_org.slug}'
            )

        # Optional: Add UTM parameters from query string
        # Usage: ?utm_source=email&utm_campaign=recruiting_2026&utm_content=newsletter
        campaign_name = self.request.GET.get('campaign_name')
        utm_source = self.request.GET.get('utm_source')
        utm_medium = self.request.GET.get('utm_medium')
        utm_campaign = self.request.GET.get('utm_campaign')
        utm_content = self.request.GET.get('utm_content')
        utm_term = self.request.GET.get('utm_term')
        qr_id = self.request.GET.get('qr_id')

        if campaign_name or utm_source:
            signup_url = URLBuilder.add_utm_params(
                signup_url,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_content=utm_content,
                utm_term=utm_term,
                qr_id=qr_id,
            )

        img = qrcode.make(signup_url, box_size=10, border=2)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        # Get stores for this org
        from configuration.models import BusinessUnit, Company
        companies = Company.objects.filter(organization=self.active_org)
        stores = BusinessUnit.objects.filter(company__in=companies).order_by('name')

        ctx['active_org'] = self.active_org
        ctx['signup_url'] = signup_url
        ctx['qr_data_url'] = f'data:image/png;base64,{b64}'
        ctx['page_title'] = 'QR Code - Organização'
        ctx['stores'] = stores
        return ctx


class QRCodeStoreView(OrgScopedMixin, TemplateView):
    """Generate QR code for a specific store with pre-filled store parameter."""
    template_name = 'recruitment/console/qr_code_store.html'

    def get_store(self):
        store_id = self.kwargs.get('store_id')
        if not store_id:
            return None
        try:
            return BusinessUnit.objects.get(pk=store_id, company__organization=self.active_org)
        except BusinessUnit.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        # Set active_org from mixin first
        self.active_org = self.get_active_org()
        if not self.active_org:
            messages.error(request, 'No active organization selected.')
            return redirect('home')

        self.store = self.get_store()
        if not self.store:
            messages.error(request, 'Store not found.')
            return redirect('recruitment:qr_code')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        import qrcode
        from django.conf import settings
        from .url_builders import URLBuilder

        ctx = super().get_context_data(**kwargs)
        signup_path = reverse('recruitment:candidate_signup')

        # Use configured QR_CODE_BASE_URL if available (for proxy), otherwise use request host
        qr_code_url = getattr(settings, 'QR_CODE_BASE_URL', None)
        if qr_code_url:
            base_url = qr_code_url.rstrip('/')
            signup_url = f'{base_url}{signup_path}?org={self.active_org.slug}&store={self.store.id}'
        else:
            signup_url = self.request.build_absolute_uri(
                f'{signup_path}?org={self.active_org.slug}&store={self.store.id}'
            )

        # Optional: Add UTM parameters from query string
        # Usage: ?utm_source=flyer&utm_campaign=bourbon_store5&utm_content=reception_area
        campaign_name = self.request.GET.get('campaign_name')
        utm_source = self.request.GET.get('utm_source')
        utm_medium = self.request.GET.get('utm_medium')
        utm_campaign = self.request.GET.get('utm_campaign')
        utm_content = self.request.GET.get('utm_content') or self.store.name
        utm_term = self.request.GET.get('utm_term')
        qr_id = self.request.GET.get('qr_id')

        if campaign_name or utm_source:
            signup_url = URLBuilder.add_utm_params(
                signup_url,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_content=utm_content,
                utm_term=utm_term,
                qr_id=qr_id,
            )

        img = qrcode.make(signup_url, box_size=10, border=2)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        ctx['active_org'] = self.active_org
        ctx['store'] = self.store
        ctx['signup_url'] = signup_url
        ctx['qr_data_url'] = f'data:image/png;base64,{b64}'
        ctx['page_title'] = f'QR Code - {self.store.name}'
        return ctx


# ---------- Candidate onboarding trail ----------

class CandidateOnboardingJobFunctionsView(TemplateView):
    """Step 1: Candidate selects job functions of interest."""
    template_name = 'recruitment/onboarding/job_functions.html'

    def get_organization(self):
        slug = self.request.GET.get('org') or self.request.POST.get('org')
        if not slug:
            return None
        return Organization.objects.filter(slug=slug).first()

    def dispatch(self, request, *args, **kwargs):
        self.organization = self.get_organization()
        if not self.organization:
            return render(request, 'recruitment/no_organization.html')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        company = self.organization.companies.first()
        job_functions = JobFunction.objects.filter(company=company, active=True) if company else []

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
                'recruitment:candidate_survey',
                candidate_id=candidate_id,
            )
        except CandidateProfile.DoesNotExist:
            messages.error(request, 'Candidate not found.')
            return redirect('recruitment:candidate_signup')


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
        self.candidate = self.get_candidate()
        if not self.candidate:
            raise Http404('Candidate not found')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['candidate'] = self.candidate
        ctx['survey_questions'] = self.get_survey_questions()

        # Check if already completed
        try:
            ctx['survey_response'] = self.candidate.profile_survey
        except CandidateProfileSurveyResponse.DoesNotExist:
            ctx['survey_response'] = None

        return ctx

    def post(self, request, *args, **kwargs):
        responses = {
            'experience': request.POST.get('experience'),
            'interests': request.POST.get('interests'),
            'skills': request.POST.get('skills'),
            'availability': request.POST.get('availability'),
        }

        # Save or update survey responses
        survey, _ = CandidateProfileSurveyResponse.objects.get_or_create(
            candidate=self.candidate,
            organization=self.candidate.organization,
        )
        survey.responses = responses
        survey.save()

        # Recalculate score
        score, _ = CandidateScore.objects.get_or_create(
            candidate=self.candidate,
            organization=self.candidate.organization,
        )
        score.recalculate()

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

        return redirect('recruitment:onboarding_complete', candidate_id=self.candidate.pk)

    def get_survey_questions(self):
        return [
            {
                'id': 'experience',
                'label': 'Qual é sua experiência anterior em vendas ou atendimento?',
                'type': 'textarea',
            },
            {
                'id': 'interests',
                'label': 'Em qual tipo de loja você mais gostaria de trabalhar?',
                'type': 'textarea',
            },
            {
                'id': 'skills',
                'label': 'Quais são suas principais habilidades profissionais?',
                'type': 'textarea',
            },
            {
                'id': 'availability',
                'label': 'Qual é sua disponibilidade de horários? (dias e turnos)',
                'type': 'textarea',
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
        self.candidate = self.get_candidate()
        if not self.candidate:
            raise Http404('Candidate not found')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['candidate'] = self.candidate

        try:
            ctx['score'] = self.candidate.score
        except CandidateScore.DoesNotExist:
            ctx['score'] = None

        return ctx


# ---------- Employee Dashboard ----------

class MarkCourseCompleteView(OrgScopedMixin, View):
    """Mark a candidate's course as completed."""
    def post(self, request, candidate_pk, course_id):
        candidate = get_object_or_404(
            CandidateProfile,
            pk=candidate_pk,
            organization=self.active_org,
        )

        from django.utils import timezone
        completion, created = CandidateCourseCompletion.objects.get_or_create(
            candidate=candidate,
            course_id=course_id,
        )

        completion.completed = True
        completion.completion_date = timezone.now()
        completion.progress_percentage = 100
        completion.save()

        # Recalculate score
        try:
            score = candidate.score
            score.recalculate()
        except CandidateScore.DoesNotExist:
            pass

        messages.success(request, f'Curso marcado como completo para {candidate.full_name}.')
        return redirect('recruitment:candidate_detail', pk=candidate.pk)


class EmployeeDashboardView(OrgScopedMixin, TemplateView):
    """Dashboard for employees showing candidates in their scope with scores."""
    template_name = 'recruitment/console/employee_dashboard.html'
    paginate_by = 20

    def get_employee_scope(self):
        """Determine which business unit the employee is scoped to."""
        from configuration.models import Membership

        # Get current membership
        memberships = self.request.user.memberships.filter(
            organization=self.active_org,
            active=True
        ).order_by('-is_primary', '-created_at')

        if memberships.exists():
            membership = memberships.first()
            return membership.business_unit
        return None

    def get_candidates_queryset(self):
        """Get candidates visible to this employee."""
        candidates = CandidateProfile.objects.filter(
            organization=self.active_org
        ).select_related('score')

        # Filter by employee's business unit if they have one
        employee_store = self.get_employee_scope()
        if employee_store:
            candidates = candidates.filter(preferred_store=employee_store)

        return candidates.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        candidates = self.get_candidates_queryset()

        # Search filter
        q = self.request.GET.get('q', '').strip()
        if q:
            candidates = candidates.filter(
                first_name__icontains=q
            ) | candidates.filter(
                last_name__icontains=q
            ) | candidates.filter(
                email__icontains=q
            )

        # Status filter
        status = self.request.GET.get('status')
        if status:
            candidates = candidates.filter(status=status)

        # Pagination
        from django.core.paginator import Paginator
        page = self.request.GET.get('page', 1)
        paginator = Paginator(candidates, self.paginate_by)
        page_obj = paginator.get_page(page)

        # Score statistics
        all_candidates = self.get_candidates_queryset()
        scores = CandidateScore.objects.filter(
            candidate__in=all_candidates
        ).values_list('overall_score', flat=True)

        avg_score = 0
        if scores:
            avg_score = sum(scores) / len(scores)

        ctx['active_org'] = self.active_org
        ctx['candidates'] = page_obj
        ctx['paginator'] = paginator
        ctx['status_choices'] = CandidateProfile.STATUS_CHOICES
        ctx['current_status'] = status or ''
        ctx['q'] = q
        ctx['avg_score'] = round(avg_score, 1)
        ctx['total_candidates'] = all_candidates.count()
        ctx['employee_store'] = self.get_employee_scope()

        return ctx


class JobFunctionsForBusinessUnitView(OrgScopedMixin, View):
    """API endpoint returning valid job functions for a business unit (for dynamic form filtering)."""

    def get(self, request, business_unit_id, *args, **kwargs):
        from django.http import JsonResponse

        try:
            business_unit = BusinessUnit.objects.get(
                pk=business_unit_id,
                company__organization=self.active_org,
            )
        except BusinessUnit.DoesNotExist:
            return JsonResponse({'error': 'Business unit not found'}, status=404)

        if business_unit.channel:
            job_functions = JobFunction.objects.filter(
                company=business_unit.company,
                channels=business_unit.channel,
                active=True,
            ).distinct().values('id', 'name')
        else:
            job_functions = JobFunction.objects.filter(
                company=business_unit.company,
                active=True,
            ).values('id', 'name')

        return JsonResponse({
            'business_unit': business_unit.name,
            'channel': business_unit.channel.name if business_unit.channel else None,
            'job_functions': list(job_functions),
        })
