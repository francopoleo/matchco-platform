from django.utils.translation import gettext_lazy as gettext_lazy
import json

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from audience.models import AudiencePolicy, AudienceRule
from matchco.core.utils import get_tenant_organization
from tenants_core.models import TenantCompany, TenantOrganization
from configuration.models import (
    BusinessChannel, BusinessUnit, Company, JobFunction, ManagementAssignment, Membership, OrganizationTerminology, PersonType,
    OperationalUnit, Organization, Domain, IntegrationConnection, GroupHierarchyType, GroupNode,
)
from courses.models import Content, Course, Quiz, Subject
from publishing.models import Publication
from documents.models import Document, DocumentLink
from documents.services import sync_media_usage
from django.contrib.contenttypes.models import ContentType
from learning.models import Certification, ContentTrail, TrailAssignment


User = get_user_model()


FIELD_CLASSES = (
    'block w-full rounded-md border border-default-medium bg-neutral-secondary-medium '
    'px-3 py-2.5 text-sm text-heading shadow-sm placeholder:text-body '
    'focus:border-brand focus:ring-brand'
)
SELECT_CLASSES = FIELD_CLASSES + ' appearance-none'
CHECKBOX_CLASSES = 'h-4 w-4 rounded-sm border border-default-medium bg-neutral-secondary-medium text-fg-brand focus:ring-2 focus:ring-brand-soft'


