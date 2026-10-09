from django.utils.translation import gettext_lazy as gettext_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from courses.models import Course, Quiz
from learning.models import Certification, CertificationRequirement
from matchco.core.utils import get_tenant_organization, get_tenant_user

from .forms import CertificationForm
from .views import ManagerRequiredMixin, active_company_id, active_content_queryset, active_organization_queryset, content_company_queryset


class CertificationScopeMixin(ManagerRequiredMixin):
    def scoped_certifications(self):
        return active_content_queryset(self.request, Certification.objects.all(), company_field='company_id')

    def form_kwargs(self):
        organization = getattr(self.request, 'active_organization', None)
        tenant_org = get_tenant_organization(organization) if organization else None
        courses = active_content_queryset(self.request, Course.objects.all()).order_by('title')
        quizzes = Quiz.objects.filter(organization=tenant_org).order_by('title') if tenant_org else Quiz.objects.none()
        return {
            'courses': courses,
            'quizzes': quizzes,
            'company_queryset': content_company_queryset(self.request),
            'default_company_id': active_company_id(self.request),
            'company_required': bool(getattr(getattr(self.request, 'active_membership', None), 'company_id', None)),
        }


class CertificationListView(CertificationScopeMixin, ListView):
    model = Certification
    template_name = 'console/certification_list.html'
    context_object_name = 'certifications'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['certification_status_choices'] = Certification.STATUS_CHOICES
        context['content_companies'] = content_company_queryset(self.request)
        context['active_company_id'] = active_company_id(self.request)
        return context

    def get_queryset(self):
        query = self.scoped_certifications().select_related('organization').order_by('title')
        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        if search:
            query = query.filter(title__icontains=search)
        if status in dict(Certification.STATUS_CHOICES):
            query = query.filter(status=status)
        return query


class CertificationFormMixin(CertificationScopeMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.form_kwargs())
        return kwargs

    def save_requirements(self, certification, form):
        CertificationRequirement.objects.filter(certification=certification).delete()
        position = 1
        for course in form.cleaned_data.get('required_courses', []):
            CertificationRequirement.objects.create(certification=certification, course=course, position=position)
            position += 1
        for quiz in form.cleaned_data.get('required_quizzes', []):
            CertificationRequirement.objects.create(certification=certification, quiz=quiz, position=position)
            position += 1


class CertificationCreateView(CertificationFormMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'console/certification_form.html'
    success_url = reverse_lazy('console:certification-list')

    def form_valid(self, form):
        tenant_org = get_tenant_organization(getattr(self.request, 'active_organization', None))
        owner = get_tenant_user(self.request.user)
        if not tenant_org or not owner:
            form.add_error(None, gettext_lazy('A organização e o usuário responsável precisam estar configurados.'))
            return self.form_invalid(form)
        form.instance.organization = tenant_org
        form.instance.company_id = form.cleaned_data.get('company').pk if form.cleaned_data.get('company') else None
        form.instance.created_by = owner
        response = super().form_valid(form)
        self.save_requirements(self.object, form)
        messages.success(self.request, gettext_lazy('Certificação criada com sucesso.'))
        return response


class CertificationUpdateView(CertificationFormMixin, UpdateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'console/certification_form.html'
    success_url = reverse_lazy('console:certification-list')

    def get_queryset(self):
        return self.scoped_certifications()

    def form_valid(self, form):
        response = super().form_valid(form)
        self.save_requirements(self.object, form)
        messages.success(self.request, gettext_lazy('Certificação atualizada com sucesso.'))
        return response


class CertificationDetailView(CertificationScopeMixin, DetailView):
    model = Certification
    template_name = 'console/certification_detail.html'
    context_object_name = 'certification'

    def get_queryset(self):
        return self.scoped_certifications().prefetch_related('requirements', 'awards')
