from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from audience.models import AudiencePolicy, AudienceRule
from configuration.models import (
    BusinessChannel, BusinessUnit, Company, JobFunction, ManagementAssignment, Membership, OrganizationTerminology, PersonType,
    OperationalUnit, Organization,
)
from courses.models import Content, Course
from publishing.models import Publication
from documents.models import Document, DocumentLink
from django.contrib.contenttypes.models import ContentType
from learning.models import ContentTrail, TrailAssignment


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


class AudienceTargetingMixin:
    """Human-friendly hierarchy selectors that compile to AudienceRules."""

    def __init__(self, *args, **kwargs):
        organization_queryset = kwargs.pop('organization_queryset', None)
        super().__init__(*args, **kwargs)
        if organization_queryset is not None and 'organization' in self.fields:
            self.fields['organization'].queryset = organization_queryset
        self.fields['companies'] = forms.ModelMultipleChoiceField(queryset=Company.objects.none(), required=False, label='Empresas')
        self.fields['business_units'] = forms.ModelMultipleChoiceField(queryset=BusinessUnit.objects.none(), required=False, label='Business units')
        self.fields['operational_units'] = forms.ModelMultipleChoiceField(queryset=OperationalUnit.objects.none(), required=False, label='Unidades operacionais')
        self.fields['channels'] = forms.ModelMultipleChoiceField(queryset=BusinessChannel.objects.none(), required=False, label='Business channels')
        self.fields['functions'] = forms.ModelMultipleChoiceField(queryset=JobFunction.objects.none(), required=False, label='Funções')
        for name in ('companies', 'business_units', 'operational_units', 'channels', 'functions'):
            self.fields[name].widget.attrs.update({'size': 5})

    def _target_ids(self, name):
        if self.is_bound:
            return self.data.getlist(self.add_prefix(name))
        return [str(value) for value in self.initial.get(name, [])]

    def _setup_target_querysets(self):
        organization_id = self.data.get(self.add_prefix('organization')) if self.is_bound else getattr(self.instance, 'organization_id', None)
        company_ids = self._target_ids('companies')
        business_unit_ids = self._target_ids('business_units')
        self.fields['companies'].queryset = Company.objects.filter(active=True, organization_id=organization_id) if organization_id else Company.objects.filter(active=True)
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
        if organization and any(org_id != organization.id for org_id in organizations):
            self.add_error('companies', 'As empresas precisam pertencer à organização selecionada.')
        if not organization and len(organizations) == 1:
            cleaned['organization'] = Organization.objects.get(pk=organizations.pop())
            organization = cleaned['organization']
        company_ids = {company.id for company in companies}
        if any(unit.company_id not in company_ids for unit in business_units):
            self.add_error('business_units', 'Selecione apenas unidades das empresas escolhidas.')
        business_unit_ids = {unit.id for unit in business_units}
        if any(unit.business_unit_id not in business_unit_ids for unit in operational_units):
            self.add_error('operational_units', 'Selecione apenas unidades operacionais das unidades escolhidas.')
        if any(channel.company_id not in company_ids for channel in channels):
            self.add_error('channels', 'Selecione apenas canais das empresas escolhidas.')
        if any(function.company_id not in company_ids for function in functions):
            self.add_error('functions', 'Selecione apenas funções das empresas escolhidas.')
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
            raise forms.ValidationError('Selecione uma audiência ou um usuário para atribuir a trilha.')
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
        organization_queryset = kwargs.pop('organization_queryset', None)
        super().__init__(*args, **kwargs)
        self._setup_target_querysets()
        self._load_target_initial()
        self._apply_flowbite_widgets()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == ContentTrail.PUBLISHED and not cleaned.get('organization'):
            self.add_error('organization', 'Uma trilha publicada precisa de uma organização.')
        return self._clean_targets(cleaned)