class FlowbiteFormMixin:
    def _apply_flowbite_widgets(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = CHECKBOX_CLASSES
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs['class'] = SELECT_CLASSES
            elif isinstance(widget, forms.FileInput):
                widget.attrs['class'] = FIELD_CLASSES + ' file:me-4 file:rounded-base file:border-0 file:bg-brand-softer file:px-4 file:py-2 file:text-sm file:font-semibold file:text-fg-brand-strong'
            else:
                widget.attrs['class'] = FIELD_CLASSES


class CourseSubjectForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = Subject
        fields = ('title', 'slug')
        labels = {'title': gettext_lazy('Nome da categoria'), 'slug': gettext_lazy('Identificador da URL')}
        help_texts = {'slug': gettext_lazy('Opcional. Se ficar vazio, será criado a partir do nome.')}

    def clean_slug(self):
        from django.utils.text import slugify
        return slugify(self.cleaned_data.get('slug') or self.cleaned_data.get('title') or '')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()


class AudienceTargetingMixin:
    """Human-friendly hierarchy selectors that compile to AudienceRules."""

    def __init__(self, *args, **kwargs):
        organization_queryset = kwargs.pop('organization_queryset', None)
        self.company_queryset = kwargs.pop('company_queryset', None)
        self.default_company_id = kwargs.pop('default_company_id', None)
        self.default_organization_id = kwargs.pop('default_organization_id', None)
        super().__init__(*args, **kwargs)
        if organization_queryset is not None and 'organization' in self.fields:
            self.fields['organization'].queryset = organization_queryset
        self.fields['companies'] = forms.ModelMultipleChoiceField(queryset=Company.objects.none(), required=False, label=gettext_lazy('Empresas'))
        self.fields['business_units'] = forms.ModelMultipleChoiceField(queryset=BusinessUnit.objects.none(), required=False, label=gettext_lazy('Unidades de negócio'))
        self.fields['operational_units'] = forms.ModelMultipleChoiceField(queryset=OperationalUnit.objects.none(), required=False, label=gettext_lazy('Unidades operacionais'))
        self.fields['channels'] = forms.ModelMultipleChoiceField(queryset=BusinessChannel.objects.none(), required=False, label=gettext_lazy('Canais de negócio'))
        self.fields['functions'] = forms.ModelMultipleChoiceField(queryset=JobFunction.objects.none(), required=False, label=gettext_lazy('Funções'))
        for name in ('companies', 'business_units', 'operational_units', 'channels', 'functions'):
            self.fields[name].widget.attrs.update({'size': 5})

    def _target_ids(self, name):
        if self.is_bound:
            return self.data.getlist(self.add_prefix(name))
        return [str(value) for value in self.initial.get(name, [])]

    def _setup_target_querysets(self):
        organization_id = self.data.get(self.add_prefix('organization')) if self.is_bound else (
            getattr(self.instance, 'organization_id', None)
            or self.initial.get('organization')
            or self.default_organization_id
        )
        if self.fields.get('organization') and self.fields['organization'].queryset.model is TenantOrganization and organization_id:
            organization_id = TenantOrganization.objects.filter(pk=organization_id).values_list('organization_id', flat=True).first()
        company_ids = self._target_ids('companies')
        business_unit_ids = self._target_ids('business_units')
        if self.company_queryset is not None:
            self.fields['companies'].queryset = self.company_queryset
        else:
            self.fields['companies'].queryset = Company.objects.filter(active=True, organization_id=organization_id) if organization_id else Company.objects.none()
        if company_ids:
            self.fields['business_units'].queryset = BusinessUnit.objects.filter(active=True, company_id__in=company_ids)
            self.fields['channels'].queryset = BusinessChannel.objects.filter(active=True, company_id__in=company_ids)
            self.fields['functions'].queryset = JobFunction.objects.filter(active=True, company_id__in=company_ids)
        else:
            self.fields['business_units'].queryset = BusinessUnit.objects.none()
            self.fields['channels'].queryset = BusinessChannel.objects.none()
            self.fields['functions'].queryset = JobFunction.objects.none()
        self.fields['operational_units'].queryset = OperationalUnit.objects.filter(active=True, business_unit_id__in=business_unit_ids) if business_unit_ids else OperationalUnit.objects.none()

    def _load_target_initial(self):
        policy = getattr(self.instance, 'audience_policy', None)
        if not policy:
            return
        for rule in policy.rules.all():
            key = {
                AudienceRule.COMPANY: 'companies',
                AudienceRule.BUSINESS_UNIT: 'business_units',
                AudienceRule.OPERATIONAL_UNIT: 'operational_units',
                AudienceRule.CHANNEL: 'channels',
                AudienceRule.FUNCTION: 'functions',
            }.get(rule.dimension)
            if key:
                self.initial[key] = rule.values

    def _clean_targets(self, cleaned):
        organization = cleaned.get('organization')
        companies = cleaned.get('companies') or []
        business_units = cleaned.get('business_units') or []
        operational_units = cleaned.get('operational_units') or []
        channels = cleaned.get('channels') or []
        functions = cleaned.get('functions') or []
        organizations = {company.organization_id for company in companies}
        organization_key = getattr(organization, 'organization_id', None) or getattr(organization, 'id', None)
        if organization and any(org_id != organization_key for org_id in organizations):
            self.add_error('companies', gettext_lazy('As empresas precisam pertencer à organização selecionada.'))
        if not organization and len(organizations) == 1:
            org_id = organizations.pop()
            tenant_org = TenantOrganization.objects.filter(organization_id=org_id).first()
            if tenant_org:
                cleaned['organization'] = tenant_org
                organization = tenant_org
        company_ids = {company.id for company in companies}
        if any(unit.company_id not in company_ids for unit in business_units):
            self.add_error('business_units', gettext_lazy('Selecione apenas unidades das empresas escolhidas.'))
        business_unit_ids = {unit.id for unit in business_units}
        if any(unit.business_unit_id not in business_unit_ids for unit in operational_units):
            self.add_error('operational_units', gettext_lazy('Selecione apenas unidades operacionais das unidades escolhidas.'))
        if any(channel.company_id not in company_ids for channel in channels):
            self.add_error('channels', gettext_lazy('Selecione apenas canais das empresas escolhidas.'))
        if any(function.company_id not in company_ids for function in functions):
            self.add_error('functions', gettext_lazy('Selecione apenas funções das empresas escolhidas.'))
        return cleaned

    def clean(self):
        cleaned = super().clean()
        return self._clean_targets(cleaned)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            self._save_audience(instance)
        return instance

    def _save_audience(self, instance):
        organization = self.cleaned_data.get('organization')
        if organization and not isinstance(organization, TenantOrganization):
            organization = get_tenant_organization(organization)
        dimensions = (
            (AudienceRule.COMPANY, self.cleaned_data.get('companies')),
            (AudienceRule.BUSINESS_UNIT, self.cleaned_data.get('business_units')),
            (AudienceRule.OPERATIONAL_UNIT, self.cleaned_data.get('operational_units')),
            (AudienceRule.CHANNEL, self.cleaned_data.get('channels')),
            (AudienceRule.FUNCTION, self.cleaned_data.get('functions')),
        )
        if not organization and not any(values for _, values in dimensions):
            instance.audience_policy = None
            type(instance).objects.filter(pk=instance.pk).update(organization=None, audience_policy=None)
            return
        instance.organization = organization
        if not any(values for _, values in dimensions):
            instance.audience_policy = None
            type(instance).objects.filter(pk=instance.pk).update(organization_id=getattr(organization, 'id', None), audience_policy=None)
            return
        policy = instance.audience_policy or AudiencePolicy()
        policy.name = f'Audiência · {instance.title}'
        policy.organization = organization
        policy.description = 'Gerada pela segmentação do conteúdo.'
        policy.match_mode = AudiencePolicy.ALL
        policy.active = True
        policy.save()
        policy.rules.all().delete()
        for position, (dimension, values) in enumerate(dimensions):
            if values:
                AudienceRule.objects.create(policy=policy, dimension=dimension, values=[str(item.pk) for item in values], position=position)
        instance.audience_policy = policy
        type(instance).objects.filter(pk=instance.pk).update(
            organization_id=getattr(organization, 'id', None), audience_policy_id=policy.id
        )


class TrailAssignmentForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = TrailAssignment
        fields = ('trail', 'audience_policy', 'user', 'due_at')
        widgets = {
            'due_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('audience_policy') and not cleaned.get('user'):
            raise forms.ValidationError(gettext_lazy('Selecione uma audiência ou um usuário para atribuir a trilha.'))
        return cleaned


class TrailForm(AudienceTargetingMixin, FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = ContentTrail
        fields = ('organization', 'title', 'slug', 'objective', 'trail_type', 'status', 'version', 'valid_until')
        widgets = {
            'objective': forms.Textarea(attrs={'rows': 3}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_target_initial()
        self._setup_target_querysets()
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == ContentTrail.PUBLISHED and not cleaned.get('organization'):
            self.add_error('organization', gettext_lazy('Uma trilha publicada precisa de uma organização.'))
        return self._clean_targets(cleaned)


class CertificationForm(FlowbiteFormMixin, forms.ModelForm):
    required_courses = forms.ModelMultipleChoiceField(queryset=Course.objects.none(), required=False, label=gettext_lazy('Cursos obrigatórios'))
    required_quizzes = forms.ModelMultipleChoiceField(queryset=Quiz.objects.none(), required=False, label=gettext_lazy('Avaliações obrigatórias'))

    class Meta:
        model = Certification
        fields = ('company', 'title', 'slug', 'description', 'status', 'version', 'validity_days', 'minimum_score', 'maximum_attempts', 'minimum_active_seconds', 'requires_manual_approval', 'starts_at', 'ends_at')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, courses=None, quizzes=None, company_queryset=None, default_company_id=None, company_required=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].required = company_required
        if company_queryset is not None:
            self.fields['company'].queryset = TenantCompany.objects.filter(company_id__in=company_queryset.values_list('pk', flat=True))
        if default_company_id and not self.is_bound and not self.instance.pk:
            self.initial['company'] = default_company_id
        self.fields['required_courses'].queryset = courses or Course.objects.none()
        self.fields['required_quizzes'].queryset = quizzes or Quiz.objects.none()
        if self.instance and self.instance.pk:
            self.initial['required_courses'] = self.instance.requirements.filter(course__isnull=False).values_list('course_id', flat=True)
            self.initial['required_quizzes'] = self.instance.requirements.filter(quiz__isnull=False).values_list('quiz_id', flat=True)
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        company = cleaned.get('company')
        company_id = company.pk if company else None
        for course in cleaned.get('required_courses', []):
            if course.company_id not in (None, company_id):
                self.add_error('required_courses', gettext_lazy('Os cursos obrigatórios precisam ser compartilhados pela organização ou pertencer à mesma empresa da certificação.'))
                break
        return cleaned


class PublicationForm(AudienceTargetingMixin, FlowbiteFormMixin, forms.ModelForm):
    company = forms.ModelChoiceField(queryset=TenantCompany.objects.none(), required=False, label=gettext_lazy('Empresa responsável'))
    documents = forms.ModelMultipleChoiceField(
        queryset=Document.objects.filter(status=Document.PUBLISHED), required=False,
        label=gettext_lazy('Documentos vinculados'), widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    class Meta:
        model = Publication
        fields = (
            'kind', 'organization', 'company', 'title', 'slug', 'excerpt', 'body', 'image', 'video_url', 'tags', 'status', 'published_at', 'expires_at', 'points_per_view', 'importance', 'content_category', 'requires_acknowledgement', 'reminder_hours', 'requires_approval', 'version', 'change_summary',
        )
        widgets = {
            'body': forms.Textarea(attrs={'rows': 12, 'data-rich-editor': 'true', 'class': 'rich-editor'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == Publication.PUBLISHED and not cleaned.get('published_at'):
            # Editing an already published item must not reset its original
            # publication moment just because the optional datetime input was
            # left blank by the browser.
            cleaned['published_at'] = (
                self.instance.published_at
                if self.instance and self.instance.pk and self.instance.published_at
                else timezone.now()
            )
        return cleaned

    def __init__(self, *args, **kwargs):
        documents_queryset = kwargs.pop('documents_queryset', None)
        company_queryset = kwargs.get('company_queryset')
        default_company_id = kwargs.get('default_company_id')
        company_required = kwargs.pop('company_required', False)
        super().__init__(*args, **kwargs)
        self.fields['company'].required = company_required
        if company_queryset is not None:
            ids = company_queryset.values_list('pk', flat=True)
            self.fields['company'].queryset = TenantCompany.objects.filter(company_id__in=ids)
        if default_company_id and not self.is_bound and not self.instance.pk:
            self.initial['company'] = default_company_id
        if documents_queryset is not None:
            self.fields['documents'].queryset = documents_queryset
        self._load_target_initial()
        self._setup_target_querysets()
        # Versioning is managed by the publication workflow and is not an
        # editable field in the form. Keeping it optional prevents an omitted
        # hidden workflow field from blocking every save.
        self.fields['version'].required = False
        self.fields['version'].widget = forms.HiddenInput()
        if self.instance and self.instance.pk:
            content_type = ContentType.objects.get_for_model(self.instance)
            self.initial['documents'] = Document.objects.filter(
                links__content_type=content_type, links__object_id=self.instance.pk,
            )
        self._apply_flowbite_widgets()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            # Keep the audit timestamp reliable for console edits, including
            # saves where Django detects no changed model field.
            now = timezone.now()
            Publication.objects.filter(pk=instance.pk).update(updated_at=now)
            instance.updated_at = now
            content_type = ContentType.objects.get_for_model(instance)
            DocumentLink.objects.filter(content_type=content_type, object_id=instance.pk).delete()
            DocumentLink.objects.bulk_create([
                DocumentLink(document=document, content_type=content_type, object_id=instance.pk, created_by=instance.author)
                for document in self.cleaned_data.get('documents', [])
            ])
            sync_media_usage(instance, instance.body, actor=instance.author, field_name='body')
        return instance


class AudiencePolicyForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = AudiencePolicy
        fields = ('name', 'organization', 'description', 'match_mode', 'active')
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        organization_queryset = kwargs.pop('organization_queryset', None)
        super().__init__(*args, **kwargs)
        if organization_queryset is not None:
            self.fields['organization'].queryset = organization_queryset
        self.fields['name'].label = gettext_lazy('Nome da política')
        self.fields['organization'].label = gettext_lazy('Organização')
        self.fields['description'].label = gettext_lazy('Descrição')
        self.fields['match_mode'].label = gettext_lazy('Modo de correspondência')
        self.fields['match_mode'].choices = (
            (AudiencePolicy.ALL, gettext_lazy('Todas as regras')),
            (AudiencePolicy.ANY, gettext_lazy('Qualquer regra')),
        )
        self.fields['active'].label = gettext_lazy('Política ativa')
        self._apply_flowbite_widgets()


class AudienceSimulationForm(AudienceTargetingMixin, FlowbiteFormMixin, forms.Form):
    """The same hierarchy selectors used by content forms, for previewing reach."""

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(active=True), required=False, label=gettext_lazy('Organização')
    )

    def __init__(self, *args, **kwargs):
        default_organization_id = kwargs.get('default_organization_id')
        super().__init__(*args, **kwargs)
        self.instance = None
        if default_organization_id and not self.is_bound:
            self.initial['organization'] = default_organization_id
        self._setup_target_querysets()
        self._apply_flowbite_widgets()


class MembershipAssignmentForm(FlowbiteFormMixin, forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=True, label=gettext_lazy('Usuários'), widget=forms.SelectMultiple(attrs={'size': 8}),
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(active=True), required=True, label=gettext_lazy('Organização')
    )
    person_type = forms.ModelChoiceField(queryset=PersonType.objects.none(), required=False, label=gettext_lazy('Tipo de pessoa'))
    companies = forms.ModelMultipleChoiceField(queryset=Company.objects.none(), required=True, label=gettext_lazy('Empresas'), widget=forms.SelectMultiple(attrs={'size': 6}))
    business_units = forms.ModelMultipleChoiceField(queryset=BusinessUnit.objects.none(), required=False, label=gettext_lazy('Business units'), widget=forms.SelectMultiple(attrs={'size': 6}))
    operational_units = forms.ModelMultipleChoiceField(queryset=OperationalUnit.objects.none(), required=False, label=gettext_lazy('Unidades operacionais'), widget=forms.SelectMultiple(attrs={'size': 6}))
    channels = forms.ModelMultipleChoiceField(queryset=BusinessChannel.objects.none(), required=False, label=gettext_lazy('Business channels (opcional)'), widget=forms.SelectMultiple(attrs={'size': 6}))
    functions = forms.ModelMultipleChoiceField(queryset=JobFunction.objects.none(), required=False, label=gettext_lazy('Funções'), widget=forms.SelectMultiple(attrs={'size': 6}))

    def __init__(self, *args, **kwargs):
        user_queryset = kwargs.pop('user_queryset', None)
        super().__init__(*args, **kwargs)
        if user_queryset is not None:
            self.fields['users'].queryset = user_queryset
        organization_id = self.data.get('organization') if self.is_bound else None
        company_ids = self.data.getlist('companies') if self.is_bound else []
        unit_ids = self.data.getlist('business_units') if self.is_bound else []
        self.fields['companies'].queryset = Company.objects.filter(active=True, organization_id=organization_id) if organization_id else Company.objects.none()
        self.fields['person_type'].queryset = PersonType.objects.filter(active=True, organization_id=organization_id) if organization_id else PersonType.objects.none()
        self.fields['business_units'].queryset = BusinessUnit.objects.filter(active=True, company_id__in=company_ids) if company_ids else BusinessUnit.objects.none()
        self.fields['channels'].queryset = BusinessChannel.objects.filter(active=True, company_id__in=company_ids) if company_ids else BusinessChannel.objects.none()
        self.fields['functions'].queryset = JobFunction.objects.filter(active=True, company_id__in=company_ids) if company_ids else JobFunction.objects.none()
        self.fields['operational_units'].queryset = OperationalUnit.objects.filter(active=True, business_unit_id__in=unit_ids) if unit_ids else OperationalUnit.objects.none()
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        companies = cleaned.get('companies') or []
        company_ids = {item.pk for item in companies}
        for item in cleaned.get('business_units') or []:
            if item.company_id not in company_ids:
                self.add_error('business_units', gettext_lazy('As unidades devem pertencer às empresas selecionadas.'))
        for item in cleaned.get('operational_units') or []:
            if item.business_unit_id not in {unit.pk for unit in cleaned.get('business_units') or []}:
                self.add_error('operational_units', gettext_lazy('As unidades operacionais devem pertencer às business units selecionadas.'))
        for item in (cleaned.get('channels') or []):
            if item.company_id not in company_ids:
                self.add_error('channels', gettext_lazy('Os canais devem pertencer às empresas selecionadas.'))
        for item in (cleaned.get('functions') or []):
            if item.company_id not in company_ids:
                self.add_error('functions', gettext_lazy('As funções devem pertencer às empresas selecionadas.'))
        return cleaned


class AudienceRuleForm(FlowbiteFormMixin, forms.ModelForm):
    values = forms.CharField(
        label=gettext_lazy('Valores'), required=False,
        help_text=gettext_lazy('IDs separados por vírgula. Ex.: 1, 4, 8.'),
    )

    class Meta:
        model = AudienceRule
        fields = ('dimension', 'operator', 'values', 'negate', 'position')
        widgets = {'position': forms.NumberInput(attrs={'min': 0})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dimension'].choices = [(value, value.replace('_', ' ').title()) for value in AudienceRule.DIMENSIONS]
        if self.instance and self.instance.pk:
            self.initial['values'] = ', '.join(str(value) for value in self.instance.values)
        self._apply_flowbite_widgets()

    def clean_values(self):
        raw = self.cleaned_data.get('values', '')
        return [value.strip() for value in raw.split(',') if value.strip()]


class CourseConsoleForm(AudienceTargetingMixin, FlowbiteFormMixin, forms.ModelForm):
    documents = forms.ModelMultipleChoiceField(
        queryset=Document.objects.filter(status=Document.PUBLISHED), required=False,
        label=gettext_lazy('Documentos relacionados'), widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    class Meta:
        model = Course
        fields = (
            'type', 'state', 'organization', 'company', 'subject', 'title', 'slug', 'overview', 'banner', 'published_date', 'points_per_enrollment',
            'points_per_completation', 'go_live_at', 'expire_at', 'importance', 'content_category', 'requires_acknowledgement',
        )
        widgets = {
            'overview': forms.Textarea(attrs={'rows': 8, 'data-rich-editor': 'true', 'class': 'rich-editor'}),
            'published_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'go_live_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expire_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        documents_queryset = kwargs.pop('documents_queryset', None)
        company_queryset = kwargs.get('company_queryset')
        default_company_id = kwargs.get('default_company_id')
        company_required = kwargs.pop('company_required', False)
        super().__init__(*args, **kwargs)
        self.fields['company'].required = company_required
        if company_queryset is not None:
            ids = company_queryset.values_list('pk', flat=True)
            self.fields['company'].queryset = TenantCompany.objects.filter(company_id__in=ids)
        if default_company_id and not self.is_bound and not self.instance.pk:
            self.initial['company'] = default_company_id
        self.fields['overview'].help_text = gettext_lazy('Use a barra de ferramentas para formatar o conteúdo. Não é necessário escrever HTML.')
        if documents_queryset is not None:
            self.fields['documents'].queryset = documents_queryset
        self._load_target_initial()
        self._setup_target_querysets()
        if self.instance and self.instance.pk:
            content_type = ContentType.objects.get_for_model(self.instance)
            self.initial['documents'] = Document.objects.filter(
                links__content_type=content_type, links__object_id=self.instance.pk,
            )
        self._apply_flowbite_widgets()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            content_type = ContentType.objects.get_for_model(instance)
            DocumentLink.objects.filter(content_type=content_type, object_id=instance.pk).delete()
            DocumentLink.objects.bulk_create([
                DocumentLink(document=document, content_type=content_type, object_id=instance.pk, created_by=instance.owner)
                for document in self.cleaned_data.get('documents', [])
            ])
        return instance



User = get_user_model()


class ConsoleUserForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()


class MembershipForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = Membership
        fields = (
            'organization', 'company', 'role', 'person_type', 'business_unit', 'operational_unit',
            'channels', 'functions', 'is_primary', 'active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].label = gettext_lazy('Papel de acesso')
        self.fields['role'].help_text = gettext_lazy('Define o que a pessoa pode administrar dentro desta organização.')
        self.fields['organization'].label = gettext_lazy('Organização')
        self.fields['company'].label = gettext_lazy('Empresa / unidade de negócio')
        self._apply_flowbite_widgets()


class OrganizationTerminologyForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = OrganizationTerminology
        fields = (
            'level_1_label', 'level_1_description',
            'level_2_label', 'level_2_description',
            'level_3_label', 'level_3_description',
        )
        widgets = {
            'level_1_description': forms.Textarea(attrs={'rows': 2}),
            'level_2_description': forms.Textarea(attrs={'rows': 2}),
            'level_3_description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_copy = {
            'level_1_label': ('Nível 1 — organização principal', 'Quem controla ou representa a operação. Ex.: Grupo, Shopping, Fabricante, Hospital.'),
            'level_1_description': ('Como explicar o nível 1', 'Descrição curta que aparece para administradores e orienta o cadastro.'),
            'level_2_label': ('Nível 2 — unidade de negócio', 'Onde a operação acontece. Ex.: Bandeira, Hospital, Distribuidor, Região.'),
            'level_2_description': ('Como explicar o nível 2', 'Descrição curta para ajudar o operador a escolher o nível correto.'),
            'level_3_label': ('Nível 3 — unidade operacional', 'A unidade ou equipe que executa o trabalho. Ex.: Loja, Unidade, Serviço, Departamento.'),
            'level_3_description': ('Como explicar o nível 3', 'Descrição curta para orientar lojas, equipes e áreas locais.'),
        }
        for name, (label, help_text) in field_copy.items():
            self.fields[name].label = label
            self.fields[name].help_text = help_text
        self._apply_flowbite_widgets()


class PersonTypeForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = PersonType
        fields = ('code', 'name', 'description', 'active', 'position')
        labels = {
            'code': gettext_lazy('Código interno'),
            'name': gettext_lazy('Nome do tipo'),
            'description': gettext_lazy('Descrição'),
            'active': gettext_lazy('Disponível para uso'),
            'position': gettext_lazy('Ordem de exibição'),
        }
        help_texts = {
            'code': gettext_lazy('Identificador usado em importações e integrações. Use letras, números e hífens.'),
            'name': gettext_lazy('Como este vínculo será apresentado para administradores e pessoas.'),
            'active': gettext_lazy('Desative para deixar de oferecer este tipo sem apagar o histórico.'),
            'position': gettext_lazy('Menor número aparece primeiro.'),
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self._apply_flowbite_widgets()

    def clean_code(self):
        code = self.cleaned_data['code']
        if self.organization:
            existing = PersonType.objects.filter(organization=self.organization, code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(gettext_lazy('Já existe um tipo de pessoa com este código nesta organização.'))
        return code


class ManagementAssignmentForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = ManagementAssignment
        fields = ('user', 'organization', 'company', 'business_unit', 'operational_unit', 'role', 'active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['organization'].queryset = Organization.objects.filter(active=True)
        self.fields['company'].queryset = Company.objects.filter(active=True)
        self.fields['business_unit'].queryset = BusinessUnit.objects.filter(active=True)
        self.fields['operational_unit'].queryset = OperationalUnit.objects.filter(active=True)
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        organization = cleaned.get('organization')
        company = cleaned.get('company')
        business_unit = cleaned.get('business_unit')
        operational_unit = cleaned.get('operational_unit')
        if company and company.organization_id != organization.pk:
            self.add_error('company', gettext_lazy('A empresa precisa pertencer à organização selecionada.'))
        if business_unit and (not company or business_unit.company_id != company.pk):
            self.add_error('business_unit', gettext_lazy('A business unit precisa pertencer à empresa selecionada.'))
        if operational_unit and (not business_unit or operational_unit.business_unit_id != business_unit.pk):
            self.add_error('operational_unit', gettext_lazy('A unidade operacional precisa pertencer à business unit selecionada.'))
        return cleaned


class GroupHierarchyTypeForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = GroupHierarchyType
        fields = ('code', 'name', 'description', 'max_levels', 'allow_links', 'auto_create_on', 'active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override auto_create_on to be a ChoiceField
        self.fields['auto_create_on'] = forms.ChoiceField(
            required=False,
            choices=[
                ('', gettext_lazy('Somente criação manual')),
                ('graduation', gettext_lazy('Conclusão de graduação')),
                ('custom', gettext_lazy('Gatilho personalizado')),
            ],
            label=gettext_lazy('Gatilho de criação automática'),
        )
        self._apply_flowbite_widgets()

    def clean_code(self):
        code = self.cleaned_data.get('code', '').lower().strip()
        if not code:
            raise forms.ValidationError(gettext_lazy('O código é obrigatório.'))
        if not code.replace('_', '').isalnum():
            raise forms.ValidationError(gettext_lazy('O código só pode conter letras, números e sublinhados.'))
        return code


class GroupNodeForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = GroupNode
        fields = ('name', 'code', 'description', 'parent_node', 'level', 'active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, hierarchy_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hierarchy_type = hierarchy_type
        if hierarchy_type:
            # Filter parent_node choices to only nodes in the same hierarchy
            self.fields['parent_node'].queryset = GroupNode.objects.filter(
                hierarchy_type=hierarchy_type
            ).order_by('level', 'name')
            # Set max level hint
            max_level = hierarchy_type.max_levels
            if max_level:
                self.fields['level'].help_text = f'Máximo: {max_level}'
        else:
            self.fields['parent_node'].queryset = GroupNode.objects.none()
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        if not self.hierarchy_type:
            raise forms.ValidationError(gettext_lazy('Hierarchy type is required'))

        level = cleaned.get('level')
        parent_node = cleaned.get('parent_node')
        max_levels = self.hierarchy_type.max_levels

        if max_levels and level and level > max_levels:
            self.add_error('level', f'Level cannot exceed {max_levels}')

        if parent_node and parent_node.hierarchy_type_id != self.hierarchy_type.id:
            self.add_error('parent_node', gettext_lazy('Parent node must belong to the same hierarchy'))

        if parent_node and level and parent_node.level >= level:
            self.add_error('level', gettext_lazy('Level must be greater than parent node level'))

        return cleaned


class OrganizationOnboardingForm(FlowbiteFormMixin, forms.Form):
    """Single guided setup that creates the first usable organization context."""

    name = forms.CharField(label=gettext_lazy('Nome da organização'), max_length=160)
    slug = forms.SlugField(label=gettext_lazy('Identificador'), max_length=180, help_text=gettext_lazy('Usado em URLs internas e no schema.'))
    market = forms.ChoiceField(label=gettext_lazy('Mercado principal'), choices=Organization.MARKET_CHOICES)
    description = forms.CharField(label=gettext_lazy('Descrição'), required=False, widget=forms.Textarea(attrs={'rows': 3}))
    domain = forms.CharField(label=gettext_lazy('Domínio (opcional)'), required=False, max_length=253, help_text=gettext_lazy('Ex.: empresa.matchco.app'))
    brand_name = forms.CharField(label=gettext_lazy('Nome da marca'), required=False, max_length=160)
    logo_url = forms.URLField(label=gettext_lazy('URL do logo'), required=False)
    favicon_url = forms.URLField(label=gettext_lazy('URL do favicon'), required=False)
    custom_domain = forms.CharField(label=gettext_lazy('Domínio white-label (opcional)'), required=False, max_length=253)
    white_label_enabled = forms.BooleanField(label=gettext_lazy('Ativar white-label'), required=False)
    primary_color = forms.RegexField(label=gettext_lazy('Cor principal'), regex=r'^#[0-9A-Fa-f]{6}$', initial='#f97316')
    company_name = forms.CharField(label=gettext_lazy('Primeira empresa ou grupo'), max_length=160)
    unit_name = forms.CharField(label=gettext_lazy('Primeira unidade ou operação'), required=False, max_length=160)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()

    def clean_slug(self):
        value = self.cleaned_data['slug'].lower().strip()
        if Organization.objects.filter(slug=value).exists():
            raise forms.ValidationError(gettext_lazy('Este identificador já está em uso.'))
        if Organization.objects.filter(schema_name=value[:63]).exists():
            raise forms.ValidationError(gettext_lazy('Este identificador já possui um schema.'))
        return value

    def clean_domain(self):
        value = self.cleaned_data.get('domain', '').strip().lower()
        if value and Domain.objects.filter(domain=value).exists():
            raise forms.ValidationError(gettext_lazy('Este domínio já está cadastrado.'))
        return value

    def clean_custom_domain(self):
        value = self.cleaned_data.get('custom_domain', '').strip().lower()
        if value and Domain.objects.filter(domain=value).exists():
            raise forms.ValidationError(gettext_lazy('Este domínio white-label já está cadastrado.'))
        return value


class IntegrationConnectionForm(FlowbiteFormMixin, forms.ModelForm):
    # Keep the storage JSON-native while giving admins a simple comma/newline
    # editor instead of exposing JSON syntax in the setup screen.
    scopes = forms.CharField(
        required=False,
        label=gettext_lazy('Escopos'),
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'people.read, people.write'}),
        help_text=gettext_lazy('Separe os escopos por vírgula ou uma linha por escopo.'),
    )

    class Meta:
        model = IntegrationConnection
        fields = ('name', 'connection_type', 'provider', 'base_url', 'secret_reference', 'scopes', 'status')
        labels = {
            'name': gettext_lazy('Nome da conexão'),
            'connection_type': gettext_lazy('Tipo de conexão'),
            'provider': gettext_lazy('Provedor'),
            'base_url': gettext_lazy('URL base'),
            'secret_reference': gettext_lazy('Referência do segredo'),
            'status': gettext_lazy('Status'),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self._apply_flowbite_widgets()

    def clean_scopes(self):
        value = (self.cleaned_data.get('scopes') or '').strip()
        if not value:
            return []
        if value.startswith('['):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError(gettext_lazy('Informe uma lista JSON válida ou escopos separados por vírgula.')) from exc
            if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                raise forms.ValidationError(gettext_lazy('Os escopos precisam ser uma lista de textos.'))
            return [item.strip() for item in parsed if item.strip()]
        return [item.strip() for item in value.replace('\n', ',').split(',') if item.strip()]


class OrganizationBrandForm(FlowbiteFormMixin, forms.ModelForm):
    """Editable brand and white-label settings for an existing tenant."""

    class Meta:
        model = Organization
        fields = (
            'name', 'market', 'brand_name', 'logo_url', 'favicon_url',
            'primary_color', 'custom_domain', 'white_label_enabled',
            'default_entry_template', 'onboarding_status',
        )
        labels = {
            'name': gettext_lazy('Nome da organização'),
            'market': gettext_lazy('Mercado'),
            'brand_name': gettext_lazy('Nome da marca'),
            'logo_url': gettext_lazy('URL do logo'),
            'favicon_url': gettext_lazy('URL do favicon'),
            'primary_color': gettext_lazy('Cor principal'),
            'custom_domain': gettext_lazy('Domínio white-label (opcional)'),
            'white_label_enabled': gettext_lazy('Ativar white-label'),
            'default_entry_template': gettext_lazy('Template de entrada padrão'),
            'onboarding_status': gettext_lazy('Status da configuração'),
        }
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-11 w-20 rounded border border-default-medium bg-transparent p-1'}),
            'default_entry_template': forms.Select(choices=(
                ('generic', gettext_lazy('Genérico')), ('shopping', gettext_lazy('Shopping')), ('retail', gettext_lazy('Varejo')),
                ('manufacturer', gettext_lazy('Fabricante')), ('distributor', gettext_lazy('Distribuidor')),
                ('hospital', gettext_lazy('Hospital')),
            )),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()
        self.fields['primary_color'].widget.attrs.update({
            'type': 'color',
            'class': 'h-11 w-20 rounded-md border border-default-medium bg-transparent p-1',
        })
