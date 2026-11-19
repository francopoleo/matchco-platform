"""Console views for managing organizational hierarchy (Company, BusinessUnit, JobFunction, etc)."""

from django.utils.translation import gettext_lazy as gettext_lazy

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView, View

from configuration.models import (
    Company, BusinessUnit, JobFunction, BusinessChannel, PersonType, OperationalUnit,
    HierarchyAuditLog, Organization, PhysicalLocation
)
from console.forms import PersonTypeForm
from console.views import ConsoleRecordNavigationMixin, ManagerRequiredMixin, active_organization


def visible_organization_ids(request):
    """Organizations visible in hierarchy screens for the active workspace."""
    organization = active_organization(request)
    if organization:
        return [organization.pk]
    if request.user.is_superuser and request.session.get('selected_organization_id') == '__all__':
        return Organization.objects.filter(active=True, is_public=False).values_list('pk', flat=True)
    return request.user.memberships.filter(active=True).values_list('organization_id', flat=True).distinct()


def get_terminology(request):
    """Get organization terminology or defaults."""
    org = active_organization(request)
    if org and hasattr(org, 'terminology') and org.terminology:
        return org.terminology
    return None


def log_hierarchy_action(request, action, resource_type, resource_id, resource_name, changes=None, reason='', affected_count=1):
    """Log a hierarchy management action to audit log."""
    org = active_organization(request)
    if org:
        HierarchyAuditLog.log_action(
            organization=org,
            user=request.user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            reason=reason,
            affected_count=affected_count,
        )


# ========== COMPANY VIEWS ==========

