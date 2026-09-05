from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from courses.models import Quiz, Question, Answer, UserQuizAttempt, UserAnswer, Module, Content
from django.contrib.contenttypes.models import ContentType
from .quiz_forms import QuizForm, QuestionForm, AnswerForm, AnswerFormSet
from .views import ManagerRequiredMixin, active_organization_queryset
from cep.core.utils import get_tenant_organization, get_tenant_user


class QuizListView(ManagerRequiredMixin, ListView):
    model = Quiz
    template_name = 'console/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 20

    def get_queryset(self):
        qs = Quiz.objects.select_related('owner', 'organization').prefetch_related('questions')
        qs = active_organization_queryset(self.request, qs, 'organization_id')

        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(overview__icontains=search))

        return qs.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['quiz_type_choices'] = Quiz.TYPE_CHOICES
        return context


class QuizDetailView(ManagerRequiredMixin, DetailView):
    model = Quiz
    template_name = 'console/quiz_detail.html'
    context_object_name = 'quiz'

    def get_queryset(self):
        return active_organization_queryset(self.request, Quiz.objects.all(), 'organization_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        context['question_count'] = self.object.get_question_count()
        context['attempts_stats'] = self.object.attempts.aggregate(
            total_attempts=Count('id'),
            avg_score=Avg('score'),
            passed_count=Count('id', filter=Q(passed=True))
        )
        return context


class QuizEditorView(ManagerRequiredMixin, DetailView):
    """Editor para adicionar perguntas ao quiz"""
    model = Quiz
    template_name = 'console/quiz_editor.html'
    context_object_name = 'quiz'

    def get_queryset(self):
        return active_organization_queryset(self.request, Quiz.objects.all(), 'organization_id')


class QuizCreateView(ManagerRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'console/quiz_form.html'

    def get_initial(self):
        return {'owner': get_tenant_user(self.request.user)}

    def form_valid(self, form):
        tenant_user = get_tenant_user(self.request.user)
        if not tenant_user:
            form.add_error(None, _('O usuário autenticado ainda não possui cadastro de TenantUser.'))
            return self.form_invalid(form)
        form.instance.owner = tenant_user
        organization = getattr(self.request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        if tenant_organization:
            form.instance.organization = tenant_organization
        messages.success(self.request, _('Quiz created successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:quiz-detail', kwargs={'pk': self.object.pk})


class QuizUpdateView(ManagerRequiredMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'console/quiz_form.html'

    def get_queryset(self):
        return active_organization_queryset(self.request, Quiz.objects.all(), 'organization_id')

    def form_valid(self, form):
        messages.success(self.request, _('Quiz updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:quiz-detail', kwargs={'pk': self.object.pk})


class QuizDeleteView(ManagerRequiredMixin, DeleteView):
    model = Quiz
    template_name = 'console/quiz_confirm_delete.html'
    success_url = reverse_lazy('console:quiz-list')

    def get_queryset(self):
        return active_organization_queryset(self.request, Quiz.objects.all(), 'organization_id')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Quiz deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class QuestionCreateView(ManagerRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'console/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=kwargs['quiz_pk'])
        active_org = getattr(request, 'active_organization', None)
        tenant_org = get_tenant_organization(active_org) if active_org else None
        # If quiz doesn't have organization, set it to the active org
        if not self.quiz.organization and tenant_org:
            self.quiz.organization = tenant_org
            self.quiz.save()
        # Check if user belongs to the same organization
        if not tenant_org or self.quiz.organization_id != tenant_org.id:
            return redirect('console:quiz-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.quiz
        return context

    def form_valid(self, form):
        form.instance.quiz = self.quiz
        messages.success(self.request, _('Question added successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:quiz-editor', kwargs={'pk': self.quiz.pk})


class QuestionUpdateView(ManagerRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'console/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.question = self.get_object()
        active_org = getattr(request, 'active_organization', None)
        tenant_org = get_tenant_organization(active_org) if active_org else None
        # If quiz doesn't have organization, set it to the active org
        if not self.question.quiz.organization and tenant_org:
            self.question.quiz.organization = tenant_org
            self.question.quiz.save()
        # Check if user belongs to the same organization
        if not tenant_org or self.question.quiz.organization_id != tenant_org.id:
            return redirect('console:quiz-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.object.quiz
        context['answers'] = self.object.answers.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Question updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:quiz-editor', kwargs={'pk': self.object.quiz.pk})


class QuestionDeleteView(ManagerRequiredMixin, DeleteView):
    model = Question
    template_name = 'console/question_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.question = self.get_object()
        active_org = getattr(request, 'active_organization', None)
        tenant_org = get_tenant_organization(active_org) if active_org else None
        # If quiz doesn't have organization, set it to the active org
        if not self.question.quiz.organization and tenant_org:
            self.question.quiz.organization = tenant_org
            self.question.quiz.save()
        # Check if user belongs to the same organization
        if not tenant_org or self.question.quiz.organization_id != tenant_org.id:
            return redirect('console:quiz-list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        quiz_pk = self.object.quiz.pk
        messages.success(request, _('Question deleted successfully.'))
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('console:quiz-editor', kwargs={'pk': self.object.quiz.pk})


class AnswerCreateView(ManagerRequiredMixin, CreateView):
    model = Answer
    form_class = AnswerForm
    template_name = 'console/answer_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(Question, pk=kwargs['question_pk'])
        active_org = getattr(request, 'active_organization', None)
        tenant_org = get_tenant_organization(active_org) if active_org else None
        # If quiz doesn't have organization, set it to the active org
        if not self.question.quiz.organization and tenant_org:
            self.question.quiz.organization = tenant_org
            self.question.quiz.save()
        # Check if user belongs to the same organization
        if not tenant_org or self.question.quiz.organization_id != tenant_org.id:
            return redirect('console:quiz-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        context['quiz'] = self.question.quiz
        return context

    def form_valid(self, form):
        form.instance.question = self.question
        messages.success(self.request, _('Answer added successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:question-update', kwargs={
            'pk': self.question.pk,
            'quiz_pk': self.question.quiz.pk
        })


class AnswerUpdateView(ManagerRequiredMixin, UpdateView):
    model = Answer
    form_class = AnswerForm
    template_name = 'console/answer_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.answer = self.get_object()
        active_org = getattr(request, 'active_organization', None)
        tenant_org = get_tenant_organization(active_org) if active_org else None
        # If quiz doesn't have organization, set it to the active org
        if not self.answer.question.quiz.organization and tenant_org:
            self.answer.question.quiz.organization = tenant_org
            self.answer.question.quiz.save()
        # Check if user belongs to the same organization
        if not tenant_org or self.answer.question.quiz.organization_id != tenant_org.id:
            return redirect('console:quiz-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.object.question
        context['quiz'] = self.object.question.quiz
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Answer updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:question-update', kwargs={
            'pk': self.object.question.pk,
            'quiz_pk': self.object.question.quiz.pk
        })


class AnswerDeleteView(ManagerRequiredMixin, DeleteView):
    model = Answer
    template_name = 'console/answer_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.answer = self.get_object()
        active_org = getattr(request, 'active_organization', None)
        tenant_org = get_tenant_organization(active_org) if active_org else None
        # If quiz doesn't have organization, set it to the active org
        if not self.answer.question.quiz.organization and tenant_org:
            self.answer.question.quiz.organization = tenant_org
            self.answer.question.quiz.save()
        # Check if user belongs to the same organization
        if not tenant_org or self.answer.question.quiz.organization_id != tenant_org.id:
            return redirect('console:quiz-list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        quiz_pk = self.object.question.quiz.pk
        messages.success(request, _('Answer deleted successfully.'))
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('console:question-update', kwargs={
            'pk': self.object.question.pk,
            'quiz_pk': self.object.question.quiz.pk
        })


class QuizAttemptsView(ManagerRequiredMixin, ListView):
    model = UserQuizAttempt
    template_name = 'console/quiz_attempts.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=kwargs['quiz_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.quiz.attempts.select_related('user').order_by('-started_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.quiz
        return context


class QuizAttemptDetailView(ManagerRequiredMixin, DetailView):
    model = UserQuizAttempt
    template_name = 'console/quiz_attempt_detail.html'
    context_object_name = 'attempt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answers'] = self.object.answers.select_related('question', 'selected_answer')
        return context
