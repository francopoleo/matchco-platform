from django import forms
from django.forms.models import inlineformset_factory
from .models import Course, Module


FLOWBITE_FIELD = 'block w-full rounded-base border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs placeholder:text-body focus:border-brand focus:ring-brand'


class CourseManagementForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('subject', 'title', 'slug', 'overview')
        widgets = {
            'subject': forms.Select(attrs={'class': FLOWBITE_FIELD}),
            'title': forms.TextInput(attrs={'class': FLOWBITE_FIELD}),
            'slug': forms.TextInput(attrs={'class': FLOWBITE_FIELD}),
            'overview': forms.Textarea(attrs={'class': FLOWBITE_FIELD, 'rows': 7}),
        }


ModuleFormSet = inlineformset_factory(Course,
                                      Module,
                                      fields=['title',
                                              'description'],
                                      extra=2,
                                      can_delete=True)
