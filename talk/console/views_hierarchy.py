"""Console views for managing organizational hierarchy (Company, BusinessUnit, JobFunction, etc)."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView

from configuration.models import (
    Company, BusinessUnit, JobFunction, BusinessChannel, PersonType, OperationalUnit
)
from console.views import active_organization


def get_terminology(request):
    """Get organization terminology or defaults."""
    org = active_organization(request)
    if org and hasattr(org, 'terminology') and org.terminology:
        return org.terminology
    return None


# ========== COMPANY VIEWS ==========

class CompanyListView(LoginRequiredMixin, ListView):
    """List companies for the organization."""
    model = Company
    template_name = 'console/hierarchy/company_list.html'
    context_object_name = 'companies'
    paginate_by = 25

    def get_queryset(self):
        return Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        terminology = get_terminology(self.request)
        ctx['title'] = terminology.level_1_label if terminology else 'Empresas'
        ctx['description'] = terminology.level_1_description if terminology else ''
        ctx['terminology'] = terminology
        return ctx


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Create new company."""
    model = Company
    template_name = 'console/hierarchy/company_form.html'
    fields = ['name', 'legal_name', 'cnpj', 'ie', 'email_geral', 'telefone_geral', 'website',
              'endereco_correspondencia', 'cep_correspondencia', 'city_correspondencia', 'state_correspondencia', 'active']
    success_url = reverse_lazy('console:company_list')

    def form_valid(self, form):
        # Set organization from user membership
        membership = self.request.user.memberships.filter(active=True).first()
        if membership:
            form.instance.organization = membership.organization
        return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """Update company."""
    model = Company
    template_name = 'console/hierarchy/company_form.html'
    fields = ['name', 'legal_name', 'cnpj', 'ie', 'email_geral', 'telefone_geral', 'website',
              'endereco_correspondencia', 'cep_correspondencia', 'city_correspondencia', 'state_correspondencia', 'active']
    success_url = reverse_lazy('console:company_list')

    def get_queryset(self):
        return Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))


# ========== BUSINESS UNIT VIEWS ==========

class BusinessUnitListView(LoginRequiredMixin, ListView):
    """List business units."""
    model = BusinessUnit
    template_name = 'console/hierarchy/business_unit_list.html'
    context_object_name = 'units'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return BusinessUnit.objects.filter(company__in=companies).select_related('company', 'manager')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        terminology = get_terminology(self.request)
        ctx['title'] = terminology.level_2_label if terminology else 'Unidades de Negócio'
        ctx['description'] = terminology.level_2_description if terminology else ''
        ctx['terminology'] = terminology
        ctx['companies'] = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return ctx


class BusinessUnitCreateView(LoginRequiredMixin, CreateView):
    """Create new business unit."""
    model = BusinessUnit
    template_name = 'console/hierarchy/business_unit_form.html'
    fields = ['company', 'name', 'code', 'endereco', 'cep', 'city', 'state',
              'telefone', 'email', 'latitude', 'longitude', 'usar_endereco_empresa', 'manager', 'active']
    success_url = reverse_lazy('console:business_unit_list')


