from django import forms
from django.contrib.auth import get_user_model

from cep.core.utils import get_tenant_organization
from tenants_core.models import TenantOrganization
from .models import Document, DocumentPermission
from .services import validate_upload

User = get_user_model()


INPUT_CLASSES = (
    'block w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 '
    'text-sm text-gray-900 shadow-sm placeholder:text-gray-400 '
    'focus:border-blue-500 focus:ring-2 focus:ring-blue-200 '
    'dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder:text-gray-400 '
    'dark:focus:border-blue-500 dark:focus:ring-blue-900/50'
)
SELECT_CLASSES = INPUT_CLASSES + ' appearance-none'
CHECKBOX_CLASSES = (
    'h-4 w-4 rounded border-gray-300 bg-gray-100 text-blue-600 '
    'focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 '
    'dark:ring-offset-gray-800 dark:focus:ring-blue-600'
)
FILE_CLASSES = (
    INPUT_CLASSES + ' file:me-4 file:rounded-md file:border-0 file:bg-blue-50 '
    'file:px-3 file:py-2 file:text-sm file:font-semibold file:text-blue-700 '
    'dark:file:bg-blue-900/30 dark:file:text-blue-300'
)


class DocumentForm(forms.ModelForm):
    initial_file = forms.FileField(required=False, label='Arquivo inicial', validators=[validate_upload])
    initial_body = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'data-rich-editor': 'true'}),
        label='Conteúdo textual inicial',
    )
    change_summary = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='Resumo da alteração')
    initial_expires_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), label='Expira em')
    permission_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'), required=False,
        label='Acesso direto para usuários', widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    permission_download = forms.BooleanField(required=False, label='Permitir download para acessos diretos')

    class Meta:
        model = Document
        fields = ('organization', 'audience_policy', 'title', 'slug', 'code', 'category', 'description', 'announce_changes', 'status')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'status': forms.Select(),
        }

    def __init__(self, *args, active_organization=None, **kwargs):
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
            else:
                self.fields['organization'].queryset = TenantOrganization.objects.none()
                self.fields['audience_policy'].queryset = self.fields['audience_policy'].queryset.none()
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
