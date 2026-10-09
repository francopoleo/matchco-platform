from django import forms
from django.utils.translation import gettext_lazy as _
from courses.models import Quiz


class QuizQuickCreateForm(forms.ModelForm):
    """Form para criar quiz rapidamente no course editor"""
    class Meta:
        model = Quiz
        fields = ['title', 'overview', 'required_score_to_pass', 'quiz_type', 'is_required']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:text-white',
                'placeholder': _('Quiz title')
            }),
            'overview': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:text-white',
                'rows': 3,
                'placeholder': _('Description (optional)')
            }),
            'required_score_to_pass': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:text-white',
                'min': 0,
                'max': 100,
                'value': 70
            }),
            'quiz_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:text-white'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'rounded'
            }),
        }