class BusinessUnitUpdateView(LoginRequiredMixin, UpdateView):
    """Update business unit."""
    model = BusinessUnit
    template_name = 'console/hierarchy/business_unit_form.html'
    fields = ['company', 'name', 'code', 'endereco', 'cep', 'city', 'state',
              'telefone', 'email', 'latitude', 'longitude', 'usar_endereco_empresa', 'manager', 'active']
    success_url = reverse_lazy('console:business_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return BusinessUnit.objects.filter(company__in=companies)


# ========== JOB FUNCTION VIEWS ==========

class JobFunctionListView(LoginRequiredMixin, ListView):
    """List job functions."""
    model = JobFunction
    template_name = 'console/hierarchy/job_function_list.html'
    context_object_name = 'functions'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return JobFunction.objects.filter(company__in=companies).prefetch_related('channels')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Funções de Trabalho'
        ctx['companies'] = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return ctx


class JobFunctionCreateView(LoginRequiredMixin, CreateView):
    """Create new job function."""
    model = JobFunction
    template_name = 'console/hierarchy/job_function_form.html'
    fields = ['company', 'name', 'channels', 'active']
    success_url = reverse_lazy('console:job_function_list')


class JobFunctionUpdateView(LoginRequiredMixin, UpdateView):
    """Update job function."""
    model = JobFunction
    template_name = 'console/hierarchy/job_function_form.html'
    fields = ['company', 'name', 'channels', 'active']
    success_url = reverse_lazy('console:job_function_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return JobFunction.objects.filter(company__in=companies)


# ========== BUSINESS CHANNEL VIEWS ==========

class BusinessChannelListView(LoginRequiredMixin, ListView):
    """List business channels."""
    model = BusinessChannel
    template_name = 'console/hierarchy/business_channel_list.html'
    context_object_name = 'channels'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return BusinessChannel.objects.filter(company__in=companies)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Canais de Negócio'
        ctx['companies'] = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return ctx


class BusinessChannelCreateView(LoginRequiredMixin, CreateView):
    """Create new business channel."""
    model = BusinessChannel
    template_name = 'console/hierarchy/business_channel_form.html'
    fields = ['company', 'name', 'active']
    success_url = reverse_lazy('console:business_channel_list')


class BusinessChannelUpdateView(LoginRequiredMixin, UpdateView):
    """Update business channel."""
    model = BusinessChannel
    template_name = 'console/hierarchy/business_channel_form.html'
    fields = ['company', 'name', 'active']
    success_url = reverse_lazy('console:business_channel_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return BusinessChannel.objects.filter(company__in=companies)


# ========== PERSON TYPE VIEWS ==========

class PersonTypeListView(LoginRequiredMixin, ListView):
    """List person types."""
    model = PersonType
    template_name = 'console/hierarchy/person_type_list.html'
    context_object_name = 'person_types'
    paginate_by = 25

    def get_queryset(self):
        orgs = self.request.user.memberships.values_list('organization', flat=True)
        return PersonType.objects.filter(organization__in=orgs).order_by('position')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Tipos de Pessoa'
        return ctx


class PersonTypeCreateView(LoginRequiredMixin, CreateView):
    """Create new person type."""
    model = PersonType
    template_name = 'console/hierarchy/person_type_form.html'
    fields = ['code', 'name', 'description', 'position', 'active']
    success_url = reverse_lazy('console:person_type_list')

    def form_valid(self, form):
        membership = self.request.user.memberships.filter(active=True).first()
        if membership:
            form.instance.organization = membership.organization
        return super().form_valid(form)


class PersonTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update person type."""
    model = PersonType
    template_name = 'console/hierarchy/person_type_form.html'
    fields = ['code', 'name', 'description', 'position', 'active']
    success_url = reverse_lazy('console:person_type_list')

    def get_queryset(self):
        orgs = self.request.user.memberships.values_list('organization', flat=True)
        return PersonType.objects.filter(organization__in=orgs)


# ========== OPERATIONAL UNIT VIEWS ==========

class OperationalUnitListView(LoginRequiredMixin, ListView):
    """List operational units."""
    model = OperationalUnit
    template_name = 'console/hierarchy/operational_unit_list.html'
    context_object_name = 'units'
    paginate_by = 25

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units).select_related('business_unit', 'business_unit__company')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        terminology = get_terminology(self.request)
        ctx['title'] = terminology.level_3_label if terminology else 'Unidades Operacionais'
        ctx['description'] = terminology.level_3_description if terminology else ''
        ctx['terminology'] = terminology
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        ctx['business_units'] = BusinessUnit.objects.filter(company__in=companies)
        return ctx


class OperationalUnitCreateView(LoginRequiredMixin, CreateView):
    """Create new operational unit."""
    model = OperationalUnit
    template_name = 'console/hierarchy/operational_unit_form.html'
    fields = ['business_unit', 'name', 'code', 'active']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        form.fields['business_unit'].queryset = business_units
        return form


class OperationalUnitUpdateView(LoginRequiredMixin, UpdateView):
    """Update operational unit."""
    model = OperationalUnit
    template_name = 'console/hierarchy/operational_unit_form.html'
    fields = ['business_unit', 'name', 'code', 'active']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        form.fields['business_unit'].queryset = business_units
        return form


# ========== INACTIVATION VIEWS ==========

class InactivateCompanyView(LoginRequiredMixin, UpdateView):
    """Inactivate a company and cascade to related units."""
    model = Company
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:company_list')

    def get_queryset(self):
        return Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Inactivate company and cascade to business units
        self.object.active = False
        self.object.save()
        # Cascade: inactivate all related business units
        BusinessUnit.objects.filter(company=self.object).update(active=False)
        # Cascade: inactivate all related operational units
        OperationalUnit.objects.filter(business_unit__company=self.object).update(active=False)
        messages.success(request, f'{self.object.name} foi inativada. Todas as unidades relacionadas foram inativadas também.')
        return redirect(self.success_url)


class InactivateBusinessUnitView(LoginRequiredMixin, UpdateView):
    """Inactivate a business unit and cascade to operational units."""
    model = BusinessUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:business_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return BusinessUnit.objects.filter(company__in=companies)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Inactivate business unit
        self.object.active = False
        self.object.save()
        # Cascade: inactivate all related operational units
        OperationalUnit.objects.filter(business_unit=self.object).update(active=False)
        messages.success(request, f'{self.object.name} foi inativada. Todas as unidades operacionais relacionadas foram inativadas também.')
        return redirect(self.success_url)


class InactivateOperationalUnitView(LoginRequiredMixin, UpdateView):
    """Inactivate an operational unit."""
    model = OperationalUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        business_units = BusinessUnit.objects.filter(company__in=companies)
        return OperationalUnit.objects.filter(business_unit__in=business_units)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.active = False
        self.object.save()
        messages.success(request, f'{self.object.name} foi inativada.')
        return redirect(self.success_url)


class ActivateCompanyView(LoginRequiredMixin, UpdateView):
    """Reactivate a company."""
    model = Company
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:company_list')

    def get_queryset(self):
        return Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.active = True
        self.object.save()
        messages.success(request, f'{self.object.name} foi reativada.')
        return redirect(self.success_url)


class ActivateBusinessUnitView(LoginRequiredMixin, UpdateView):
    """Reactivate a business unit."""
    model = BusinessUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:business_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
        return BusinessUnit.objects.filter(company__in=companies)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Check if parent company is active
        if not self.object.company.active:
            messages.error(request, f'Não é possível reativar. A empresa {self.object.company.name} está inativa.')
            return redirect(self.success_url)
        self.object.active = True
        self.object.save()
        messages.success(request, f'{self.object.name} foi reativada.')
        return redirect(self.success_url)


class ActivateOperationalUnitView(LoginRequiredMixin, UpdateView):
    """Reactivate an operational unit."""
    model = OperationalUnit
    fields = []
    http_method_names = ['post']
    success_url = reverse_lazy('console:operational_unit_list')

    def get_queryset(self):
        companies = Company.objects.filter(organization__in=self.request.user.memberships.values_list('organization', flat=True))
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
        messages.success(request, f'{self.object.name} foi reativada.')
        return redirect(self.success_url)
