from django.utils.translation import gettext_lazy as gettext_lazy
import json

from django import forms
from django.contrib import messages
from django.core.management import call_command
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from recruitment.domain_models import RecruitmentOrganization
from recruitment.models import QuestionnaireQuestion, QuestionnaireTemplate
from recruitment.questionnaire_builder import create_questionnaire_draft

from .views import ManagerRequiredMixin, active_organization
from django.views.generic import View


class QuestionnaireTemplateForm(forms.ModelForm):
    class Meta:
        model = QuestionnaireTemplate
        fields = ('name', 'description', 'status', 'market', 'audience_role', 'is_default', 'max_questions', 'is_approved_by_ops')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        control = 'mt-1 block w-full rounded-base border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-brand focus:ring-2 focus:ring-brand/30'
        for field in self.fields.values():
            field.widget.attrs['class'] = control
        self.fields['is_default'].widget.attrs['class'] = 'console-checkbox h-4 w-4 rounded border-gray-300 bg-gray-100 text-blue-600 focus:ring-2 focus:ring-blue-500'


class QuestionnaireQuestionForm(forms.ModelForm):
    class Meta:
        model = QuestionnaireQuestion
        fields = ('key', 'label', 'help_text', 'field_type', 'options', 'conditions', 'required', 'order', 'active')
        widgets = {
            'help_text': forms.TextInput(),
            'options': forms.Textarea(attrs={'rows': 2, 'placeholder': '["Opção 1", "Opção 2"]'}),
            'conditions': forms.Textarea(attrs={'rows': 2, 'placeholder': '{"key": "outra", "equals": "Sim"}'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        control = 'mt-1 block w-full rounded-base border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-brand focus:ring-2 focus:ring-brand/30'
        for field in self.fields.values():
            field.widget.attrs['class'] = control
        for name in ('required', 'active'):
            self.fields[name].widget.attrs['class'] = 'console-checkbox h-4 w-4 rounded border-gray-300 bg-gray-100 text-blue-600 focus:ring-2 focus:ring-blue-500'

    def clean_options(self):
        value = self.cleaned_data.get('options')
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError(gettext_lazy('Use uma lista JSON, por exemplo ["Sim", "Não"].'))
        return value or []

    def clean_conditions(self):
        value = self.cleaned_data.get('conditions')
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError(gettext_lazy('Use um objeto JSON válido ou deixe vazio.'))
        return value or {}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('label') and cleaned.get('field_type'):
            from recruitment.questionnaire_compliance import validate_question_definition
            validate_question_definition(label=cleaned['label'], field_type=cleaned['field_type'])
        return cleaned


def _recruitment_organization(organization):
    if not organization:
        return None
    return (
        RecruitmentOrganization.objects.filter(legacy_id=organization.pk).first()
        or RecruitmentOrganization.objects.filter(slug=organization.slug).first()
    )


class QuestionnaireTemplateListView(ManagerRequiredMixin, View):
    template_name = 'console/questionnaire_template_list.html'

    def get(self, request):
        organization = active_organization(request)
        recruitment_org = _recruitment_organization(organization)
        templates = QuestionnaireTemplate.objects.filter(organization=recruitment_org).prefetch_related('questions') if recruitment_org else []
        template_queryset = templates if hasattr(templates, 'filter') else []
        return render(request, self.template_name, {
            'organization': organization,
            'recruitment_organization': recruitment_org,
            'templates': templates,
            'template_count': len(templates) if isinstance(templates, list) else templates.count(),
            'published_count': template_queryset.filter(status=QuestionnaireTemplate.STATUS_PUBLISHED).count() if hasattr(template_queryset, 'filter') else 0,
            'draft_count': template_queryset.exclude(status=QuestionnaireTemplate.STATUS_PUBLISHED).count() if hasattr(template_queryset, 'filter') else 0,
        })

    @transaction.atomic
    def post(self, request):
        organization = active_organization(request)
        recruitment_org = _recruitment_organization(organization)
        if not organization or not recruitment_org:
            messages.error(request, gettext_lazy('Esta organização ainda não possui o vínculo de recrutamento necessário.'))
            return redirect('console:questionnaire-templates')
        action = request.POST.get('action')
        if action == 'seed':
            call_command('seed_questionnaire_templates', organization=recruitment_org.slug)
            messages.success(request, gettext_lazy('Biblioteca inicial aplicada. Templates existentes foram preservados.'))
        elif action == 'draft':
            brief = {
                'name': request.POST.get('name') or 'Novo questionário · rascunho',
                'code': request.POST.get('code') or 'custom-setup',
                'description': request.POST.get('description', ''),
                'market': request.POST.get('market', ''),
                'audience_role': request.POST.get('audience_role', ''),
            }
            template = create_questionnaire_draft(recruitment_org, brief)
            messages.success(request, f'Rascunho {template.name} criado. Revise as perguntas antes de publicar.')
            return redirect('console:questionnaire-template-edit', pk=template.pk)
        return redirect('console:questionnaire-templates')


class QuestionnaireTemplateEditView(ManagerRequiredMixin, View):
    template_name = 'console/questionnaire_template_edit.html'

    def get_template(self, request, pk):
        organization = active_organization(request)
        recruitment_org = _recruitment_organization(organization)
        return get_object_or_404(QuestionnaireTemplate, pk=pk, organization=recruitment_org)

    def get(self, request, pk):
        template = self.get_template(request, pk)
        return render(request, self.template_name, {
            'organization': active_organization(request),
            'questionnaire': template,
            'form': QuestionnaireTemplateForm(instance=template),
            'question_form': QuestionnaireQuestionForm(),
            'questions': template.questions.all(),
        })

    @transaction.atomic
    def post(self, request, pk):
        template = self.get_template(request, pk)
        if request.POST.get('action') == 'question':
            form = QuestionnaireQuestionForm(request.POST)
            if form.is_valid():
                question = form.save(commit=False)
                question.template = template
                try:
                    question.full_clean()
                except forms.ValidationError as exc:
                    form.add_error(None, exc)
                    return render(request, self.template_name, {
                        'organization': active_organization(request), 'questionnaire': template,
                        'form': QuestionnaireTemplateForm(instance=template), 'question_form': form,
                        'questions': template.questions.all(),
                    })
                question.save()
                messages.success(request, gettext_lazy('Pergunta adicionada ao template.'))
                return redirect('console:questionnaire-template-edit', pk=pk)
            return render(request, self.template_name, {
                'organization': active_organization(request), 'questionnaire': template,
                'form': QuestionnaireTemplateForm(instance=template), 'question_form': form,
                'questions': template.questions.all(),
            })
        form = QuestionnaireTemplateForm(request.POST, instance=template)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.is_approved_by_ops and not obj.approval_date:
                from django.utils import timezone
                obj.approval_date = timezone.now()
            if obj.status == QuestionnaireTemplate.STATUS_PUBLISHED and not obj.published_at:
                from django.utils import timezone
                obj.published_at = timezone.now()
            try:
                obj.full_clean()
            except forms.ValidationError as exc:
                form.add_error(None, exc)
                return render(request, self.template_name, {
                    'organization': active_organization(request), 'questionnaire': template,
                    'form': form, 'question_form': QuestionnaireQuestionForm(),
                    'questions': template.questions.all(),
                })
            obj.save()
            messages.success(request, gettext_lazy('Template atualizado.'))
            return redirect('console:questionnaire-template-edit', pk=pk)
        return render(request, self.template_name, {
            'organization': active_organization(request), 'questionnaire': template,
            'form': form, 'question_form': QuestionnaireQuestionForm(),
            'questions': template.questions.all(),
        })