class CompanyFormStyleMixin:
    """Apply the shared Flowbite-compatible form tokens to company fields."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        field_class = (
            'block w-full rounded-base border border-default-medium '
            'bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading '
            'placeholder:text-body focus:border-brand focus:ring-2 focus:ring-brand/30'
        )
        checkbox_class = (
            'h-4 w-4 rounded border-default-medium bg-neutral-secondary-medium '
            'text-brand focus:ring-2 focus:ring-brand/30'
        )
        for field in form.fields.values():
            field.widget.attrs['class'] = checkbox_class if getattr(field.widget, 'input_type', '') == 'checkbox' else field_class
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Empresas'), 'url': reverse('console:company_list')},
            {'label': gettext_lazy('Nova empresa') if not getattr(self.object, 'pk', None) else self.object.name},
        ]
        context['organization'] = active_organization(self.request)
        return context

class CompanyListView(LoginRequiredMixin, ListView):
    """List companies for the organization."""
    model = Company
    template_name = 'console/hierarchy/company_list.html'
    context_object_name = 'companies'
    paginate_by = 25

    def get_queryset(self):
        return (
            Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
            .select_related('organization')
            .prefetch_related('business_units')
            .annotate(
                active_unit_count=Count('business_units', filter=Q(business_units__active=True), distinct=True),
                operational_unit_count=Count(
                    'business_units__operational_units',
                    filter=Q(business_units__operational_units__active=True),
                    distinct=True,
                ),
            )
            .order_by('organization__name', 'name')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        terminology = get_terminology(self.request)
        ctx['title'] = terminology.level_1_label if terminology else 'Empresas'
        ctx['description'] = terminology.level_1_description if terminology else ''
        ctx['terminology'] = terminology
        ctx['organization'] = active_organization(self.request)
        ctx['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': ctx['title']},
        ]
        all_companies = self.get_queryset()
        ctx['company_count'] = all_companies.count()
        ctx['active_company_count'] = all_companies.filter(active=True).count()
        ctx['active_unit_count'] = sum(all_companies.values_list('active_unit_count', flat=True))
        return ctx


class CompanyCreateView(CompanyFormStyleMixin, LoginRequiredMixin, CreateView):
    """Create new company."""
    model = Company
    template_name = 'console/hierarchy/company_form.html'
    fields = ['name', 'legal_name', 'cnpj', 'ie', 'email_geral', 'telefone_geral', 'website',
              'endereco_correspondencia', 'cep_correspondencia', 'city_correspondencia', 'state_correspondencia', 'active']
    success_url = reverse_lazy('console:company_list')

    def form_valid(self, form):
        # Set organization from user membership
        membership = self.request.user.memberships.filter(
            active=True, organization_id__in=visible_organization_ids(self.request)
        ).first()
        if membership:
            form.instance.organization = membership.organization
        return super().form_valid(form)


class CompanyUpdateView(CompanyFormStyleMixin, ConsoleRecordNavigationMixin, LoginRequiredMixin, UpdateView):
    """Update company."""
    model = Company
    template_name = 'console/hierarchy/company_form.html'
    fields = ['name', 'legal_name', 'cnpj', 'ie', 'email_geral', 'telefone_geral', 'website',
              'endereco_correspondencia', 'cep_correspondencia', 'city_correspondencia', 'state_correspondencia', 'active']
    success_url = reverse_lazy('console:company_list')
    navigation_url_name = 'console:company_update'
    navigation_list_url_name = 'console:company_list'
    navigation_label = 'Empresas'
    navigation_ordering = ('name', 'pk')

    def get_queryset(self):
        return Company.objects.filter(organization_id__in=visible_organization_ids(self.request))


# ========== BUSINESS UNIT VIEWS ==========

class BusinessUnitListView(LoginRequiredMixin, ListView):
    """List business units."""
    model = BusinessUnit
    template_name = 'console/hierarchy/business_unit_list.html'
    context_object_name = 'units'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessUnit.objects.filter(company__in=companies).select_related('company', 'manager', 'physical_location', 'channel')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        terminology = get_terminology(self.request)
        ctx['title'] = terminology.level_2_label if terminology else 'Unidades de negócio'
        ctx['description'] = terminology.level_2_description if terminology else ''
        ctx['terminology'] = terminology
        ctx['organization'] = active_organization(self.request)
        ctx['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': ctx['title']},
        ]
        ctx['companies'] = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        all_units = self.get_queryset()
        ctx['unit_count'] = all_units.count()
        ctx['active_unit_count'] = all_units.filter(active=True).count()
        ctx['company_count'] = ctx['companies'].filter(active=True).count()
        from configuration.services import service_enabled
        page_units = list(ctx.get('units') or [])
        for unit in page_units:
            unit.match_service_enabled = service_enabled(
                unit.company.organization_id, 'recruitment', unit.company,
            )
        ctx['recruitment_enabled'] = any(unit.match_service_enabled for unit in page_units)
        # O Console mostra o estado do de-para sem duplicar a edição do Portal.
        # A ponte usa o legacy_id estável entre a unidade estrutural e sua
        # representação de recrutamento.
        from recruitment.domain_models import RecruitmentStore
        from recruitment.models import CanonicalFunctionMapping
        if not ctx['recruitment_enabled']:
            for unit in page_units:
                unit.match_mapping_count = 0
            return ctx
        legacy_ids = [unit.pk for unit in page_units]
        stores = list(RecruitmentStore.objects.filter(legacy_id__in=legacy_ids).only('id', 'legacy_id'))
        store_by_legacy = {store.legacy_id: store for store in stores}
        counts = {
            row['business_unit_id']: row['total']
            for row in CanonicalFunctionMapping.objects.filter(
                business_unit_id__in=[store.pk for store in stores], active=True,
            ).values('business_unit_id').annotate(total=Count('id'))
        }
        for unit in page_units:
            store = store_by_legacy.get(unit.pk)
            unit.match_mapping_count = counts.get(store.pk, 0) if store and unit.match_service_enabled else 0
        return ctx


class BusinessUnitRecruitmentCatalogView(LoginRequiredMixin, View):
    """Open the Match de-para for a structural business unit.

    The configuration unit remains the source of the organizational cargo and
    is translated to its recruitment representation only at this boundary.
    """

    def get(self, request, pk):
        unit = get_object_or_404(
            BusinessUnit.objects.select_related('company'),
            pk=pk,
            company__organization_id__in=visible_organization_ids(request),
        )
        from recruitment.integrations.organization import find_organization, find_store

        recruitment_org = find_organization(pk=unit.company.organization_id)
        store = find_store(store_id=unit.pk, organization=recruitment_org) if recruitment_org else None
        if store is None:
            messages.error(request, gettext_lazy('Esta unidade ainda não está disponível no catálogo de recrutamento.'))
            return redirect('console:business_unit_list')
        return redirect(reverse('recruitment:store_function_catalog', kwargs={'store_id': store.pk}))


class BusinessUnitFormScopeMixin:
    """Keep unit registration inside the selected organization."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        organization_ids = visible_organization_ids(self.request)
        form.fields['company'].queryset = Company.objects.filter(
            organization_id__in=organization_ids, active=True,
        ).order_by('name')
        form.fields['channel'].queryset = BusinessChannel.objects.filter(
            company__organization_id__in=organization_ids, active=True,
        ).select_related('company').order_by('company__name', 'name')
        form.fields['physical_location'].queryset = PhysicalLocation.objects.filter(
            active=True,
        ).order_by('name')
        field_class = (
            'block w-full rounded-base border border-default-medium '
            'bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading '
            'placeholder:text-body focus:border-brand focus:ring-2 focus:ring-brand/30'
        )
        checkbox_class = (
            'h-4 w-4 rounded border-default-medium bg-neutral-secondary-medium '
            'text-brand focus:ring-2 focus:ring-brand/30'
        )
        for field in form.fields.values():
            field.widget.attrs['class'] = checkbox_class if getattr(field.widget, 'input_type', '') == 'checkbox' else field_class
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Unidades de negócio'), 'url': reverse('console:business_unit_list')},
            {'label': gettext_lazy('Nova unidade') if not getattr(self.object, 'pk', None) else self.object.name},
        ]
        context['organization'] = active_organization(self.request)
        return context


