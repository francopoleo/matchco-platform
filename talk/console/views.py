import csv
import io
from collections import defaultdict
from functools import wraps

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from audience.models import AudiencePolicy, AudienceRule
from configuration.models import (
    BusinessChannel, BusinessUnit, Company, JobFunction, ManagementAssignment, Membership,
    OperationalUnit, Organization,
)
from configuration.services import management_access
from courses.models import Course
from publishing.models import Publication

from .forms import (
    AudiencePolicyForm, AudienceRuleForm, AudienceSimulationForm, ConsoleUserForm, CourseConsoleForm,
    ManagementAssignmentForm, MembershipAssignmentForm,
    MembershipForm, PublicationForm,
)

User = get_user_model()


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
        context.update({
            'publication_count': Publication.objects.count(),
            'published_count': Publication.objects.filter(status=Publication.PUBLISHED).count(),
            'policy_count': AudiencePolicy.objects.count(),
            'course_count': Course.objects.filter(type='course').count(),
            'user_count': User.objects.count(),
            'rule_count': AudienceRule.objects.count(),
            'publication_by_kind': Publication.objects.values('kind').annotate(total=Count('id')),
        })
        return context


class PublicationConsoleListView(ManagerRequiredMixin, ListView):
    model = Publication
    template_name = 'console/publication_list.html'
    context_object_name = 'publications'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'author', 'organization', 'audience_policy'
        ).prefetch_related('audience_policy__rules')
        query = self.request.GET.get('q', '').strip()
        kind = self.request.GET.get('kind', '').strip()
        status = self.request.GET.get('status', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query)
        if kind in (Publication.FEED, Publication.WIKI):
            queryset = queryset.filter(kind=kind)
        if status in (Publication.DRAFT, Publication.PUBLISHED):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Publicação salva com sucesso.')
        return super().form_valid(form)


class PublicationConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'console/publication_form.html'
    success_url = reverse_lazy('console:publication-list')


class AudienceSimulationView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/audience_simulation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = AudienceSimulationForm(self.request.GET or None)
        results = []
        if self.request.GET:
            form.is_valid()
            selected = self._selected_scope(form)
            memberships = list(
                Membership.objects.filter(active=True)
                .select_related('user', 'organization', 'company', 'business_unit', 'operational_unit')
                .prefetch_related('channels', 'functions')
            )
            publications = Publication.objects.filter(
                status=Publication.PUBLISHED
            ).select_related('organization', 'audience_policy').prefetch_related('audience_policy__rules')
            courses = Course.objects.filter(
                state='published'
            ).select_related('organization', 'audience_policy').prefetch_related('audience_policy__rules')
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
                        defaults={'organization': data['organization'], 'active': True},
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
                membership, _ = Membership.objects.update_or_create(
                    user=user, company=company, business_unit=business_unit, operational_unit=operational_unit,
                    defaults={'organization': organization, 'active': True},
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
        queryset = Course.objects.select_related('organization', 'subject', 'audience_policy').annotate(module_count=Count('modules')).order_by('-created')
        query = self.request.GET.get('q', '').strip()
        state = self.request.GET.get('state', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query)
        if state in ('published', 'unpublished'):
            queryset = queryset.filter(state=state)
        return queryset


class CourseConsoleCreateView(ManagerRequiredMixin, CreateView):
    model = Course
    form_class = CourseConsoleForm
    template_name = 'console/course_form.html'
    success_url = reverse_lazy('console:course-list')

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


class PolicyConsoleFormView(ManagerRequiredMixin, View):
    template_name = 'console/policy_form.html'
    success_url = reverse_lazy('console:policy-list')

    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(AudiencePolicy, pk=pk) if pk else AudiencePolicy()

    def get_forms(self, request=None):
        policy = self.get_object()
        post_data = request.POST if request is not None else None
        policy_form = AudiencePolicyForm(post_data, instance=policy, prefix='policy')
        rule_formset = forms.inlineformset_factory(
            AudiencePolicy, AudienceRule, form=AudienceRuleForm,
            extra=2, can_delete=True
        )(post_data, instance=policy, prefix='rules')
        return policy, policy_form, rule_formset

    def get(self, request, *args, **kwargs):
        policy, policy_form, rule_formset = self.get_forms()
        return self.render_to_response(policy, policy_form, rule_formset)

    def post(self, request, *args, **kwargs):
        policy, policy_form, rule_formset = self.get_forms(request)
        if policy_form.is_valid() and rule_formset.is_valid():
            policy = policy_form.save()
            rule_formset.instance = policy
            rule_formset.save()
            messages.success(request, 'Regra de audiência salva com sucesso.')
            return redirect(self.success_url)
        return self.render_to_response(policy, policy_form, rule_formset)

    def render_to_response(self, policy, policy_form, rule_formset):
        from django.shortcuts import render
        return render(self.request, self.template_name, {
            'policy': policy, 'form': policy_form, 'rule_formset': rule_formset,
        })


class PolicyConsoleListView(ManagerRequiredMixin, ListView):
    model = AudiencePolicy
    template_name = 'console/policy_list.html'
    context_object_name = 'policies'

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('rules')
        query = self.request.GET.get('q', '').strip()
        active = self.request.GET.get('active', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        if active in ('true', 'false'):
            queryset = queryset.filter(active=active == 'true')
        return queryset


class PolicyConsoleCreateView(PolicyConsoleFormView):
    pass


class PolicyConsoleUpdateView(PolicyConsoleFormView):
    pass


class UserConsoleListView(ManagerRequiredMixin, ListView):
    model = User
    template_name = 'console/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        queryset = User.objects.prefetch_related('memberships__company', 'memberships__business_unit')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(username__icontains=query) | queryset.filter(email__icontains=query)
        return queryset.order_by('username')


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
