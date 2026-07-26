import csv
import io
from collections import defaultdict
from functools import wraps
from urllib.parse import urlencode
from unidecode import unidecode

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from audience.models import AudiencePolicy, AudienceRule
from audience.services import estimate_policy_reach
from configuration.models import (
    BusinessChannel, BusinessUnit, Company, JobFunction, ManagementAssignment, Membership,
    OperationalUnit, Organization, OrganizationTerminology, PersonType,
)
from configuration.services import management_access
from courses.models import Content, Course
from documents.models import Document
from publishing.models import ContentFeedback, ContentInteraction, ContentQuestion, Publication
from learning.models import AnalyticsExportAudit, ContentEvent
from learning.models import ContentTrail, TrailAssignment, TrailStep
from user_management.models import RegistrationRequest

from .forms import (
    AudiencePolicyForm, AudienceRuleForm, AudienceSimulationForm, ConsoleUserForm, CourseConsoleForm,
    ManagementAssignmentForm, MembershipAssignmentForm,
    MembershipForm, OrganizationTerminologyForm, PersonTypeForm, PublicationForm,
    TrailAssignmentForm, TrailForm,
)


def _metrics_pdf(lines):
    """Build a small dependency-free, printable PDF for governed exports."""
    text_lines = [str(line).encode('latin-1', 'replace').decode('latin-1') for line in lines]
    stream_lines = ['BT', '/F1 10 Tf', '50 760 Td']
    for index, line in enumerate(text_lines):
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        if index:
            stream_lines.append('0 -16 Td')
        stream_lines.append(f'({safe}) Tj')
    stream_lines.append('ET')
    stream = '\n'.join(stream_lines).encode('latin-1')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream',
    ]
    output = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f'{number} 0 obj\n'.encode())
        output.extend(obj)
        output.extend(b'\nendobj\n')
    xref = len(output)
    output.extend(f'xref\n0 {len(objects) + 1}\n'.encode())
    output.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        output.extend(f'{offset:010d} 00000 n \n'.encode())
    output.extend(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode())
    return bytes(output)

User = get_user_model()


def active_organization_queryset(request, queryset, field='organization_id', include_global=True):
    """Limit console data to the organization selected in the navbar.

    Global records (without an organization) remain visible because they are
    intentionally shared across tenants. Tenant records never cross the
    active organization boundary.
    """
    organization = getattr(request, 'active_organization', None)
    if organization is None:
        organization_id = getattr(request.user, '_active_organization_id', None)
    else:
        organization_id = organization.pk
    if not organization_id:
        return queryset
    lookup = {field: organization_id}
    if include_global:
        return queryset.filter(Q(**lookup) | Q(**{field.replace('_id', '') + '__isnull': True}))
    return queryset.filter(**lookup)


def active_organization(request):
    return getattr(request, 'active_organization', None)


def accent_insensitive_search(*field_names):
    """Filter queryset by accent-insensitive search across fields (Pediátrica = Pediatrica)."""
    def search_filter(queryset, search_term):
        if not search_term:
            return queryset

        # Normalize search term
        normalized_term = unidecode(search_term).lower()

        # Get all objects and filter in Python with accent normalization
        filtered_ids = []
        for obj in queryset:
            for field_name in field_names:
                field_value = str(getattr(obj, field_name, ''))
                normalized_value = unidecode(field_value).lower()
                if normalized_term in normalized_value:
                    filtered_ids.append(obj.id)
                    break

        return queryset.filter(id__in=filtered_ids) if filtered_ids else queryset.none()
    return search_filter


def manager_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        user = request.user
        allowed = user.is_authenticated and (
            user.is_superuser or user.is_staff or
            user.groups.filter(name__in=('content_manager', 'audience_manager')).exists()
        )
        if not allowed:
            return HttpResponseForbidden('Management access required.')
        return view(request, *args, **kwargs)
    return wrapped


class ManagerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.is_staff or user.groups.filter(
                name__in=('content_manager', 'audience_manager')).exists()):
            return HttpResponseForbidden('Management access required.')
        return super().dispatch(request, *args, **kwargs)


class ConsoleDashboardView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = active_organization(self.request)
        publications = active_organization_queryset(self.request, Publication.objects)
        courses = active_organization_queryset(self.request, Course.objects)
        policies = active_organization_queryset(self.request, AudiencePolicy.objects)

        if organization:
            org_users = User.objects.filter(
                memberships__organization=organization,
                memberships__active=True,
            ).distinct()
            org_rules = AudienceRule.objects.filter(
                policy__organization=organization,
                policy__active=True,
            )
        else:
            org_users = User.objects.all()
            org_rules = AudienceRule.objects.filter(policy__active=True)

        context.update({
            'publication_count': publications.count(),
            'published_count': publications.filter(status=Publication.PUBLISHED).count(),
            'policy_count': policies.count(),
            'course_count': courses.filter(type='course').count(),
            'user_count': org_users.count(),
            'rule_count': org_rules.count(),
            'publication_by_kind': publications.values('kind').annotate(total=Count('id')),
            'active_organization': organization,
        })
        return context


class PublicationConsoleListView(ManagerRequiredMixin, ListView):
    model = Publication
    template_name = 'console/publication_list.html'
    context_object_name = 'publications'
    paginate_by = 20

    def get_queryset(self):
        queryset = active_organization_queryset(self.request, super().get_queryset()).select_related(
            'author', 'organization', 'audience_policy'
        ).prefetch_related('audience_policy__rules')
        query = self.request.GET.get('q', '').strip()
        kind = self.request.GET.get('kind', '').strip()
        status = self.request.GET.get('status', '').strip()
        if query:
            search_filter = accent_insensitive_search('title', 'excerpt')
            queryset = search_filter(queryset, query)
        if kind in (Publication.FEED, Publication.WIKI):
            queryset = queryset.filter(kind=kind)
        if status in (Publication.DRAFT, Publication.PUBLISHED):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_organization'] = active_organization(self.request)
        publications_page = context['publications']
        publications = list(getattr(publications_page, 'object_list', publications_page))
        rules_by_publication = {}
        ids_by_dimension = defaultdict(set)

        for publication in publications:
            rules = list(publication.audience_policy.rules.all()) if publication.audience_policy else []
            rules_by_publication[publication.pk] = {rule.dimension: rule for rule in rules}
            for rule in rules:
                ids_by_dimension[rule.dimension].update(str(value) for value in rule.values)

        model_by_dimension = {
            AudienceRule.COMPANY: Company,
            AudienceRule.BUSINESS_UNIT: BusinessUnit,
            AudienceRule.OPERATIONAL_UNIT: OperationalUnit,
            AudienceRule.CHANNEL: BusinessChannel,
            AudienceRule.FUNCTION: JobFunction,
        }
        names_by_dimension = {}
        for dimension, model in model_by_dimension.items():
            names_by_dimension[dimension] = {
                str(item.pk): item.name
                for item in model.objects.filter(pk__in=ids_by_dimension[dimension])
            }

        for publication in publications:
            rules = rules_by_publication.get(publication.pk, {})
            organization = publication.organization or getattr(publication.audience_policy, 'organization', None)
            if not organization and not rules:
                publication.audience_levels = [{'label': 'Audiência', 'values': ['Todos os usuários'], 'all': True}]
                continue

            levels = [{'label': 'Organização', 'values': [organization.name] if organization else ['*'], 'all': not organization}]
            for dimension, label in (
                (AudienceRule.COMPANY, 'Empresa'),
                (AudienceRule.BUSINESS_UNIT, 'Business unit'),
                (AudienceRule.OPERATIONAL_UNIT, 'Unidade operacional'),
                (AudienceRule.CHANNEL, 'Canal'),
                (AudienceRule.FUNCTION, 'Função'),
            ):
                rule = rules.get(dimension)
                values = [names_by_dimension[dimension].get(str(value), f'#{value}') for value in rule.values] if rule else ['*']
                levels.append({'label': label, 'values': values, 'all': not rule})
            publication.audience_levels = levels

        return context