class BusinessUnitCreateView(BusinessUnitFormScopeMixin, LoginRequiredMixin, CreateView):
    """Create new business unit."""
    model = BusinessUnit
    template_name = 'console/hierarchy/business_unit_form.html'
    fields = ['company', 'name', 'trade_name', 'code', 'external_reference', 'unit_kind', 'location_type',
              'channel', 'physical_location', 'shopping_name', 'endereco', 'address_number',
              'address_complement', 'neighborhood', 'cep', 'city', 'state', 'telefone', 'email',
              'contact_name', 'website', 'tax_id', 'state_registration', 'opening_hours',
              'latitude', 'longitude', 'usar_endereco_empresa', 'manager', 'active']
    success_url = reverse_lazy('console:business_unit_list')


class BusinessUnitUpdateView(BusinessUnitFormScopeMixin, ConsoleRecordNavigationMixin, LoginRequiredMixin, UpdateView):
    """Update business unit."""
    model = BusinessUnit
    template_name = 'console/hierarchy/business_unit_form.html'
    fields = BusinessUnitCreateView.fields
    success_url = reverse_lazy('console:business_unit_list')
    navigation_url_name = 'console:business_unit_update'
    navigation_list_url_name = 'console:business_unit_list'
    navigation_label = 'Unidades de negócio'
    navigation_ordering = ('name', 'pk')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessUnit.objects.filter(company__in=companies)


# ========== JOB FUNCTION VIEWS ==========

class JobFunctionListView(LoginRequiredMixin, ListView):
    """List job functions."""
    model = JobFunction
    template_name = 'console/hierarchy/job_function_list.html'
    context_object_name = 'functions'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return JobFunction.objects.filter(company__in=companies).prefetch_related('channels')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Funções de Trabalho'
        ctx['organization'] = active_organization(self.request)
        ctx['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Cargos e funções')},
        ]
        ctx['companies'] = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        all_functions = self.get_queryset()
        ctx['function_count'] = all_functions.count()
        ctx['active_function_count'] = all_functions.filter(active=True).count()
        from configuration.services import service_enabled
        ctx['recruitment_enabled'] = any(
            service_enabled(company.organization_id, 'recruitment', company)
            for company in ctx['companies']
        )
        return ctx


