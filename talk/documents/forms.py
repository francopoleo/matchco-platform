from django import forms
from django.contrib.auth import get_user_model

from .models import Document, DocumentPermission
from .services import validate_upload

User = get_user_model()


class DocumentForm(forms.ModelForm):
    initial_file = forms.FileField(required=False, label='Arquivo inicial', validators=[validate_upload])
    initial_body = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 8}), label='Conteúdo textual inicial')
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
        if active_organization:
            self.fields['organization'].queryset = self.fields['organization'].queryset.filter(pk=active_organization.pk)
            self.fields['audience_policy'].queryset = self.fields['audience_policy'].queryset.filter(organization=active_organization)
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