class PublicationConsoleCreateView(ManagerRequiredMixin, CreateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'console/publication_form.html'
    success_url = reverse_lazy('console:publication-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organization = active_organization(self.request)
        if organization:
            kwargs['organization_queryset'] = Organization.objects.filter(pk=organization.pk)
            kwargs['documents_queryset'] = Document.objects.filter(
                status=Document.PUBLISHED,
            ).filter(Q(organization=organization) | Q(organization__isnull=True)).distinct()
            kwargs.setdefault('initial', {})['organization'] = organization.pk
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Publicação salva com sucesso.')
        return super().form_valid(form)


class PublicationConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'console/publication_form.html'
    success_url = reverse_lazy('console:publication-list')

    def get_queryset(self):
        return active_organization_queryset(self.request, super().get_queryset())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organization = active_organization(self.request)
        if organization:
            kwargs['organization_queryset'] = Organization.objects.filter(pk=organization.pk)
            kwargs['documents_queryset'] = Document.objects.filter(
                status=Document.PUBLISHED,
            ).filter(Q(organization=organization) | Q(organization__isnull=True)).distinct()
        return kwargs


class ContentMetricsView(ManagerRequiredMixin, TemplateView):
    """Operational view of reach, feedback and content priority."""

    template_name = 'console/content_metrics.html'

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format') == 'pdf':
            active_org = active_organization(self.request)
            rows = context.get('publications', [])
            AnalyticsExportAudit.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                organization=active_org,
                report_name='content_metrics_pdf',
                filters={key: value for key, value in context.get('filters', {}).items() if value},
                row_count=len(rows),
            )
            lines = [
                'Talk - Metricas de conteudo',
                f"Periodo: ultimos {context.get('filters', {}).get('period', '30')} dias",
                f"Conteudos: {len(rows)} | Visualizacoes: {context.get('total_views', 0)} | Leitores: {context.get('total_readers', 0)}",
                f"Feedbacks: {context.get('total_feedback', 0)} | Perguntas: {context.get('total_questions', 0)}",
                '',
            ]
            lines.extend(
                f"- {item.title[:70]} | {item.get_kind_display()} | {item.metric_views} views | {item.metric_readers} leitores | {item.metric_feedback} feedbacks"
                for item in rows
            )
            response = HttpResponse(_metrics_pdf(lines), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="talk-content-metrics.pdf"'
            return response
        if self.request.GET.get('format') == 'csv':
            active_org = active_organization(self.request)
            AnalyticsExportAudit.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                organization=active_org,
                report_name='content_metrics_csv',
                filters={key: value for key, value in context.get('filters', {}).items() if value},
                row_count=len(context.get('publications', [])),
            )
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="talk-content-metrics.csv"'
            response.write('\ufeff')
            writer = csv.writer(response)
            writer.writerow(['Conteúdo', 'Tipo', 'Importância', 'Visualizações', 'Leitores', 'Feedbacks', 'Ajudou %', 'Não ajudou %', 'Tempo ativo (s)', 'Tempo médio (s)'])
            for item in context.get('publications', []):
                writer.writerow([
                    item.title, item.get_kind_display(), item.get_importance_display(), item.metric_views,
                    item.metric_readers, item.metric_feedback, item.metric_helpful_rate or '',
                    item.metric_not_helpful_rate or '', item.metric_active_seconds, item.metric_avg_active_seconds,
                ])
            return response
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = active_organization_queryset(
            self.request,
            Publication.objects.filter(status=Publication.PUBLISHED),
        ).select_related('organization', 'author')
        query = self.request.GET.get('q', '').strip()
        kind = self.request.GET.get('kind', '').strip()
        importance = self.request.GET.get('importance', '').strip()
        category = self.request.GET.get('category', '').strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(body__icontains=query))
        if kind in (Publication.FEED, Publication.WIKI):
            queryset = queryset.filter(kind=kind)
        if importance in (Publication.ROUTINE, Publication.IMPORTANT, Publication.CRITICAL):
            queryset = queryset.filter(importance=importance)
        if category:
            queryset = queryset.filter(content_category=category)

        publications = list(queryset.order_by('-importance', '-published_at'))
        audience_form = AudienceSimulationForm(self.request.GET or None)
        audience_keys = ('organization', 'companies', 'business_units', 'operational_units', 'channels', 'functions')
        audience_has_selection = any(self.request.GET.getlist(key) for key in audience_keys)
        if audience_has_selection and audience_form.is_valid():
            selected_scope = AudienceSimulationView._selected_scope(audience_form)
            memberships = list(
                active_organization_queryset(self.request, Membership.objects.filter(active=True))
                .prefetch_related('channels', 'functions')
            )
            publications = [
                item for item in publications
                if AudienceSimulationView._impacted_users(item, memberships, selected_scope) > 0
            ]
        content_type = ContentType.objects.get_for_model(Publication)
        ids = [item.pk for item in publications]
        interaction_rows = {
            row['object_id']: row
            for row in ContentInteraction.objects.filter(
                content_type=content_type, object_id__in=ids,
            ).values('object_id').annotate(
                views=Sum('view_count'), readers=Count('user', distinct=True),
                acknowledged=Count('acknowledged_at'),
            )
        }
        feedback_rows = {
            row['object_id']: row
            for row in ContentFeedback.objects.filter(
                content_type=content_type, object_id__in=ids,
            ).values('object_id').annotate(
                total=Count('id'),
                helpful=Count('id', filter=Q(rating=ContentFeedback.HELPFUL)),
                partial=Count('id', filter=Q(rating=ContentFeedback.PARTIAL)),
                not_helpful=Count('id', filter=Q(rating=ContentFeedback.NOT_HELPFUL)),
            )
        }
        question_rows = {
            row['object_id']: row
            for row in ContentQuestion.objects.filter(
                content_type=content_type, object_id__in=ids,
            ).values('object_id').annotate(
                total=Count('id'), open=Count('id', filter=Q(status=ContentQuestion.OPEN)),
            )
        }
        event_rows = {
            row['object_id']: row
            for row in ContentEvent.objects.filter(
                content_type=content_type, object_id__in=ids,
            ).values('object_id').annotate(
                active_seconds=Sum('active_seconds'),
                active_users=Count('user', filter=Q(event_name=ContentEvent.CONTENT_ACTIVE), distinct=True),
            )
        }
        total_views = total_readers = total_feedback = total_helpful = total_partial = total_not_helpful = total_questions = 0
        for item in publications:
            interaction = interaction_rows.get(item.pk, {})
            feedback = feedback_rows.get(item.pk, {})
            questions = question_rows.get(item.pk, {})
            events = event_rows.get(item.pk, {})
            item.metric_views = interaction.get('views') or 0
            item.metric_readers = interaction.get('readers') or 0
            item.metric_acknowledged = interaction.get('acknowledged') or 0
            item.metric_feedback = feedback.get('total') or 0
            item.metric_helpful = feedback.get('helpful') or 0
            item.metric_partial = feedback.get('partial') or 0
            item.metric_not_helpful = feedback.get('not_helpful') or 0
            item.metric_questions = questions.get('total') or 0
            item.metric_open_questions = questions.get('open') or 0
            item.metric_active_seconds = events.get('active_seconds') or 0
            item.metric_active_users = events.get('active_users') or 0
            item.metric_avg_active_seconds = round(item.metric_active_seconds / item.metric_active_users) if item.metric_active_users else 0
            item.metric_helpful_rate = round(item.metric_helpful * 100 / item.metric_feedback) if item.metric_feedback else None
            item.metric_not_helpful_rate = round(item.metric_not_helpful * 100 / item.metric_feedback) if item.metric_feedback else None
            total_views += item.metric_views
            total_readers += item.metric_readers
            total_feedback += item.metric_feedback
            total_helpful += item.metric_helpful
            total_partial += item.metric_partial
            total_not_helpful += item.metric_not_helpful
            total_questions += item.metric_questions

        review_queue = [
            item for item in publications
            if item.metric_views >= 3 and item.metric_feedback >= 2 and (item.metric_not_helpful_rate or 0) >= 30
        ]
        review_queue.sort(key=lambda item: (item.metric_not_helpful_rate, item.metric_views), reverse=True)
        critical_low_reading = [
            item for item in publications
            if item.importance == Publication.CRITICAL and item.metric_readers == 0
        ][:8]

        event_queryset = ContentEvent.objects.all()
        organization = active_organization(self.request)
        if organization:
            event_queryset = event_queryset.filter(organization=organization)
        period = self.request.GET.get('period', '30').strip()
        if period not in {'7', '30', '90', '365'}:
            period = '30'
        event_queryset = event_queryset.filter(
            occurred_at__gte=timezone.now() - timezone.timedelta(days=int(period)),
        )
        event_metrics = event_queryset.aggregate(
            course_enrollments=Count('id', filter=Q(event_name=ContentEvent.COURSE_ENROLLED)),
            content_completions=Count('id', filter=Q(event_name=ContentEvent.CONTENT_COMPLETED)),
            trail_starts=Count('id', filter=Q(event_name=ContentEvent.TRAIL_STARTED)),
            trail_completions=Count('id', filter=Q(event_name=ContentEvent.TRAIL_COMPLETED)),
            active_seconds=Sum('active_seconds'),
            opened_users=Count('user', filter=Q(event_name=ContentEvent.CONTENT_OPENED), distinct=True),
            active_users=Count('user', filter=Q(event_name=ContentEvent.CONTENT_ACTIVE), distinct=True),
            acknowledged_users=Count('user', filter=Q(event_name=ContentEvent.CONTENT_ACKNOWLEDGED), distinct=True),
            step_users=Count('user', filter=Q(event_name=ContentEvent.TRAIL_STEP_COMPLETED), distinct=True),
        )
        repeated_users = event_queryset.values('user_id').annotate(total=Count('id')).filter(total__gt=1).count()
        event_metrics['returning_users'] = repeated_users
        event_metrics['abandoned_users'] = max(0, (event_metrics.get('opened_users') or 0) - (event_metrics.get('active_users') or 0))
        course_content_type = ContentType.objects.get_for_model(Content)
        event_metrics['course_feedback'] = ContentFeedback.objects.filter(content_type=course_content_type).count()
        event_metrics['operational_actions'] = event_queryset.filter(event_name=ContentEvent.ACTION_COMPLETED).count()
        question_aggregate = ContentQuestion.objects.filter(
            content_type=content_type,
        ).values('question_hash').annotate(total=Count('id'))
        event_metrics['repeated_questions'] = sum(max(0, row['total'] - 1) for row in question_aggregate)
        search_times = list(ContentEvent.objects.filter(
            event_name=ContentEvent.SEARCH_PERFORMED,
            metadata__time_to_results_ms__isnull=False,
        ).values_list('metadata', flat=True))
        elapsed_values = [item.get('time_to_results_ms') for item in search_times if isinstance(item, dict) and item.get('time_to_results_ms') is not None]
        event_metrics['avg_search_time_ms'] = round(sum(elapsed_values) / len(elapsed_values)) if elapsed_values else None
        min_group_size = max(1, int(getattr(settings, 'ANALYTICS_MIN_GROUP_SIZE', 5)))
        event_metrics['privacy_suppressed'] = bool(
            event_metrics.get('opened_users') and event_metrics['opened_users'] < min_group_size
        )

        context.update({
            'publications': publications,
            'active_organization': active_organization(self.request),
            'total_views': total_views,
            'total_readers': total_readers,
            'total_feedback': total_feedback,
            'total_questions': total_questions,
            'helpful_rate': round(total_helpful * 100 / total_feedback) if total_feedback else None,
            'partial_rate': round(total_partial * 100 / total_feedback) if total_feedback else None,
            'not_helpful_rate': round(total_not_helpful * 100 / total_feedback) if total_feedback else None,
            'categories': Publication.CONTENT_CATEGORIES,
            'filters': {'q': query, 'kind': kind, 'importance': importance, 'category': category, 'period': period},
            'event_metrics': event_metrics,
            'review_queue': review_queue[:8],
            'critical_low_reading': critical_low_reading,
            'analytics_min_group_size': min_group_size,
            'audience_form': audience_form,
            'audience_has_selection': audience_has_selection,
            'export_query': urlencode([(key, value) for key in self.request.GET for value in self.request.GET.getlist(key) if key != 'format']),
        })
        return context


