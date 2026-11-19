from django.utils.translation import gettext_lazy as gettext_lazy
import hashlib
import os

from django import forms
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from matchco.core.utils import get_tenant_organization
from configuration.models import Company, Membership
from audience.models import AudiencePolicy
from tenants_core.models import TenantCompany, TenantOrganization
from .models import Document, DocumentPermission, DocumentVersion, MediaAsset, MediaAssetVersion, MediaCollection, MediaTag
from .services import validate_upload

User = get_user_model()


INPUT_CLASSES = (
    'block w-full rounded-base border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 '
    'text-sm text-heading shadow-xs placeholder:text-body '
    'focus:border-brand focus:ring-2 focus:ring-brand/30'
)
SELECT_CLASSES = INPUT_CLASSES + ' appearance-none'
CHECKBOX_CLASSES = (
    'console-checkbox h-4 w-4 rounded border-gray-300 bg-gray-100 text-blue-600 '
    'focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 '
    'dark:ring-offset-gray-800 dark:focus:ring-blue-600'
)
FILE_CLASSES = (
    INPUT_CLASSES + ' file:me-4 file:rounded-base file:border-0 file:bg-brand-softer '
    'file:px-3 file:py-2 file:text-sm file:font-semibold file:text-fg-brand'
)


def materialize_upload(uploaded):
    """Copy the request upload to a stable stream before form validation/save."""
    if not uploaded:
        return uploaded
    try:
        uploaded.seek(0)
        payload = uploaded.read()
    except (AttributeError, OSError, ValueError) as exc:
        raise forms.ValidationError(gettext_lazy('Não foi possível ler o arquivo enviado. Tente selecionar o arquivo novamente.')) from exc
    if not payload:
        raise forms.ValidationError(gettext_lazy('O arquivo enviado está vazio.'))
    return ContentFile(payload, name=getattr(uploaded, 'name', 'arquivo'))


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)] if data else []