class PublicationForm(AudienceTargetingMixin, FlowbiteFormMixin, forms.ModelForm):
    documents = forms.ModelMultipleChoiceField(
        queryset=Document.objects.filter(status=Document.PUBLISHED), required=False,
        label='Documentos vinculados', widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    class Meta:
        model = Publication
        fields = (
            'kind', 'organization', 'title', 'slug', 'excerpt', 'body', 'image', 'video_url', 'tags', 'status', 'published_at', 'expires_at', 'points_per_view', 'importance', 'content_category', 'requires_acknowledgement', 'reminder_hours',
        )
        widgets = {
            'body': forms.Textarea(attrs={'rows': 12}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == Publication.PUBLISHED and not cleaned.get('published_at'):
            cleaned['published_at'] = timezone.now()
        return cleaned

    def __init__(self, *args, **kwargs):
        documents_queryset = kwargs.pop('documents_queryset', None)
        super().__init__(*args, **kwargs)
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
                DocumentLink(document=document, content_type=content_type, object_id=instance.pk, created_by=instance.author)
                for document in self.cleaned_data.get('documents', [])
            ])
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
        self._apply_flowbite_widgets()


class AudienceSimulationForm(AudienceTargetingMixin, FlowbiteFormMixin, forms.Form):
    """The same hierarchy selectors used by content forms, for previewing reach."""

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(active=True), required=False, label='Organização'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = None
        self._setup_target_querysets()
        self._apply_flowbite_widgets()


class MembershipAssignmentForm(FlowbiteFormMixin, forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=True, label='Usuários', widget=forms.SelectMultiple(attrs={'size': 8}),
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(active=True), required=True, label='Organização'
    )
    person_type = forms.ModelChoiceField(queryset=PersonType.objects.none(), required=False, label='Tipo de pessoa')
    companies = forms.ModelMultipleChoiceField(queryset=Company.objects.none(), required=True, label='Empresas', widget=forms.SelectMultiple(attrs={'size': 6}))
    business_units = forms.ModelMultipleChoiceField(queryset=BusinessUnit.objects.none(), required=False, label='Business units', widget=forms.SelectMultiple(attrs={'size': 6}))
    operational_units = forms.ModelMultipleChoiceField(queryset=OperationalUnit.objects.none(), required=False, label='Unidades operacionais', widget=forms.SelectMultiple(attrs={'size': 6}))
    channels = forms.ModelMultipleChoiceField(queryset=BusinessChannel.objects.none(), required=False, label='Business channels (opcional)', widget=forms.SelectMultiple(attrs={'size': 6}))
    functions = forms.ModelMultipleChoiceField(queryset=JobFunction.objects.none(), required=False, label='Funções', widget=forms.SelectMultiple(attrs={'size': 6}))

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
                self.add_error('business_units', 'As unidades devem pertencer às empresas selecionadas.')
        for item in cleaned.get('operational_units') or []:
            if item.business_unit_id not in {unit.pk for unit in cleaned.get('business_units') or []}:
                self.add_error('operational_units', 'As unidades operacionais devem pertencer às business units selecionadas.')
        for item in (cleaned.get('channels') or []):
            if item.company_id not in company_ids:
                self.add_error('channels', 'Os canais devem pertencer às empresas selecionadas.')
        for item in (cleaned.get('functions') or []):
            if item.company_id not in company_ids:
                self.add_error('functions', 'As funções devem pertencer às empresas selecionadas.')
        return cleaned


class AudienceRuleForm(FlowbiteFormMixin, forms.ModelForm):
    values = forms.CharField(
        label='Valores', required=False,
        help_text='IDs separados por vírgula. Ex.: 1, 4, 8.',
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
        label='Documentos relacionados', widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    class Meta:
        model = Course
        fields = (
            'type', 'state', 'organization', 'subject', 'title', 'slug', 'overview', 'banner', 'published_date', 'points_per_enrollment',
            'points_per_completation', 'go_live_at', 'expire_at', 'importance', 'content_category', 'requires_acknowledgement',
        )
        widgets = {
            'overview': forms.Textarea(attrs={'rows': 8}),
            'published_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'go_live_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expire_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        documents_queryset = kwargs.pop('documents_queryset', None)
        super().__init__(*args, **kwargs)
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
            'organization', 'company', 'person_type', 'business_unit', 'operational_unit',
            'channels', 'functions', 'is_primary', 'active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self._apply_flowbite_widgets()


class PersonTypeForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = PersonType
        fields = ('code', 'name', 'description', 'active', 'position')
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()


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
            self.add_error('company', 'A empresa precisa pertencer à organização selecionada.')
        if business_unit and (not company or business_unit.company_id != company.pk):
            self.add_error('business_unit', 'A business unit precisa pertencer à empresa selecionada.')
        if operational_unit and (not business_unit or operational_unit.business_unit_id != business_unit.pk):
            self.add_error('operational_unit', 'A unidade operacional precisa pertencer à business unit selecionada.')
        return cleaned