class ContentQuestionConsoleView(ManagerRequiredMixin, View):
    template_name = 'console/content_question_list.html'

    def get_queryset(self):
        queryset = ContentQuestion.objects.select_related('user', 'answered_by').order_by('-created_at')
        organization = active_organization(self.request)
        if organization:
            publication_type = ContentType.objects.get_for_model(Publication)
            ids = Publication.objects.filter(organization=organization).values_list('pk', flat=True)
            queryset = queryset.filter(content_type=publication_type, object_id__in=ids)
        status = self.request.GET.get('status', '')
        if status in dict(ContentQuestion.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get(self, request):
        return render(request, self.template_name, {
            'questions': self.get_queryset(),
            'status': request.GET.get('status', ''),
            'status_choices': ContentQuestion.STATUS_CHOICES,
        })

    def post(self, request):
        question = get_object_or_404(self.get_queryset(), pk=request.POST.get('pk'))
        answer = request.POST.get('answer', '').strip()
        if answer:
            question.answer = answer[:4000]
            question.status = ContentQuestion.ANSWERED
            question.answered_by = request.user
            question.answered_at = timezone.now()
            question.save(update_fields=('answer', 'status', 'answered_by', 'answered_at', 'updated_at'))
        return redirect('console:content-questions')


class EngagementFunnelView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/engagement_funnel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kind = self.request.GET.get('kind', '')
        period = self.request.GET.get('period', '30')
        if period not in {'7', '30', '90', '365'}:
            period = '30'
        cutoff = timezone.now() - timezone.timedelta(days=int(period))
        publications = list(active_organization_queryset(self.request, Publication.objects.filter(status=Publication.PUBLISHED)).select_related('organization', 'audience_policy'))
        courses = list(active_organization_queryset(self.request, Course.objects.filter(state='published')).select_related('organization', 'audience_policy'))
        trails = list(active_organization_queryset(self.request, ContentTrail.objects.filter(status=ContentTrail.PUBLISHED)).select_related('organization', 'audience_policy'))
        audience_form = AudienceSimulationForm(self.request.GET or None)
        audience_keys = ('organization', 'companies', 'business_units', 'operational_units', 'channels', 'functions')
        audience_selected = any(self.request.GET.getlist(key) for key in audience_keys)
        if audience_selected and audience_form.is_valid():
            selected = AudienceSimulationView._selected_scope(audience_form)
            memberships = list(active_organization_queryset(self.request, Membership.objects.filter(active=True)).prefetch_related('channels', 'functions'))
            publications = [item for item in publications if AudienceSimulationView._impacted_users(item, memberships, selected) > 0]
            courses = [item for item in courses if AudienceSimulationView._impacted_users(item, memberships, selected) > 0]
            trails = [item for item in trails if AudienceSimulationView._impacted_users(item, memberships, selected) > 0]
        groups = []
        if kind in ('', 'feed', 'wiki'):
            groups.extend((item, item.kind, ContentType.objects.get_for_model(Publication)) for item in publications if not kind or item.kind == kind)
        if kind in ('', 'course'):
            groups.extend((item, 'course', ContentType.objects.get_for_model(Course)) for item in courses)
        if kind in ('', 'trail'):
            groups.extend((item, 'trail', ContentType.objects.get_for_model(ContentTrail)) for item in trails)
        events = ContentEvent.objects.filter(occurred_at__gte=cutoff)
        organization = active_organization(self.request)
        if organization:
            events = events.filter(organization=organization)
        rows = []
        for item, item_kind, content_type in groups:
            item_events = events.filter(content_type=content_type, object_id=item.pk)
            if item_kind in ('feed', 'wiki'):
                interaction = ContentInteraction.objects.filter(content_type=content_type, object_id=item.pk).aggregate(views=Sum('view_count'), readers=Count('user', distinct=True))
                reached = interaction['views'] or 0
                readers = interaction['readers'] or 0
                completed = item_events.filter(event_name=ContentEvent.CONTENT_ACKNOWLEDGED).count()
            elif item_kind == 'course':
                reached = item_events.filter(event_name=ContentEvent.COURSE_ENROLLED).count()
                readers = item_events.filter(event_name=ContentEvent.COURSE_ENROLLED).values('user_id').distinct().count()
                completed = item_events.filter(event_name=ContentEvent.COURSE_COMPLETED).count()
            else:
                reached = item_events.filter(event_name=ContentEvent.TRAIL_STARTED).count()
                readers = item_events.filter(event_name=ContentEvent.TRAIL_STARTED).values('user_id').distinct().count()
                completed = item_events.filter(event_name=ContentEvent.TRAIL_COMPLETED).count()
            rows.append({'item': item, 'kind': item_kind, 'reached': reached, 'readers': readers, 'completed': completed, 'active_seconds': item_events.aggregate(total=Sum('active_seconds'))['total'] or 0})
        context.update({'rows': rows, 'kind': kind, 'period': period, 'audience_form': audience_form, 'audience_selected': audience_selected, 'total_reached': sum(row['reached'] for row in rows), 'total_readers': sum(row['readers'] for row in rows), 'total_completed': sum(row['completed'] for row in rows)})
        return context


class LearningMetricsView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/learning_metrics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = active_organization_queryset(
            self.request,
            Course.objects.filter(state='published'),
        ).select_related('organization', 'subject').annotate(
            module_count=Count('modules', distinct=True),
            content_count=Count('modules__contents', distinct=True),
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(overview__icontains=query))
        content_type = ContentType.objects.get_for_model(Content)
        courses = []
        total_enrollments = total_completions = total_feedback = total_active = total_video_events = total_attachment_opens = total_helpful = total_not_helpful = courses_with_progress = 0
        for course in queryset.order_by('title'):
            content_ids = list(Content.objects.filter(module__course=course).values_list('pk', flat=True))
            events = ContentEvent.objects.filter(content_type=content_type, object_id__in=content_ids)
            enrollments = course.students.count()
            completions = events.filter(event_name=ContentEvent.CONTENT_COMPLETED).values('user_id').distinct().count()
            progress_users = events.filter(event_name=ContentEvent.CONTENT_ACTIVE).values('user_id').distinct().count()
            feedback = ContentFeedback.objects.filter(content_type=content_type, object_id__in=content_ids)
            helpful = feedback.filter(rating=ContentFeedback.HELPFUL).count()
            not_helpful = feedback.filter(rating=ContentFeedback.NOT_HELPFUL).count()
            active_seconds = events.aggregate(total=Sum('active_seconds')).get('total') or 0
            video_metrics = events.filter(event_name=ContentEvent.VIDEO_PROGRESS).aggregate(
                events=Count('id'), average_progress=Avg('progress_percent'),
            )
            attachment_opens = events.filter(event_name=ContentEvent.ATTACHMENT_OPENED).count()
            course.metric_enrollments = enrollments
            course.metric_completions = completions
            course.metric_feedback = feedback.count()
            course.metric_helpful_rate = round(helpful * 100 / course.metric_feedback) if course.metric_feedback else None
            course.metric_active_seconds = active_seconds
            course.metric_completion_rate = round(completions * 100 / enrollments) if enrollments else None
            course.metric_video_events = video_metrics['events'] or 0
            course.metric_video_progress = round(video_metrics['average_progress']) if video_metrics['average_progress'] is not None else None
            course.metric_attachment_opens = attachment_opens
            total_enrollments += enrollments
            total_completions += completions
            total_feedback += course.metric_feedback
            total_helpful += helpful
            total_not_helpful += not_helpful
            total_active += active_seconds
            total_video_events += course.metric_video_events
            total_attachment_opens += attachment_opens
            if progress_users > 0:
                courses_with_progress += 1
            courses.append(course)
        context.update({
            'courses': courses,
            'active_organization': active_organization(self.request),
            'filters': {'q': query},
            'total_courses': len(courses),
            'total_enrollments': total_enrollments,
            'total_completions': total_completions,
            'total_feedback': total_feedback,
            'total_active_seconds': total_active,
            'total_video_events': total_video_events,
            'total_attachment_opens': total_attachment_opens,
            'overall_completion_rate': round(total_completions * 100 / total_enrollments) if total_enrollments else None,
            'courses_with_progress': courses_with_progress,
            'course_helpful_rate': round(total_helpful * 100 / total_feedback) if total_feedback else None,
            'course_not_helpful_rate': round(total_not_helpful * 100 / total_feedback) if total_feedback else None,
        })
        return context


class TrailConsoleListView(ManagerRequiredMixin, ListView):
    """Governance view for versioned trails and their current adherence."""

    model = ContentTrail
    template_name = 'console/trail_list.html'
    context_object_name = 'trails'
    paginate_by = 20

    def get_queryset(self):
        queryset = active_organization_queryset(
            self.request,
            ContentTrail.objects.all(),
        ).annotate(
            step_count=Count('steps', distinct=True),
            assignment_count=Count('assignments', distinct=True),
            completed_count=Count('assignments', filter=Q(assignments__completed_at__isnull=False), distinct=True),
        ).order_by('title')
        query = self.request.GET.get('q', '').strip()
        trail_type = self.request.GET.get('type', '').strip()
        status = self.request.GET.get('status', '').strip()
        if query:
            search_filter = accent_insensitive_search('title', 'objective')
            queryset = search_filter(queryset, query)
        if trail_type in (ContentTrail.REQUIRED, ContentTrail.RECOMMENDED, ContentTrail.CONTEXTUAL):
            queryset = queryset.filter(trail_type=trail_type)
        if status in (ContentTrail.DRAFT, ContentTrail.PUBLISHED, ContentTrail.ARCHIVED):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        from collections import defaultdict
        from audience.models import AudienceRule
        from configuration.models import Company, BusinessUnit, OperationalUnit, BusinessChannel, JobFunction

        context = super().get_context_data(**kwargs)
        trails = context['trails']
        rules_by_trail = {}
        ids_by_dimension = defaultdict(set)

        for trail in trails:
            rules = list(trail.audience_policy.rules.all()) if trail.audience_policy else []
            rules_by_trail[trail.pk] = {rule.dimension: rule for rule in rules}
            for rule in rules:
                ids_by_dimension[rule.dimension].update(str(value) for value in rule.values)

        model_by_dimension = {
            AudienceRule.COMPANY: Company,
            AudienceRule.BUSINESS_UNIT: BusinessUnit,
            AudienceRule.OPERATIONAL_UNIT: OperationalUnit,
            AudienceRule.CHANNEL: BusinessChannel,
            AudienceRule.FUNCTION: JobFunction,
        }
        names_by_dimension = {}
        for dimension, model in model_by_dimension.items():
            names_by_dimension[dimension] = {
                str(item.pk): item.name
                for item in model.objects.filter(pk__in=ids_by_dimension[dimension])
            }

        for trail in trails:
            rules = rules_by_trail.get(trail.pk, {})
            organization = trail.organization or getattr(trail.audience_policy, 'organization', None)
            if not organization and not rules:
                trail.audience_levels = [{'label': 'Audiência', 'values': ['Todos os usuários'], 'all': True}]
                continue

            levels = [{'label': 'Organização', 'values': [organization.name] if organization else ['*'], 'all': not organization}]
            for dimension, label in (
                (AudienceRule.COMPANY, 'Empresa'),
                (AudienceRule.BUSINESS_UNIT, 'Business unit'),
                (AudienceRule.OPERATIONAL_UNIT, 'Unidade operacional'),
                (AudienceRule.CHANNEL, 'Canal'),
                (AudienceRule.FUNCTION, 'Função'),
            ):
                rule = rules.get(dimension)
                values = [names_by_dimension[dimension].get(str(value), f'#{value}') for value in rule.values] if rule else ['*']
                levels.append({'label': label, 'values': values, 'all': not rule})
            trail.audience_levels = levels

        context.update({
            'active_organization': active_organization(self.request),
            'filters': {
                'q': self.request.GET.get('q', ''),
                'type': self.request.GET.get('type', ''),
                'status': self.request.GET.get('status', ''),
            },
            'trail_total': self.get_queryset().count(),
            'published_total': self.get_queryset().filter(status=ContentTrail.PUBLISHED).count(),
            'assignment_total': sum(item.assignment_count for item in trails),
            'completed_total': sum(item.completed_count for item in trails),
        })
        return context


class TrailProgressView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/trail_progress.html'

    def get_trail(self):
        return get_object_or_404(
            active_organization_queryset(self.request, ContentTrail.objects.all()),
            pk=self.kwargs['pk'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trail = self.get_trail()
        total = trail.steps.count()
        assignments = list(trail.assignments.select_related('user', 'audience_policy').prefetch_related('progress'))
        query = self.request.GET.get('q', '').strip().lower()
        status = self.request.GET.get('status', '').strip()
        all_assignments = assignments
        step_stats = []
        for step in trail.steps.all():
            completed = sum(
                item.progress.filter(step=step, completed_at__isnull=False).exists()
                for item in all_assignments
            )
            step_stats.append({
                'step': step,
                'completed': completed,
                'pending': max(0, len(all_assignments) - completed),
                'completion_rate': round(completed * 100 / len(all_assignments)) if all_assignments else 0,
            })
        return_events = ContentEvent.objects.filter(
            event_name=ContentEvent.TRAIL_STEP_COMPLETED,
            metadata__trail_id=trail.pk,
            user__isnull=False,
        ).values('user_id').annotate(total=Count('id')).filter(total__gt=1).count()
        for assignment in assignments:
            completed = sum(progress.completed_at is not None for progress in assignment.progress.all())
            assignment.progress_completed = completed
            assignment.progress_total = total
            assignment.progress_percent = round(completed * 100 / total) if total else 0
            if assignment.revoked_at:
                assignment.progress_status = 'revoked'
            else:
                assignment.progress_status = 'completed' if assignment.completed_at else ('started' if completed else 'pending')
            assignment.progress_last_activity = max(
                [assignment.started_at] + [progress.completed_at for progress in assignment.progress.all() if progress.completed_at],
                default=None,
            )
            assignment.is_abandoned = bool(
                assignment.progress_status == 'started'
                and assignment.progress_last_activity
                and assignment.progress_last_activity < timezone.now() - timezone.timedelta(days=30)
            )
            if assignment.is_abandoned:
                assignment.progress_status = 'abandoned'
        assignments = [item for item in assignments if not query or query in (item.user.get_username().lower() if item.user else '')]
        if status in ('pending', 'started', 'abandoned', 'completed', 'revoked'):
            assignments = [item for item in assignments if item.progress_status == status]
        context.update({
            'trail': trail,
            'assignments': assignments,
            'filters': {'q': self.request.GET.get('q', ''), 'status': status},
            'total_assignments': len(assignments),
            'completed_assignments': sum(item.progress_status == 'completed' for item in assignments),
            'started_assignments': sum(item.progress_status == 'started' for item in assignments),
            'pending_assignments': sum(item.progress_status == 'pending' for item in assignments),
            'abandoned_assignments': sum(item.progress_status == 'abandoned' for item in assignments),
            'revoked_assignments': sum(item.progress_status == 'revoked' for item in assignments),
            'step_stats': step_stats,
            'returning_users': return_events,
        })
        return context


class TrailAssignmentCreateView(ManagerRequiredMixin, CreateView):
    model = TrailAssignment
    form_class = TrailAssignmentForm
    template_name = 'console/trail_assignment_form.html'
    success_url = reverse_lazy('console:trail-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        organization = active_organization(self.request)
        if organization:
            form.fields['trail'].queryset = ContentTrail.objects.filter(
                Q(organization=organization) | Q(organization__isnull=True),
                status=ContentTrail.PUBLISHED,
            )
            form.fields['audience_policy'].queryset = AudiencePolicy.objects.filter(
                Q(organization=organization) | Q(organization__isnull=True), active=True,
            )
            form.fields['user'].queryset = User.objects.filter(
                memberships__organization=organization,
                memberships__active=True,
            ).distinct().order_by('username')
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Atribuição da trilha criada com sucesso.')
        return super().form_valid(form)


class AudienceImpactView(ManagerRequiredMixin, View):
    def get(self, request):
        policy = get_object_or_404(AudiencePolicy, pk=request.GET.get('policy'))
        organization = active_organization(request)
        impact = estimate_policy_reach(policy, organization_id=organization.pk if organization else None)
        return JsonResponse({'ok': True, **impact})


class TrailEditorView(ManagerRequiredMixin, View):
    template_name = 'console/trail_form.html'

    def get_object(self):
        pk = self.kwargs.get('pk')
        if not pk:
            return ContentTrail(owner=self.request.user)
        queryset = active_organization_queryset(self.request, ContentTrail.objects.all())
        return get_object_or_404(queryset, pk=pk)

    def get_target_options(self):
        organization = active_organization(self.request)
        publications = active_organization_queryset(
            self.request, Publication.objects.filter(status=Publication.PUBLISHED)
        ).order_by('kind', 'title')
        courses = active_organization_queryset(
            self.request, Course.objects.filter(state='published')
        ).select_related('subject').order_by('title')
        contents = Content.objects.filter(module__course__in=courses).select_related(
            'module', 'module__course', 'content_type'
        ).order_by('module__course__title', 'module__order', 'order')
        options = []
        for item in publications:
            options.append({
                'value': f'publication:{item.pk}',
                'label': f'{item.get_kind_display()} · {item.title}',
                'group': 'Publicações',
            })
        for item in courses:
            options.append({
                'value': f'course:{item.pk}',
                'label': f'Curso · {item.title}',
                'group': 'Cursos',
            })
        for item in contents:
            options.append({
                'value': f'content:{item.pk}',
                'label': f'Conteúdo · {item.module.course.title} / {item.module.title} / {item.item}',
                'group': 'Conteúdos de cursos',
            })
        return options

    def resolve_target(self, value):
        try:
            kind, raw_id = value.split(':', 1)
            object_id = int(raw_id)
        except (AttributeError, ValueError):
            return None
        if kind == 'publication':
            return active_organization_queryset(self.request, Publication.objects.filter(status=Publication.PUBLISHED)).filter(pk=object_id).first()
        if kind == 'course':
            return active_organization_queryset(self.request, Course.objects.filter(state='published')).filter(pk=object_id).first()
        if kind == 'content':
            return Content.objects.filter(pk=object_id, module__course__in=active_organization_queryset(self.request, Course.objects.all())).first()
        return None

    def context(self, form, trail, selected_steps):
        organization = active_organization(self.request)
        return {
            'form': form,
            'trail': trail,
            'target_options': self.get_target_options(),
            'selected_steps': selected_steps,
            'selected_prerequisites': getattr(self, '_selected_prerequisites', []),
            'active_organization': organization,
        }

    def get(self, request, *args, **kwargs):
        trail = self.get_object()
        organization = active_organization(request)
        form = TrailForm(
            instance=trail,
            organization_queryset=Organization.objects.filter(pk=organization.pk) if organization else Organization.objects.all(),
        )
        if trail.pk:
            steps = list(trail.steps.order_by('position', 'id'))
            selected_steps = [
                f'{step.content_type.model}:{step.object_id}'
                for step in steps
            ]
            step_ids = [step.pk for step in steps]
            self._selected_prerequisites = [
                step_ids.index(step.prerequisite_id) + 1 if step.prerequisite_id in step_ids else 0
                for step in steps
            ]
        else:
            selected_steps = []
            self._selected_prerequisites = []
        return render(request, self.template_name, self.context(form, trail, selected_steps))

    def post(self, request, *args, **kwargs):
        trail = self.get_object()
        organization = active_organization(request)
        form = TrailForm(
            request.POST,
            instance=trail,
            organization_queryset=Organization.objects.filter(pk=organization.pk) if organization else Organization.objects.all(),
        )
        raw_steps = [value for value in request.POST.getlist('step_content') if value]
        raw_prerequisites = request.POST.getlist('step_prerequisite')
        prerequisite_indexes = []
        for index, value in enumerate(raw_prerequisites):
            try:
                prerequisite = int(value or 0)
            except ValueError:
                prerequisite = 0
            prerequisite_indexes.append(prerequisite if 0 < prerequisite <= index else 0)
        targets = [self.resolve_target(value) for value in raw_steps]
        targets = [target for target in targets if target is not None]
        if len(targets) != len(raw_steps):
            form.add_error(None, 'Uma ou mais etapas não pertencem à organização ativa ou não estão publicadas.')
        if form.is_valid() and (targets or form.cleaned_data.get('status') != ContentTrail.PUBLISHED):
            trail = form.save(commit=False)
            trail.owner = trail.owner_id and trail.owner or request.user
            if not trail.organization and organization:
                trail.organization = organization
            trail.save()
            trail.steps.all().delete()
            for position, target in enumerate(targets):
                TrailStep.objects.create(
                    trail=trail,
                    position=position,
                    title=str(target),
                    content_type=ContentType.objects.get_for_model(target),
                    object_id=target.pk,
                    required=trail.trail_type == ContentTrail.REQUIRED,
                    completion_event=ContentEvent.CONTENT_COMPLETED if isinstance(target, Content) else ContentEvent.CONTENT_OPENED,
                )
            created_steps = list(trail.steps.order_by('position', 'id'))
            for index, prerequisite_index in enumerate(prerequisite_indexes[:len(created_steps)]):
                if prerequisite_index:
                    created_steps[index].prerequisite = created_steps[prerequisite_index - 1]
                    created_steps[index].save(update_fields=('prerequisite',))
            messages.success(request, 'Trilha salva com sucesso.')
            return redirect('console:trail-list')
        if form.is_valid() and not targets:
            form.add_error(None, 'Uma trilha publicada precisa ter pelo menos uma etapa.')
        self._selected_prerequisites = prerequisite_indexes or [0]
        return render(request, self.template_name, self.context(form, trail, raw_steps or ['']))


class AudienceSimulationView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/audience_simulation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = AudienceSimulationForm(self.request.GET or None)
        results = []
        context['active_organization'] = active_organization(self.request)
        if self.request.GET:
            form.is_valid()
            selected = self._selected_scope(form)
            memberships = list(
                active_organization_queryset(self.request, Membership.objects.filter(active=True))
                .select_related('user', 'organization', 'company', 'business_unit', 'operational_unit')
                .prefetch_related('channels', 'functions')
            )
            publications = active_organization_queryset(self.request, Publication.objects.filter(
                status=Publication.PUBLISHED
            )).select_related('organization', 'audience_policy').prefetch_related('audience_policy__rules')
            courses = active_organization_queryset(self.request, Course.objects.filter(
                state='published'
            )).select_related('organization', 'audience_policy').prefetch_related('audience_policy__rules')
            for item in list(publications) + list(courses):
                if isinstance(item, Publication) and not item.is_published:
                    continue
                if isinstance(item, Course):
                    now = timezone.now()
                    if (item.go_live_at and item.go_live_at > now) or (item.expire_at and item.expire_at <= now):
                        continue
                if self._matches(item, selected):
                    is_course = isinstance(item, Course)
                    results.append({
                        'kind': 'Curso' if is_course else item.get_kind_display(),
                        'title': item.title,
                        'organization': item.organization,
                        'url': item.get_absolute_url() if hasattr(item, 'get_absolute_url') else (
                            f'/course/{item.slug}/' if is_course else (
                                f'/feed/{item.slug}/' if item.kind == Publication.FEED else f'/wiki/{item.slug}/'
                            )
                        ),
                        'policy': item.audience_policy,
                        'impacted_users': self._impacted_users(item, memberships, selected),
                        'impacted_companies': self._impacted_companies(item, memberships, selected),
                    })
        context.update({'form': form, 'results': results, 'has_selection': bool(self.request.GET)})
        return context

    @staticmethod
    def _selected_scope(form):
        values = {
            'organization': {str(form.cleaned_data['organization'].pk)} if form.cleaned_data.get('organization') else set(),
            'company': {str(item.pk) for item in form.cleaned_data.get('companies', [])},
            'business_unit': {str(item.pk) for item in form.cleaned_data.get('business_units', [])},
            'operational_unit': {str(item.pk) for item in form.cleaned_data.get('operational_units', [])},
            'channel': {str(item.pk) for item in form.cleaned_data.get('channels', [])},
            'function': {str(item.pk) for item in form.cleaned_data.get('functions', [])},
        }
        units = BusinessUnit.objects.filter(pk__in=values['business_unit'])
        operational = OperationalUnit.objects.filter(pk__in=values['operational_unit']).select_related('business_unit')
        channels = BusinessChannel.objects.filter(pk__in=values['channel'])
        functions = JobFunction.objects.filter(pk__in=values['function']).prefetch_related('channels')
        values['company'].update(str(item.company_id) for item in units)
        values['business_unit'].update(str(item.business_unit_id) for item in operational)
        values['company'].update(str(item.business_unit.company_id) for item in operational)
        values['company'].update(str(item.company_id) for item in channels)
        values['company'].update(str(item.company_id) for item in functions)
        values['channel'].update(str(channel.pk) for item in functions for channel in item.channels.all())
        return values

    @staticmethod
    def _matches(item, selected):
        organization_id = getattr(item, 'organization_id', None) or getattr(item.audience_policy, 'organization_id', None)
        if selected['organization'] and str(organization_id) not in selected['organization']:
            return False
        policy = item.audience_policy
        if not policy or not policy.active:
            return True
        rule_results = []
        for rule in policy.rules.all():
            expected = {str(value) for value in rule.values}
            available = selected.get(rule.dimension, set())
            rule_results.append(not available or bool(available.intersection(expected)))
        return any(rule_results) if policy.match_mode == policy.ANY else all(rule_results)

    @staticmethod
    def _membership_in_scope(membership, selected):
        checks = {
            'organization': {str(membership.organization_id)},
            'company': {str(membership.company_id)},
            'business_unit': {str(membership.business_unit_id)} if membership.business_unit_id else set(),
            'operational_unit': {str(membership.operational_unit_id)} if membership.operational_unit_id else set(),
            'channel': {str(item.pk) for item in membership.channels.all()},
            'function': {str(item.pk) for item in membership.functions.all()},
        }
        return all(not expected or checks[key].intersection(expected) for key, expected in selected.items())

    @classmethod
    def _impacted_users(cls, content, memberships, selected):
        return len({membership.user_id for membership in memberships if cls._membership_in_scope(membership, selected) and cls._membership_matches_content(membership, content)})

    @classmethod
    def _impacted_companies(cls, content, memberships, selected):
        return len({membership.company_id for membership in memberships if cls._membership_in_scope(membership, selected) and cls._membership_matches_content(membership, content)})

    @staticmethod
    def _membership_matches_content(membership, content):
        organization_id = getattr(content, 'organization_id', None) or getattr(content.audience_policy, 'organization_id', None)
        if organization_id and membership.organization_id != organization_id:
            return False
        policy = content.audience_policy
        if not policy or not policy.active or not policy.rules.exists():
            return True

        def rule_matches(rule):
            if rule.dimension == AudienceRule.TENANT:
                values = {str(membership.organization_id)}
            elif rule.dimension == AudienceRule.COMPANY:
                values = {str(membership.company_id)}
            elif rule.dimension == AudienceRule.BUSINESS_UNIT:
                values = {str(membership.business_unit_id)} if membership.business_unit_id else set()
            elif rule.dimension == AudienceRule.OPERATIONAL_UNIT:
                values = {str(membership.operational_unit_id)} if membership.operational_unit_id else set()
            elif rule.dimension == AudienceRule.CHANNEL:
                values = {str(item.pk) for item in membership.channels.all()}
            else:
                values = {str(item.pk) for item in membership.functions.all()}
            matched = bool(values.intersection(str(value) for value in rule.values))
            return not matched if rule.negate else matched

        results = [rule_matches(rule) for rule in policy.rules.all()]
        return any(results) if policy.match_mode == policy.ANY else all(results)


class MembershipAssignmentView(ManagerRequiredMixin, View):
    template_name = 'console/membership_assignment.html'

    def get(self, request, *args, **kwargs):
        return self.render(request, self.build_form(request))

    def post(self, request, *args, **kwargs):
        if request.FILES.get('csv_file'):
            return self.import_csv(request)
        form = MembershipAssignmentForm(request.POST, user_queryset=self.user_queryset(request))
        if form.is_valid():
            data = form.cleaned_data
            units = list(data['business_units'])
            operational = list(data['operational_units'])
            combos = []
            if operational:
                combos = [(item.business_unit.company, item.business_unit, item) for item in operational]
            elif units:
                combos = [(item.company, item, None) for item in units]
            else:
                combos = [(item, None, None) for item in data['companies']]
            created = 0
            for user in data['users']:
                for company, business_unit, operational_unit in combos:
                    membership, _ = Membership.objects.update_or_create(
                        user=user, company=company, business_unit=business_unit,
                        operational_unit=operational_unit,
                        defaults={'organization': data['organization'], 'person_type': data.get('person_type'), 'active': True},
                    )
                    functions = [item for item in data['functions'] if item.company_id == company.pk]
                    channels = [item for item in data['channels'] if item.company_id == company.pk]
                    membership.functions.set(functions)
                    membership.channels.set(channels)
                    created += 1
            messages.success(request, f'{created} associação(ões) de usuário atualizada(s) com sucesso.')
            return redirect('console:assignment')
        return self.render(request, form)

    def render(self, request, form):
        from django.shortcuts import render
        return render(request, self.template_name, {
            'form': form,
            'user_filter_query': request.GET.get('q', ''),
            'user_filter_organization': request.GET.get('user_organization', ''),
            'user_filter_company': request.GET.get('user_company', ''),
            'filtered_users': self.user_queryset(request),
            'organizations': Organization.objects.filter(active=True),
            'companies': Company.objects.filter(active=True).select_related('organization'),
        })

    @staticmethod
    def user_queryset(request):
        queryset = User.objects.filter(is_active=True).prefetch_related(
            'memberships__organization', 'memberships__company'
        ).order_by('username')
        query = request.GET.get('q', '').strip()
        organization = request.GET.get('user_organization', '').strip()
        company = request.GET.get('user_company', '').strip()
        if query:
            queryset = queryset.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
        if organization:
            queryset = queryset.filter(memberships__organization_id=organization)
        if company:
            queryset = queryset.filter(memberships__company_id=company)
        return queryset.distinct()

    def build_form(self, request):
        return MembershipAssignmentForm(
            user_queryset=self.user_queryset(request)
        )

    @transaction.atomic
    def import_csv(self, request):
        try:
            decoded = request.FILES['csv_file'].read().decode('utf-8-sig')
            rows = csv.DictReader(io.StringIO(decoded))
            required = {'username', 'organization', 'company'}
            if not required.issubset(set(rows.fieldnames or [])):
                messages.error(request, 'CSV deve conter pelo menos: username, organization e company.')
                return self.render(request, self.build_form(request))
            imported = 0
            for row in rows:
                username = (row.get('username') or '').strip()
                if not username:
                    continue
                organization = self.lookup(Organization, row.get('organization'))
                company = self.lookup(Company, row.get('company'))
                if not organization or not company or company.organization_id != organization.pk:
                    continue
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': (row.get('email') or '').strip(),
                        'first_name': (row.get('first_name') or '').strip(),
                        'last_name': (row.get('last_name') or '').strip(),
                    },
                )
                if row.get('email') and not user.email:
                    user.email = row['email'].strip()
                if row.get('first_name'):
                    user.first_name = row['first_name'].strip()
                if row.get('last_name'):
                    user.last_name = row['last_name'].strip()
                user.save(update_fields=['email', 'first_name', 'last_name'])
                business_unit = self.lookup(BusinessUnit, row.get('business_unit'))
                operational_unit = self.lookup(OperationalUnit, row.get('operational_unit'))
                if business_unit and business_unit.company_id != company.pk:
                    business_unit = None
                if operational_unit and (not business_unit or operational_unit.business_unit_id != business_unit.pk):
                    operational_unit = None
                person_type = self.lookup(PersonType, row.get('person_type'))
                if person_type and person_type.organization_id != organization.pk:
                    person_type = None
                membership, _ = Membership.objects.update_or_create(
                    user=user, company=company, business_unit=business_unit, operational_unit=operational_unit,
                    defaults={'organization': organization, 'person_type': person_type, 'active': True},
                )
                membership.functions.set(self.lookup_many(JobFunction, row.get('functions'), company.pk))
                membership.channels.set(self.lookup_many(BusinessChannel, row.get('channels'), company.pk))
                imported += 1
            messages.success(request, f'{imported} usuário(s) importado(s) e associado(s).')
        except UnicodeDecodeError:
            messages.error(request, 'Não foi possível ler o CSV. Salve o arquivo em UTF-8.')
        return redirect('console:assignment')

    @staticmethod
    def lookup(model, value):
        value = (value or '').strip()
        if not value:
            return None
        return model.objects.filter(Q(pk=value) | Q(name__iexact=value)).first()

    @staticmethod
    def lookup_many(model, value, company_id):
        names = [item.strip() for item in (value or '').replace(';', ',').split(',') if item.strip()]
        if not names:
            return []
        return model.objects.filter(company_id=company_id).filter(Q(pk__in=names) | Q(name__in=names))

    @staticmethod
    def _membership_in_scope(membership, selected):
        checks = {
            'organization': {str(membership.organization_id)},
            'company': {str(membership.company_id)},
            'business_unit': {str(membership.business_unit_id)} if membership.business_unit_id else set(),
            'operational_unit': {str(membership.operational_unit_id)} if membership.operational_unit_id else set(),
            'channel': {str(item.pk) for item in membership.channels.all()},
            'function': {str(item.pk) for item in membership.functions.all()},
        }
        return all(not expected or checks[key].intersection(expected) for key, expected in selected.items())

    @classmethod
    def _impacted_users(cls, content, memberships, selected):
        impacted = set()
        for membership in memberships:
            if not cls._membership_in_scope(membership, selected):
                continue
            if cls._membership_matches_content(membership, content):
                impacted.add(membership.user_id)
        return len(impacted)

    @classmethod
    def _impacted_companies(cls, content, memberships, selected):
        impacted = set()
        for membership in memberships:
            if cls._membership_in_scope(membership, selected) and cls._membership_matches_content(membership, content):
                impacted.add(membership.company_id)
        return len(impacted)

    @staticmethod
    def _membership_matches_content(membership, content):
        organization_id = getattr(content, 'organization_id', None) or getattr(content.audience_policy, 'organization_id', None)
        if organization_id and membership.organization_id != organization_id:
            return False
        policy = content.audience_policy
        if not policy or not policy.active or not policy.rules.exists():
            return True

        def rule_matches(rule):
            if rule.dimension == AudienceRule.TENANT:
                values = {str(membership.organization_id)}
            elif rule.dimension == AudienceRule.COMPANY:
                values = {str(membership.company_id)}
            elif rule.dimension == AudienceRule.BUSINESS_UNIT:
                values = {str(membership.business_unit_id)} if membership.business_unit_id else set()
            elif rule.dimension == AudienceRule.OPERATIONAL_UNIT:
                values = {str(membership.operational_unit_id)} if membership.operational_unit_id else set()
            elif rule.dimension == AudienceRule.CHANNEL:
                values = {str(item.pk) for item in membership.channels.all()}
            else:
                values = {str(item.pk) for item in membership.functions.all()}
            matched = bool(values.intersection(str(value) for value in rule.values))
            return not matched if rule.negate else matched

        results = [rule_matches(rule) for rule in policy.rules.all()]
        return any(results) if policy.match_mode == policy.ANY else all(results)


class CourseConsoleListView(ManagerRequiredMixin, ListView):
    model = Course
    template_name = 'console/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        queryset = active_organization_queryset(self.request, Course.objects).select_related('organization', 'subject', 'audience_policy').prefetch_related('audience_policy__rules').annotate(module_count=Count('modules')).order_by('-created')
        query = self.request.GET.get('q', '').strip()
        state = self.request.GET.get('state', '').strip()
        if query:
            search_filter = accent_insensitive_search('title', 'overview')
            queryset = search_filter(queryset, query)
        if state in ('published', 'unpublished'):
            queryset = queryset.filter(state=state)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_organization'] = active_organization(self.request)
        courses_page = context['courses']
        courses = list(getattr(courses_page, 'object_list', courses_page))
        rules_by_course = {}
        ids_by_dimension = defaultdict(set)

        for course in courses:
            rules = list(course.audience_policy.rules.all()) if course.audience_policy else []
            rules_by_course[course.pk] = {rule.dimension: rule for rule in rules}
            for rule in rules:
                ids_by_dimension[rule.dimension].update(str(value) for value in rule.values)

        model_by_dimension = {
            AudienceRule.COMPANY: Company,
            AudienceRule.BUSINESS_UNIT: BusinessUnit,
            AudienceRule.OPERATIONAL_UNIT: OperationalUnit,
            AudienceRule.CHANNEL: BusinessChannel,
            AudienceRule.FUNCTION: JobFunction,
        }
        names_by_dimension = {}
        for dimension, model in model_by_dimension.items():
            names_by_dimension[dimension] = {
                str(item.pk): item.name
                for item in model.objects.filter(pk__in=ids_by_dimension[dimension])
            }

        for course in courses:
            rules = rules_by_course.get(course.pk, {})
            organization = course.organization or getattr(course.audience_policy, 'organization', None)
            if not organization and not rules:
                course.audience_levels = [{'label': 'Audiência', 'values': ['Todos os usuários'], 'all': True}]
                continue

            levels = [{'label': 'Organização', 'values': [organization.name] if organization else ['*'], 'all': not organization}]
            for dimension, label in (
                (AudienceRule.COMPANY, 'Empresa'),
                (AudienceRule.BUSINESS_UNIT, 'Business unit'),
                (AudienceRule.OPERATIONAL_UNIT, 'Unidade operacional'),
                (AudienceRule.CHANNEL, 'Canal'),
                (AudienceRule.FUNCTION, 'Função'),
            ):
                rule = rules.get(dimension)
                values = [names_by_dimension[dimension].get(str(value), f'#{value}') for value in rule.values] if rule else ['*']
                levels.append({'label': label, 'values': values, 'all': not rule})
            course.audience_levels = levels
        return context


class CourseConsoleCreateView(ManagerRequiredMixin, CreateView):
    model = Course
    form_class = CourseConsoleForm
    template_name = 'console/course_form.html'
    success_url = reverse_lazy('console:course-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organization = active_organization(self.request)
        if organization:
            kwargs['organization_queryset'] = Organization.objects.filter(pk=organization.pk)
            kwargs['documents_queryset'] = Document.objects.filter(
                status=Document.PUBLISHED,
            ).filter(Q(organization=organization) | Q(organization__isnull=True)).distinct()
            kwargs.setdefault('initial', {})['organization'] = organization.pk
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.author = self.request.user
        messages.success(self.request, 'Curso salvo com sucesso.')
        return super().form_valid(form)


class CourseConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = Course
    form_class = CourseConsoleForm
    template_name = 'console/course_form.html'
    success_url = reverse_lazy('console:course-list')

    def get_queryset(self):
        return active_organization_queryset(self.request, super().get_queryset())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organization = active_organization(self.request)
        if organization:
            kwargs['organization_queryset'] = Organization.objects.filter(pk=organization.pk)
            kwargs['documents_queryset'] = Document.objects.filter(
                status=Document.PUBLISHED,
            ).filter(Q(organization=organization) | Q(organization__isnull=True)).distinct()
        return kwargs



class OrganizationSettingsView(ManagerRequiredMixin, View):
    template_name = 'console/organization_settings.html'

    def get_organization(self, request):
        organization_id = request.GET.get('organization') or request.POST.get('organization')
        queryset = Organization.objects.filter(active=True).order_by('name')
        return get_object_or_404(queryset, pk=organization_id) if organization_id else queryset.first()

    def render_page(self, request, organization, terminology_form=None, person_type_form=None):
        terminology = getattr(organization, 'terminology', None) if organization else None
        if terminology_form is None:
            terminology_form = OrganizationTerminologyForm(instance=terminology)
        if person_type_form is None:
            person_type = get_object_or_404(organization.person_types, pk=request.GET.get('edit_person_type')) if organization and request.GET.get('edit_person_type') else None
            person_type_form = PersonTypeForm(instance=person_type)
        return render(request, self.template_name, {
            'organizations': Organization.objects.filter(active=True).order_by('name'),
            'organization': organization,
            'terminology_form': terminology_form,
            'person_type_form': person_type_form,
            'person_types': organization.person_types.all() if organization else [],
            'editing_person_type': getattr(person_type_form.instance, 'pk', None),
        })

    def get(self, request, *args, **kwargs):
        return self.render_page(request, self.get_organization(request))

    def post(self, request, *args, **kwargs):
        organization = self.get_organization(request)
        if not organization:
            return redirect('console:organization-settings')
        if request.POST.get('action') == 'terminology':
            terminology, _ = OrganizationTerminology.objects.get_or_create(organization=organization)
            form = OrganizationTerminologyForm(request.POST, instance=terminology)
            if form.is_valid():
                form.save()
                messages.success(request, 'Rótulos e descrições atualizados.')
                return redirect(f'{reverse_lazy("console:organization-settings")}?organization={organization.pk}')
            return self.render_page(request, organization, terminology_form=form)
        person_type_id = request.POST.get('person_type_id')
        person_type = get_object_or_404(organization.person_types, pk=person_type_id) if person_type_id else None
        form = PersonTypeForm(request.POST, instance=person_type)
        if form.is_valid():
            person_type = form.save(commit=False)
            person_type.organization = organization
            person_type.save()
            messages.success(request, 'Tipo de pessoa atualizado.' if person_type else 'Tipo de pessoa adicionado.')
            return redirect(f'{reverse_lazy("console:organization-settings")}?organization={organization.pk}')
        return self.render_page(request, organization, person_type_form=form)


class UserConsoleListView(ManagerRequiredMixin, ListView):
    model = User
    template_name = 'console/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        organization = active_organization(self.request)
        if organization:
            queryset = User.objects.filter(
                memberships__organization=organization,
                memberships__active=True,
            ).distinct().prefetch_related('memberships__company', 'memberships__business_unit')
        else:
            queryset = User.objects.prefetch_related('memberships__company', 'memberships__business_unit')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(username__icontains=query) | Q(email__icontains=query))
        return queryset.order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = active_organization(self.request)
        if organization:
            org_users = User.objects.filter(
                memberships__organization=organization,
                memberships__active=True,
            ).distinct()
            context['user_total'] = org_users.count()
            context['active_total'] = org_users.filter(is_active=True).count()
            context['inactive_total'] = org_users.filter(is_active=False).count()
        else:
            context['user_total'] = User.objects.count()
            context['active_total'] = User.objects.filter(is_active=True).count()
            context['inactive_total'] = User.objects.filter(is_active=False).count()
        context['active_organization'] = organization
        return context


class UserConsoleFormView(ManagerRequiredMixin, View):
    template_name = 'console/user_form.html'

    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(User, pk=pk) if pk else User()

    def get_forms(self, request=None):
        user = self.get_object()
        post_data = request.POST if request is not None else None
        user_form = ConsoleUserForm(post_data, instance=user, prefix='user')
        membership_formset = forms.inlineformset_factory(
            User, Membership, form=MembershipForm, extra=1, can_delete=True
        )(post_data, instance=user, prefix='memberships')
        return user, user_form, membership_formset

    def get(self, request, *args, **kwargs):
        return self.render_forms(*self.get_forms())

    def post(self, request, *args, **kwargs):
        user, user_form, membership_formset = self.get_forms(request)
        is_new = not user.pk
        if user_form.is_valid() and membership_formset.is_valid():
            user = user_form.save()
            if is_new:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            membership_formset.instance = user
            membership_formset.save()
            messages.success(request, 'Usuário e associação salvos com sucesso.')
            return redirect('console:user-list')
        return self.render_forms(user, user_form, membership_formset)

    def render_forms(self, user, user_form, membership_formset):
        from django.shortcuts import render
        return render(self.request, self.template_name, {
            'object': user, 'form': user_form, 'membership_formset': membership_formset,
        })


class UserConsoleCreateView(UserConsoleFormView):
    pass


class UserConsoleUpdateView(UserConsoleFormView):
    def dispatch(self, request, *args, **kwargs):
        target = self.get_object()
        if not management_access.can_manage_user(request.user, target):
            return HttpResponseForbidden('Você não possui escopo para administrar este usuário.')
        return super().dispatch(request, *args, **kwargs)


class ManagementAssignmentListView(ManagerRequiredMixin, ListView):
    model = ManagementAssignment
    template_name = 'console/management_assignment_list.html'
    context_object_name = 'assignments'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Somente superusuários podem definir gestores.')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ManagementAssignment.objects.select_related(
            'user', 'organization', 'company', 'business_unit', 'operational_unit'
        )


class ManagementAssignmentFormView(ManagerRequiredMixin, View):
    template_name = 'console/management_assignment_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Somente superusuários podem definir gestores.')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        assignment = get_object_or_404(ManagementAssignment, pk=kwargs['pk']) if kwargs.get('pk') else None
        return self.render(request, ManagementAssignmentForm(instance=assignment), assignment)

    def post(self, request, *args, **kwargs):
        assignment = get_object_or_404(ManagementAssignment, pk=kwargs['pk']) if kwargs.get('pk') else None
        form = ManagementAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Escopo de gestão salvo com sucesso.')
            return redirect('console:management-assignments')
        return self.render(request, form, assignment)

    def render(self, request, form, assignment):
        from django.shortcuts import render
        return render(request, self.template_name, {'form': form, 'assignment': assignment})