class DocumentForm(forms.ModelForm):
    company = forms.ModelChoiceField(queryset=TenantCompany.objects.none(), required=False, label=gettext_lazy('Empresa responsável'))
    initial_source_type = forms.ChoiceField(
        choices=(
            (DocumentVersion.SOURCE_RICH_TEXT, gettext_lazy('Conteúdo criado no sistema')),
            (DocumentVersion.SOURCE_UPLOAD, gettext_lazy('Arquivo anexado')),
        ),
        required=False,
        initial=DocumentVersion.SOURCE_RICH_TEXT,
        label=gettext_lazy('Forma do conteúdo'),
    )
    initial_file = forms.FileField(required=False, label=gettext_lazy('Arquivo inicial'), validators=[validate_upload])
    initial_body = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'data-rich-editor': 'true'}),
        label=gettext_lazy('Conteúdo textual inicial'),
    )
    change_summary = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label=gettext_lazy('Resumo da alteração'))
    initial_expires_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), label=gettext_lazy('Expira em'))
    permission_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'), required=False,
        label=gettext_lazy('Acesso direto para usuários'), widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    permission_download = forms.BooleanField(required=False, label=gettext_lazy('Permitir download para acessos diretos'))

    class Meta:
        model = Document
        fields = ('organization', 'company', 'audience_policy', 'title', 'slug', 'code', 'category', 'description', 'announce_changes', 'requires_approval', 'status')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'status': forms.Select(),
        }

    def __init__(self, *args, active_organization=None, company_queryset=None, default_company_id=None, company_required=False, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = CHECKBOX_CLASSES
            elif isinstance(widget, forms.FileInput):
                widget.attrs['class'] = FILE_CLASSES
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs['class'] = SELECT_CLASSES
                if isinstance(widget, forms.SelectMultiple):
                    widget.attrs.setdefault('size', 5)
            else:
                widget.attrs['class'] = INPUT_CLASSES
        if active_organization:
            tenant_org = get_tenant_organization(active_organization)
            if tenant_org:
                self.fields['organization'].queryset = TenantOrganization.objects.filter(pk=tenant_org.pk)
                self.fields['audience_policy'].queryset = self.fields['audience_policy'].queryset.filter(organization=tenant_org)
                allowed_companies = company_queryset if company_queryset is not None else Company.objects.filter(
                    organization_id=active_organization.pk, active=True,
                )
                self.fields['company'].queryset = TenantCompany.objects.filter(
                    company_id__in=allowed_companies.values_list('pk', flat=True),
                )
                self.fields['company'].required = company_required
            else:
                self.fields['organization'].queryset = TenantOrganization.objects.none()
                self.fields['audience_policy'].queryset = self.fields['audience_policy'].queryset.none()
        if default_company_id and not self.is_bound and not self.instance.pk:
            self.initial['company'] = TenantCompany.objects.filter(company_id=default_company_id).values_list('pk', flat=True).first()
        if self.instance and self.instance.pk:
            self.initial['permission_users'] = self.instance.explicit_permissions.values_list('user_id', flat=True)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            DocumentPermission.objects.filter(document=instance).delete()
            DocumentPermission.objects.bulk_create([
                DocumentPermission(
                    document=instance, user=user, can_view=True,
                    can_download=self.cleaned_data.get('permission_download', False),
                    granted_by=instance.owner,
                ) for user in self.cleaned_data.get('permission_users', [])
            ])
        return instance


class MediaAssetForm(forms.ModelForm):
    change_summary = forms.CharField(required=False, label=gettext_lazy('Resumo da alteração'), widget=forms.Textarea(attrs={'rows': 2}))
    collection = forms.ModelChoiceField(queryset=MediaCollection.objects.none(), required=False, label=gettext_lazy('Coleção'))
    tags = forms.ModelMultipleChoiceField(queryset=MediaTag.objects.none(), required=False, label=gettext_lazy('Tags'), widget=forms.SelectMultiple(attrs={'size': 5}))
    company = forms.ModelChoiceField(queryset=TenantCompany.objects.none(), required=False, label=gettext_lazy('Empresa'))
    audience_policy = forms.ModelChoiceField(queryset=AudiencePolicy.objects.none(), required=False, label=gettext_lazy('Audiência'))
    valid_until = forms.DateTimeField(required=False, input_formats=['%Y-%m-%dT%H:%M'], widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), label=gettext_lazy('Válido até'))
    retention_until = forms.DateTimeField(required=False, input_formats=['%Y-%m-%dT%H:%M'], widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), label=gettext_lazy('Reter até'))

    class Meta:
        model = MediaAsset
        fields = ('title', 'kind', 'company', 'audience_policy', 'collection', 'tags', 'file', 'external_url', 'alt_text', 'description', 'license_name', 'source_label', 'valid_until', 'retention_until', 'active', 'public_access', 'requires_approval')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'file': forms.ClearableFileInput(),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'retention_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, active_organization=None, company_queryset=None, default_company_id=None, company_required=False, **kwargs):
        super().__init__(*args, **kwargs)
        organization = get_tenant_organization(active_organization)
        scope = {'organization': organization} if organization else {'organization__isnull': True}
        self.fields['collection'].queryset = MediaCollection.objects.filter(active=True, **scope).order_by('name')
        self.fields['tags'].queryset = MediaTag.objects.filter(**scope).order_by('name')
        if organization:
            company_ids = company_queryset.values_list('pk', flat=True) if company_queryset is not None else Membership.objects.filter(organization_id=organization.organization_id, active=True).exclude(company_id__isnull=True).values_list('company_id', flat=True)
            self.fields['company'].queryset = TenantCompany.objects.filter(pk__in=company_ids).order_by('name')
            self.fields['company'].required = company_required
            if default_company_id and not self.is_bound and not self.instance.pk:
                tenant_company_id = TenantCompany.objects.filter(company_id=default_company_id).values_list('pk', flat=True).first()
                self.initial['company'] = tenant_company_id
            self.fields['audience_policy'].queryset = AudiencePolicy.objects.filter(organization=organization, active=True).order_by('name')
        if self.instance and self.instance.pk:
            self.initial['tags'] = self.instance.tags.values_list('pk', flat=True)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = CHECKBOX_CLASSES if isinstance(field.widget, forms.CheckboxInput) else (
                FILE_CLASSES if isinstance(field.widget, forms.FileInput) else (
                    SELECT_CLASSES if isinstance(field.widget, forms.Select) else INPUT_CLASSES
                )
            )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('file') and not cleaned.get('external_url') and not self.instance.file:
            raise forms.ValidationError(gettext_lazy('Envie um arquivo ou informe uma URL externa para a mídia.'))
        if cleaned.get('external_url') and not cleaned.get('public_access'):
            raise forms.ValidationError(gettext_lazy('Uma URL externa só pode ser usada quando a mídia for marcada como pública.'))
        if cleaned.get('kind') == MediaAsset.IMAGE and (not self.instance.pk or cleaned.get('file')) and not cleaned.get('alt_text', '').strip():
            self.add_error('alt_text', gettext_lazy('Informe um texto alternativo para imagens.'))
        if cleaned.get('file'):
            cleaned['file'] = materialize_upload(cleaned['file'])
            validate_upload(cleaned['file'])
            digest = hashlib.sha256()
            uploaded = cleaned['file']
            current_position = uploaded.tell() if hasattr(uploaded, 'tell') else 0
            uploaded.seek(0)
            for chunk in uploaded.chunks():
                digest.update(chunk)
            uploaded.seek(current_position)
            duplicates = MediaAsset.objects.filter(checksum=digest.hexdigest()).exclude(pk=self.instance.pk)
            if duplicates.exists():
                names = ', '.join(duplicates.values_list('title', flat=True)[:3])
                raise forms.ValidationError(
                    f'Este arquivo já existe na biblioteca ({names}). Use o item existente ou altere o arquivo antes de enviar.'
                )
        return cleaned

    def save(self, commit=True):
        old_name = self.instance.file.name if self.instance.pk and self.instance.file else ''
        old_checksum = self.instance.checksum if self.instance.pk else ''
        old_bytes = None
        if old_name and self.instance.file:
            try:
                with self.instance.file.open('rb') as stream:
                    old_bytes = stream.read()
            except (FileNotFoundError, OSError, ValueError):
                old_bytes = None
        instance = super().save(commit=commit)
        if commit and self.cleaned_data.get('file') and old_name and old_name != instance.file.name:
            last = instance.versions.order_by('-version_number').first()
            version = MediaAssetVersion(
                asset=instance, version_number=(last.version_number + 1 if last else 1),
                mime_type=instance.mime_type, file_size=len(old_bytes or b''),
                checksum=old_checksum, change_summary=self.cleaned_data.get('change_summary', ''),
                created_by=instance.owner,
            )
            if old_bytes is not None:
                version.file.save(f'{instance.pk}-v{version.version_number}-{os.path.basename(old_name)}', ContentFile(old_bytes), save=False)
            version.save()
            instance.file.storage.delete(old_name)
        elif commit and not old_name and instance.file:
            current = instance.file
            try:
                with current.open('rb') as stream:
                    current_bytes = stream.read()
                version = MediaAssetVersion(asset=instance, version_number=1, mime_type=instance.mime_type, file_size=len(current_bytes), checksum=instance.checksum, created_by=instance.owner)
                version.file.save(f'{instance.pk}-v1-{os.path.basename(current.name)}', ContentFile(current_bytes), save=False)
                version.save()
            except (FileNotFoundError, OSError, ValueError):
                pass
        return instance


