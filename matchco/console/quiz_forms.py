from django import forms
from django.utils.translation import gettext_lazy as _
from courses.models import Quiz, Question, Answer
from .forms import FlowbiteFormMixin


class QuizForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'overview', 'quiz_type', 'is_required',
            'required_score_to_pass', 'allow_multiple_attempts', 'max_attempts',
            'attempts_limit_period_days', 'time_limit_minutes',
            'show_feedback_type', 'shuffle_questions', 'show_correct_answers'
        ]
        widgets = {
            'overview': forms.Textarea(attrs={'rows': 4}),
            'required_score_to_pass': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'max_attempts': forms.NumberInput(attrs={'min': 1}),
            'attempts_limit_period_days': forms.NumberInput(attrs={'min': 1}),
            'time_limit_minutes': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_flowbite_widgets()


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'text', 'explanation']
        widgets = {
            'question_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:text-white'}),
            'text': forms.Textarea(attrs={'class': 'rich-editor w-full rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white', 'rows': 6, 'data-rich-editor': 'true'}),
            'explanation': forms.Textarea(attrs={'class': 'rich-editor w-full rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white', 'rows': 5, 'data-rich-editor': 'true'}),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:text-white'}),
            'correct': forms.CheckboxInput(attrs={'class': 'rounded'}),
        }


class AnswerFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        correct_answers = sum(1 for form in self.forms if form.cleaned_data.get('correct', False))
        if correct_answers == 0:
            raise forms.ValidationError(_('At least one answer must be marked as correct.'))