class JobFunctionFormScopeMixin:
    """Keep job-function forms scoped to the active organization."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        organization_ids = visible_organization_ids(self.request)
        form.fields['company'].queryset = Company.objects.filter(
            organization_id__in=organization_ids, active=True,
        ).order_by('name')
        form.fields['channels'].queryset = BusinessChannel.objects.filter(
            company__organization_id__in=organization_ids, active=True,
        ).select_related('company').order_by('company__name', 'name')
        field_class = (
            'block w-full rounded-base border border-default-medium '
            'bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading '
            'placeholder:text-body focus:border-brand focus:ring-2 focus:ring-brand/30'
        )
        checkbox_class = 'h-4 w-4 rounded border-default-medium bg-neutral-secondary-medium text-brand focus:ring-2 focus:ring-brand/30'
        for field in form.fields.values():
            field.widget.attrs['class'] = checkbox_class if getattr(field.widget, 'input_type', '') == 'checkbox' else field_class
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Cargos e funções'), 'url': reverse('console:job_function_list')},
            {'label': gettext_lazy('Novo cargo') if not getattr(self.object, 'pk', None) else self.object.name},
        ]
        context['organization'] = active_organization(self.request)
        return context


class JobFunctionCreateView(JobFunctionFormScopeMixin, LoginRequiredMixin, CreateView):
    """Create new job function."""
    model = JobFunction
    template_name = 'console/hierarchy/job_function_form.html'
    fields = ['company', 'name', 'channels', 'active']
    success_url = reverse_lazy('console:job_function_list')


class JobFunctionUpdateView(JobFunctionFormScopeMixin, ConsoleRecordNavigationMixin, LoginRequiredMixin, UpdateView):
    """Update job function."""
    model = JobFunction
    template_name = 'console/hierarchy/job_function_form.html'
    fields = ['company', 'name', 'channels', 'active']
    success_url = reverse_lazy('console:job_function_list')
    navigation_url_name = 'console:job_function_update'
    navigation_list_url_name = 'console:job_function_list'
    navigation_label = 'Funções'
    navigation_ordering = ('name', 'pk')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return JobFunction.objects.filter(company__in=companies)


# ========== BUSINESS CHANNEL VIEWS ==========

class BusinessChannelListView(LoginRequiredMixin, ListView):
    """List business channels."""
    model = BusinessChannel
    template_name = 'console/hierarchy/business_channel_list.html'
    context_object_name = 'channels'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessChannel.objects.filter(company__in=companies)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Canais de negócio'
        ctx['organization'] = active_organization(self.request)
        ctx['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Canais de negócio')},
        ]
        ctx['companies'] = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        all_channels = self.get_queryset()
        ctx['channel_count'] = all_channels.count()
        ctx['active_channel_count'] = all_channels.filter(active=True).count()
        return ctx


class BusinessChannelFormScopeMixin:
    """Keep channel forms inside the active organization and style them consistently."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['company'].queryset = Company.objects.filter(
            organization_id__in=visible_organization_ids(self.request), active=True,
        ).order_by('name')
        field_class = (
            'block w-full rounded-base border border-default-medium '
            'bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading '
            'placeholder:text-body focus:border-brand focus:ring-2 focus:ring-brand/30'
        )
        checkbox_class = 'h-4 w-4 rounded border-default-medium bg-neutral-secondary-medium text-brand focus:ring-2 focus:ring-brand/30'
        for field in form.fields.values():
            field.widget.attrs['class'] = checkbox_class if getattr(field.widget, 'input_type', '') == 'checkbox' else field_class
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Canais de negócio'), 'url': reverse('console:business_channel_list')},
            {'label': gettext_lazy('Novo canal') if not getattr(self.object, 'pk', None) else self.object.name},
        ]
        context['organization'] = active_organization(self.request)
        return context