class ManagementReportView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/management_report.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not management_access.can_view_reports(request.user):
            return HttpResponseForbidden('Você não possui permissão para visualizar relatórios.')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = ManagementAssignment.objects.filter(active=True)
        if not self.request.user.is_superuser:
            assignments = assignments.filter(user=self.request.user, role__in=('people_admin', 'report_viewer'))
        memberships = Membership.objects.filter(active=True).select_related(
            'user', 'organization', 'company', 'business_unit', 'operational_unit'
        ).prefetch_related('functions', 'channels')
        if not self.request.user.is_superuser:
            scopes = []
            for assignment in assignments:
                assignment_scope = Q(organization_id=assignment.organization_id)
                if assignment.company_id:
                    assignment_scope &= Q(company_id=assignment.company_id)
                if assignment.business_unit_id:
                    assignment_scope &= Q(business_unit_id=assignment.business_unit_id)
                if assignment.operational_unit_id:
                    assignment_scope &= Q(operational_unit_id=assignment.operational_unit_id)
                scopes.append(assignment_scope)
            scope = Q()
            for assignment_scope in scopes:
                scope |= assignment_scope
            memberships = memberships.filter(scope) if scopes else memberships.none()
        context.update({
            'assignments': assignments,
            'memberships': memberships,
            'user_count': memberships.values('user_id').distinct().count(),
            'company_count': memberships.values('company_id').distinct().count(),
        })
        return context