class MediaBulkUploadForm(forms.Form):
    files = MultipleFileField(widget=MultipleFileInput(attrs={'multiple': True}), label=gettext_lazy('Arquivos'))
    kind = forms.ChoiceField(choices=MediaAsset.KIND_CHOICES, label=gettext_lazy('Tipo comum'))
    collection = forms.ModelChoiceField(queryset=MediaCollection.objects.none(), required=False, label=gettext_lazy('Coleção'))
    company = forms.ModelChoiceField(queryset=TenantCompany.objects.none(), required=False, label=gettext_lazy('Empresa'))
    audience_policy = forms.ModelChoiceField(queryset=AudiencePolicy.objects.none(), required=False, label=gettext_lazy('Audiência'))
    tags = forms.CharField(required=False, label=gettext_lazy('Tags'), help_text=gettext_lazy('Separe por vírgulas. Ex.: treinamento, bourbon, banner'))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label=gettext_lazy('Descrição comum'))
    alt_text = forms.CharField(required=False, label=gettext_lazy('Texto alternativo comum'))
    public_access = forms.BooleanField(required=False, label=gettext_lazy('Permitir acesso público sem login'))

    def __init__(self, *args, active_organization=None, company_queryset=None, default_company_id=None, company_required=False, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = CHECKBOX_CLASSES if isinstance(field.widget, forms.CheckboxInput) else (
                FILE_CLASSES if isinstance(field.widget, forms.FileInput) else (
                    SELECT_CLASSES if isinstance(field.widget, forms.Select) else INPUT_CLASSES
                )
            )
        organization = get_tenant_organization(active_organization)
        scope = {'organization': organization} if organization else {'organization__isnull': True}
        self.fields['collection'].queryset = MediaCollection.objects.filter(active=True, **scope).order_by('name')
        if organization:
            company_ids = company_queryset.values_list('pk', flat=True) if company_queryset is not None else Membership.objects.filter(organization_id=organization.organization_id, active=True).exclude(company_id__isnull=True).values_list('company_id', flat=True)
            self.fields['company'].queryset = TenantCompany.objects.filter(pk__in=company_ids).order_by('name')
            self.fields['company'].required = company_required
            if default_company_id and not self.is_bound:
                self.initial['company'] = default_company_id
            self.fields['audience_policy'].queryset = AudiencePolicy.objects.filter(organization=organization, active=True).order_by('name')

    def clean_files(self):
        files = [materialize_upload(uploaded) for uploaded in self.cleaned_data['files']]
        for file in files:
            validate_upload(file)
        return files

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('kind') == MediaAsset.IMAGE and not cleaned.get('alt_text', '').strip():
            self.add_error('alt_text', gettext_lazy('Informe um texto alternativo comum para as imagens do lote.'))
        return cleaned


class MediaCollectionForm(forms.ModelForm):
    class Meta:
        model = MediaCollection
        fields = ('name', 'description', 'active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = CHECKBOX_CLASSES if isinstance(field.widget, forms.CheckboxInput) else INPUT_CLASSES