class BusinessChannelCreateView(BusinessChannelFormScopeMixin, LoginRequiredMixin, CreateView):
    """Create new business channel."""
    model = BusinessChannel
    template_name = 'console/hierarchy/business_channel_form.html'
    fields = ['company', 'name', 'active']
    success_url = reverse_lazy('console:business_channel_list')


class BusinessChannelUpdateView(BusinessChannelFormScopeMixin, ConsoleRecordNavigationMixin, LoginRequiredMixin, UpdateView):
    """Update business channel."""
    model = BusinessChannel
    template_name = 'console/hierarchy/business_channel_form.html'
    fields = ['company', 'name', 'active']
    success_url = reverse_lazy('console:business_channel_list')
    navigation_url_name = 'console:business_channel_update'
    navigation_list_url_name = 'console:business_channel_list'
    navigation_label = 'Canais'
    navigation_ordering = ('name', 'pk')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessChannel.objects.filter(company__in=companies)


# ========== PERSON TYPE VIEWS ==========

class PersonTypeListView(ManagerRequiredMixin, ListView):
    """List person types."""
    model = PersonType
    template_name = 'console/hierarchy/person_type_list.html'
    context_object_name = 'person_types'
    paginate_by = 25

    def get_queryset(self):
        orgs = visible_organization_ids(self.request)
        return PersonType.objects.filter(organization__in=orgs).order_by('position')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_types = self.get_queryset()
        ctx.update({
            'title': gettext_lazy('Tipos de público e vínculo'),
            'organization': active_organization(self.request),
            'total_person_types': all_types.count(),
            'active_person_types': all_types.filter(active=True).count(),
            'inactive_person_types': all_types.filter(active=False).count(),
            'breadcrumbs': [
                {'label': gettext_lazy('Organização e estrutura')},
                {'label': gettext_lazy('Tipos de público e vínculo')},
            ],
        })
        return ctx


class PersonTypeCreateView(ManagerRequiredMixin, CreateView):
    """Create new person type."""
    model = PersonType
    template_name = 'console/hierarchy/person_type_form.html'
    form_class = PersonTypeForm
    success_url = reverse_lazy('console:person_type_list')

    def form_valid(self, form):
        organization = active_organization(self.request)
        if not organization:
            form.add_error(None, gettext_lazy('Selecione uma organização ativa antes de criar um tipo de pessoa.'))
            return self.form_invalid(form)
        form.instance.organization = organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = active_organization(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = active_organization(self.request)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Tipos de público e vínculo'), 'url': reverse('console:person_type_list')},
            {'label': gettext_lazy('Novo tipo')},
        ]
        return context


class PersonTypeUpdateView(ConsoleRecordNavigationMixin, ManagerRequiredMixin, UpdateView):
    """Update person type."""
    model = PersonType
    template_name = 'console/hierarchy/person_type_form.html'
    form_class = PersonTypeForm
    success_url = reverse_lazy('console:person_type_list')
    navigation_url_name = 'console:person_type_update'
    navigation_list_url_name = 'console:person_type_list'
    navigation_label = 'Tipos de pessoa'
    navigation_ordering = ('name', 'pk')

    def get_queryset(self):
        orgs = visible_organization_ids(self.request)
        return PersonType.objects.filter(organization__in=orgs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.object.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = active_organization(self.request)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Tipos de público e vínculo'), 'url': reverse('console:person_type_list')},
            {'label': self.object.name},
        ]
        return context


# ========== OPERATIONAL UNIT VIEWS ==========

