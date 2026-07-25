from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.contenttypes.models import ContentType
from .models import Course, Module
from documents.models import Document, DocumentLink


FLOWBITE_FIELD = 'block w-full rounded-base border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs placeholder:text-body focus:border-brand focus:ring-brand'


class CourseManagementForm(forms.ModelForm):
    documents = forms.ModelMultipleChoiceField(
        queryset=Document.objects.filter(status=Document.PUBLISHED), required=False,
        label='Documentos relacionados', widget=forms.SelectMultiple(attrs={'size': 5, 'class': FLOWBITE_FIELD}),
    )
    class Meta:
        model = Course
        fields = ('subject', 'title', 'slug', 'overview')
        widgets = {
            'subject': forms.Select(attrs={'class': FLOWBITE_FIELD}),
            'title': forms.TextInput(attrs={'class': FLOWBITE_FIELD}),
            'slug': forms.TextInput(attrs={'class': FLOWBITE_FIELD}),
            'overview': forms.Textarea(attrs={'class': FLOWBITE_FIELD, 'rows': 7}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            content_type = ContentType.objects.get_for_model(Course)
            self.initial['documents'] = Document.objects.filter(
                links__content_type=content_type, links__object_id=self.instance.pk,
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and instance.pk:
            content_type = ContentType.objects.get_for_model(Course)
            DocumentLink.objects.filter(content_type=content_type, object_id=instance.pk).delete()
            DocumentLink.objects.bulk_create([
                DocumentLink(document=document, content_type=content_type, object_id=instance.pk, created_by=instance.owner)
                for document in self.cleaned_data.get('documents', [])
            ])
        return instance


class ModuleManagementForm(forms.ModelForm):
    documents = forms.ModelMultipleChoiceField(
        queryset=Document.objects.filter(status=Document.PUBLISHED),
        required=False,
        label='Documentos relacionados',
        widget=forms.SelectMultiple(attrs={'size': 4, 'class': FLOWBITE_FIELD}),
    )

    class Meta:
        model = Module
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': FLOWBITE_FIELD}),
            'description': forms.Textarea(attrs={'class': FLOWBITE_FIELD, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            content_type = ContentType.objects.get_for_model(Module)
            self.initial['documents'] = Document.objects.filter(
                links__content_type=content_type, links__object_id=self.instance.pk,
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and instance.pk:
            content_type = ContentType.objects.get_for_model(Module)
            DocumentLink.objects.filter(content_type=content_type, object_id=instance.pk).delete()
            DocumentLink.objects.bulk_create([
                DocumentLink(
                    document=document,
                    content_type=content_type,
                    object_id=instance.pk,
                    created_by=self.form_user,
                )
                for document in self.cleaned_data.get('documents', [])
            ])
        return instance


ModuleFormSet = inlineformset_factory(
    Course,
    Module,
    form=ModuleManagementForm,
    fields=['title', 'description', 'documents'],
    extra=2,
    can_delete=True,
)