class OperationalUnitListView(LoginRequiredMixin, ListView):
    """List operational units."""
    model = OperationalUnit
    template_name = 'console/hierarchy/operational_unit_list.html'
    context_object_name = 'units'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units).select_related('business_unit', 'business_unit__company')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        terminology = get_terminology(self.request)
        ctx['title'] = terminology.level_3_label if terminology else 'Unidades operacionais'
        ctx['description'] = terminology.level_3_description if terminology else ''
        ctx['terminology'] = terminology
        ctx['organization'] = active_organization(self.request)
        ctx['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': ctx['title']},
        ]
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        ctx['business_units'] = BusinessUnit.objects.filter(company__in=companies)
        all_units = self.get_queryset()
        ctx['unit_count'] = all_units.count()
        ctx['active_unit_count'] = all_units.filter(active=True).count()
        ctx['business_unit_count'] = ctx['business_units'].filter(active=True).count()
        return ctx


class OperationalUnitFormScopeMixin:
    """Keep operational units scoped and styled consistently."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        form.fields['business_unit'].queryset = BusinessUnit.objects.filter(company__in=companies).select_related('company').order_by('company__name', 'name')
        field_class = (
            'block w-full rounded-base border border-default-medium '
            'bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading '
            'placeholder:text-body focus:border-brand focus:ring-2 focus:ring-brand/30'
        )
        checkbox_class = 'h-4 w-4 rounded border-default-medium bg-neutral-secondary-medium text-brand focus:ring-2 focus:ring-brand/30'
        for field in form.fields.values():
            field.widget.attrs['class'] = checkbox_class if getattr(field.widget, 'input_type', '') == 'checkbox' else field_class
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': gettext_lazy('Organização e estrutura')},
            {'label': gettext_lazy('Unidades operacionais'), 'url': reverse('console:operational_unit_list')},
            {'label': gettext_lazy('Nova unidade operacional') if not getattr(self.object, 'pk', None) else self.object.name},
        ]
        context['organization'] = active_organization(self.request)
        return context


class OperationalUnitCreateView(OperationalUnitFormScopeMixin, LoginRequiredMixin, CreateView):
    """Create new operational unit."""
    model = OperationalUnit
    template_name = 'console/hierarchy/operational_unit_form.html'
    fields = ['business_unit', 'name', 'code', 'active']
    success_url = reverse_lazy('console:operational_unit_list')

class OperationalUnitUpdateView(OperationalUnitFormScopeMixin, ConsoleRecordNavigationMixin, LoginRequiredMixin, UpdateView):
    """Update operational unit."""
    model = OperationalUnit
    template_name = 'console/hierarchy/operational_unit_form.html'
    fields = ['business_unit', 'name', 'code', 'active']
    success_url = reverse_lazy('console:operational_unit_list')
    navigation_url_name = 'console:operational_unit_update'
    navigation_list_url_name = 'console:operational_unit_list'
    navigation_label = 'Unidades operacionais'
    navigation_ordering = ('name', 'pk')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units)

# ========== INACTIVATION VIEWS ==========

class InactivateCompanyView(LoginRequiredMixin, UpdateView):
    """Inactivate a company and cascade to related units."""
    model = Company
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:company_list')

    def get_queryset(self):
        return Company.objects.filter(organization_id__in=visible_organization_ids(self.request))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Inactivate company and cascade to business units
        self.object.active = False
        self.object.save()
        # Cascade: inactivate all related business units
        bu_count = BusinessUnit.objects.filter(company=self.object).update(active=False)
        # Cascade: inactivate all related operational units
        ou_count = OperationalUnit.objects.filter(business_unit__company=self.object).update(active=False)

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_INACTIVATE,
            HierarchyAuditLog.RESOURCE_COMPANY,
            self.object.id,
            self.object.name,
            changes={'active': {'before': True, 'after': False}},
            reason='Cascaded inactivation',
            affected_count=1 + bu_count + ou_count,
        )

        messages.success(request, f'{self.object.name} foi inativada. Todas as unidades relacionadas foram inativadas também.')
        return redirect(self.success_url)


class InactivateBusinessUnitView(LoginRequiredMixin, UpdateView):
    """Inactivate a business unit and cascade to operational units."""
    model = BusinessUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:business_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessUnit.objects.filter(company__in=companies)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Inactivate business unit
        self.object.active = False
        self.object.save()
        # Cascade: inactivate all related operational units
        ou_count = OperationalUnit.objects.filter(business_unit=self.object).update(active=False)

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_INACTIVATE,
            HierarchyAuditLog.RESOURCE_BUSINESS_UNIT,
            self.object.id,
            self.object.name,
            changes={'active': {'before': True, 'after': False}},
            reason='Cascaded inactivation',
            affected_count=1 + ou_count,
        )

        messages.success(request, f'{self.object.name} foi inativada. Todas as unidades operacionais relacionadas foram inativadas também.')
        return redirect(self.success_url)


class InactivateOperationalUnitView(LoginRequiredMixin, UpdateView):
    """Inactivate an operational unit."""
    model = OperationalUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.active = False
        self.object.save()

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_INACTIVATE,
            HierarchyAuditLog.RESOURCE_OPERATIONAL_UNIT,
            self.object.id,
            self.object.name,
            changes={'active': {'before': True, 'after': False}},
        )

        messages.success(request, f'{self.object.name} foi inativada.')
        return redirect(self.success_url)


class ActivateCompanyView(LoginRequiredMixin, UpdateView):
    """Reactivate a company."""
    model = Company
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:company_list')

    def get_queryset(self):
        return Company.objects.filter(organization_id__in=visible_organization_ids(self.request))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.active = True
        self.object.save()

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_ACTIVATE,
            HierarchyAuditLog.RESOURCE_COMPANY,
            self.object.id,
            self.object.name,
            changes={'active': {'before': False, 'after': True}},
        )

        messages.success(request, f'{self.object.name} foi reativada.')
        return redirect(self.success_url)


class ActivateBusinessUnitView(LoginRequiredMixin, UpdateView):
    """Reactivate a business unit."""
    model = BusinessUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:business_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessUnit.objects.filter(company__in=companies)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Check if parent company is active
        if not self.object.company.active:
            messages.error(request, f'Não é possível reativar. A empresa {self.object.company.name} está inativa.')
            return redirect(self.success_url)
        self.object.active = True
        self.object.save()

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_ACTIVATE,
            HierarchyAuditLog.RESOURCE_BUSINESS_UNIT,
            self.object.id,
            self.object.name,
            changes={'active': {'before': False, 'after': True}},
        )

        messages.success(request, f'{self.object.name} foi reativada.')
        return redirect(self.success_url)


class ActivateOperationalUnitView(LoginRequiredMixin, UpdateView):
    """Reactivate an operational unit."""
    model = OperationalUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Check if parent business unit is active
        if not self.object.business_unit.active:
            messages.error(request, f'Não é possível reativar. A unidade {self.object.business_unit.name} está inativa.')
            return redirect(self.success_url)
        self.object.active = True
        self.object.save()

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_ACTIVATE,
            HierarchyAuditLog.RESOURCE_OPERATIONAL_UNIT,
            self.object.id,
            self.object.name,
            changes={'active': {'before': False, 'after': True}},
        )

        messages.success(request, f'{self.object.name} foi reativada.')
        return redirect(self.success_url)


# ========== AUDIT LOG VIEWS ==========

class HierarchyAuditLogView(LoginRequiredMixin, ListView):
    """View hierarchy audit logs."""
    model = HierarchyAuditLog
    template_name = 'console/hierarchy/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        org = active_organization(self.request)
        if not org:
            return HierarchyAuditLog.objects.none()
        
        qs = HierarchyAuditLog.objects.filter(organization=org)
        
        # Filter by resource type if specified
        resource_type = self.request.GET.get('resource_type')
        if resource_type in dict(HierarchyAuditLog.RESOURCE_CHOICES):
            qs = qs.filter(resource_type=resource_type)
        
        # Filter by action if specified
        action = self.request.GET.get('action')
        if action in dict(HierarchyAuditLog.ACTION_CHOICES):
            qs = qs.filter(action=action)
        
        return qs.select_related('user')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action_choices'] = [
            (HierarchyAuditLog.ACTION_CREATE, gettext_lazy('Criado')),
            (HierarchyAuditLog.ACTION_UPDATE, gettext_lazy('Atualizado')),
            (HierarchyAuditLog.ACTION_INACTIVATE, gettext_lazy('Desativado')),
            (HierarchyAuditLog.ACTION_ACTIVATE, gettext_lazy('Ativado')),
            (HierarchyAuditLog.ACTION_DELETE, gettext_lazy('Excluído')),
        ]
        ctx['resource_choices'] = [
            (HierarchyAuditLog.RESOURCE_COMPANY, gettext_lazy('Empresa')),
            (HierarchyAuditLog.RESOURCE_BUSINESS_UNIT, gettext_lazy('Unidade de negócio')),
            (HierarchyAuditLog.RESOURCE_OPERATIONAL_UNIT, gettext_lazy('Unidade operacional')),
        ]
        ctx['current_action'] = self.request.GET.get('action', '')
        ctx['current_resource'] = self.request.GET.get('resource_type', '')
        ctx['total_logs'] = ctx['paginator'].count if ctx.get('paginator') else self.get_queryset().count()
        ctx['breadcrumbs'] = [
            {'label': gettext_lazy('Análises e auditoria')},
            {'label': gettext_lazy('Auditoria da estrutura')},
        ]
        return ctx


# ========== DELETE VIEWS ==========

class DeleteCompanyView(LoginRequiredMixin, DeleteView):
    """Delete a company if it has no related business units."""
    model = Company
    http_method_names = ['post']
    success_url = reverse_lazy('console:company_list')

    def get_queryset(self):
        return Company.objects.filter(organization_id__in=visible_organization_ids(self.request))

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if there are related business units
        related_bu = BusinessUnit.objects.filter(company=self.object).count()
        if related_bu > 0:
            messages.error(
                request,
                f'Não é possível deletar {self.object.name}. Existem {related_bu} unidades de negócio relacionadas. Inative-as primeiro ou delete-as individualmente.'
            )
            return redirect(self.success_url)

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_DELETE,
            HierarchyAuditLog.RESOURCE_COMPANY,
            self.object.id,
            self.object.name,
            reason='Manual deletion - no related business units',
        )

        messages.success(request, f'{self.object.name} foi deletada permanentemente.')
        return super().delete(request, *args, **kwargs)


class DeleteBusinessUnitView(LoginRequiredMixin, DeleteView):
    """Delete a business unit if it has no related operational units."""
    model = BusinessUnit
    http_method_names = ['post']
    success_url = reverse_lazy('console:business_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        return BusinessUnit.objects.filter(company__in=companies)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if there are related operational units
        related_ou = OperationalUnit.objects.filter(business_unit=self.object).count()
        if related_ou > 0:
            messages.error(
                request,
                f'Não é possível deletar {self.object.name}. Existem {related_ou} unidades operacionais relacionadas. Inative-as primeiro ou delete-as individualmente.'
            )
            return redirect(self.success_url)

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_DELETE,
            HierarchyAuditLog.RESOURCE_BUSINESS_UNIT,
            self.object.id,
            self.object.name,
            reason='Manual deletion - no related operational units',
        )

        messages.success(request, f'{self.object.name} foi deletada permanentemente.')
        return super().delete(request, *args, **kwargs)


class DeleteOperationalUnitView(LoginRequiredMixin, DeleteView):
    """Delete an operational unit."""
    model = OperationalUnit
    http_method_names = ['post']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization_id__in=visible_organization_ids(self.request))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Log to audit
        log_hierarchy_action(
            request,
            HierarchyAuditLog.ACTION_DELETE,
            HierarchyAuditLog.RESOURCE_OPERATIONAL_UNIT,
            self.object.id,
            self.object.name,
            reason='Manual deletion',
        )

        messages.success(request, f'{self.object.name} foi deletada permanentemente.')
        return super().delete(request, *args, **kwargs)
