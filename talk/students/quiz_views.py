from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import json

from courses.models import Quiz, UserQuizAttempt, UserAnswer, Question


class QuizTakeView(LoginRequiredMixin, DetailView):
    """Display quiz questions for the user to answer"""
    model = Quiz
    template_name = 'students/quiz_take.html'
    context_object_name = 'quiz'

    def get_object(self):
        quiz_id = self.kwargs.get('quiz_id')
        return get_object_or_404(Quiz, pk=quiz_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object
        user = self.request.user

        # Check if user can take the quiz
        active_attempt = UserQuizAttempt.objects.filter(
            user=user,
            quiz=quiz,
            completed_at__isnull=True
        ).first()

        if active_attempt:
            context['active_attempt'] = active_attempt
            context['answers'] = active_attempt.answers.select_related('question', 'selected_answer')
        else:
            # Check attempt limits
            if not quiz.allow_multiple_attempts:
                past_attempt = UserQuizAttempt.objects.filter(user=user, quiz=quiz).first()
                if past_attempt:
                    context['error'] = _('You have already completed this quiz.')
                    return context

            # Check attempt limit
            if quiz.max_attempts:
                attempt_count = UserQuizAttempt.objects.filter(user=user, quiz=quiz).count()
                if attempt_count >= quiz.max_attempts:
                    context['error'] = _('You have reached the maximum number of attempts.')
                    return context

            # Check retry period
            if quiz.attempts_limit_period_days:
                last_attempt = UserQuizAttempt.objects.filter(user=user, quiz=quiz).order_by('-started_at').first()
                if last_attempt:
                    retry_date = last_attempt.started_at + timedelta(days=quiz.attempts_limit_period_days)
                    if timezone.now() < retry_date:
                        days_remaining = (retry_date - timezone.now()).days + 1
                        context['error'] = _('You can retry this quiz in %(days)s days.') % {'days': days_remaining}
                        return context

            # Create new attempt
            attempt = UserQuizAttempt.objects.create(
                user=user,
                quiz=quiz,
                attempt_number=UserQuizAttempt.objects.filter(user=user, quiz=quiz).count() + 1
            )
            context['active_attempt'] = attempt
            context['answers'] = []

        # Get questions
        questions = quiz.get_questions()
        context['questions'] = questions
        context['question_count'] = len(questions)
        context['attempt_number'] = context['active_attempt'].attempt_number if context['active_attempt'] else None

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if 'error' in context:
            messages.error(request, context['error'])
            return redirect('student-dashboard')
        return self.render_to_response(context)


class QuizSubmitView(LoginRequiredMixin, View):
    """Process quiz answers and calculate score"""

    def post(self, request, *args, **kwargs):
        quiz_id = kwargs.get('quiz_id')
        attempt_id = request.POST.get('attempt_id')

        quiz = get_object_or_404(Quiz, pk=quiz_id)
        attempt = get_object_or_404(UserQuizAttempt, pk=attempt_id, user=request.user)

        if attempt.completed_at:
            messages.error(request, _('This quiz attempt has already been submitted.'))
            return redirect('quiz-result', quiz_id=quiz_id, attempt_id=attempt_id)

        # Process answers
        questions = quiz.questions.all()
        correct_count = 0

        for question in questions:
            answer_data = None

            if question.question_type == 'multiple_choice' or question.question_type == 'multiple_correct':
                # Get selected answer
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    try:
                        from courses.models import Answer
                        answer = Answer.objects.get(id=answer_id, question=question)
                        answer_data = answer
                        is_correct = answer.correct
                        if is_correct:
                            correct_count += 1
                    except:
                        is_correct = False
                else:
                    is_correct = False

            elif question.question_type == 'true_false':
                # Get T/F answer
                answer_text = request.POST.get(f'question_{question.id}')
                if answer_text:
                    from courses.models import Answer
                    answer = Answer.objects.filter(
                        question=question,
                        text__iexact=answer_text
                    ).first()
                    if answer:
                        answer_data = answer
                        is_correct = answer.correct
                        if is_correct:
                            correct_count += 1
                    else:
                        is_correct = False
                else:
                    is_correct = False

            elif question.question_type == 'short_answer':
                # Get text answer
                answer_text = request.POST.get(f'question_{question.id}', '').strip()
                if answer_text:
                    from courses.models import Answer
                    # For short answer, check if matches any correct answer
                    correct_answer = Answer.objects.filter(
                        question=question,
                        correct=True
                    ).first()

                    is_correct = False
                    if correct_answer:
                        # Simple string match (can be enhanced with fuzzy matching)
                        is_correct = answer_text.lower() == correct_answer.text.lower()
                        if is_correct:
                            correct_count += 1
                else:
                    is_correct = False
                    answer_text = ''

            # Create UserAnswer record
            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_answer': answer_data if question.question_type in ['multiple_choice', 'multiple_correct', 'true_false'] else None,
                    'user_answer_text': answer_text if question.question_type == 'short_answer' else '',
                    'is_correct': is_correct,
                    'points_earned': 1 if is_correct else 0
                }
            )

        # Calculate score
        total_questions = questions.count()
        if total_questions > 0:
            score = (correct_count / total_questions) * 100
        else:
            score = 0

        # Update attempt
        attempt.completed_at = timezone.now()
        attempt.score = score
        attempt.passed = score >= quiz.required_score_to_pass

        # Calculate time spent
        time_spent = (attempt.completed_at - attempt.started_at).total_seconds() / 60
        attempt.time_spent_minutes = int(time_spent)

        attempt.save()

        # Award points if passed
        if attempt.passed and quiz.points_per_approval:
            from gamification.models import GamificationPostView
            try:
                # Award gamification points
                # This is a simplified version - you may need to adjust based on your gamification model
                pass
            except:
                pass

        messages.success(request, _('Quiz submitted successfully!'))
        return redirect('quiz-result', quiz_id=quiz_id, attempt_id=attempt_id)


class QuizResultView(LoginRequiredMixin, TemplateView):
    """Display quiz results and feedback"""
    template_name = 'students/quiz_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz_id = kwargs.get('quiz_id')
        attempt_id = kwargs.get('attempt_id')

        quiz = get_object_or_404(Quiz, pk=quiz_id)
        attempt = get_object_or_404(UserQuizAttempt, pk=attempt_id, user=self.request.user)

        context['quiz'] = quiz
        context['attempt'] = attempt
        context['answers'] = attempt.answers.select_related('question', 'selected_answer').order_by('question__order')
        context['correct_count'] = attempt.answers.filter(is_correct=True).count()
        context['total_count'] = attempt.answers.count()

        return context


class QuizAttemptsView(LoginRequiredMixin, TemplateView):
    """View user's quiz attempts history"""
    template_name = 'students/quiz_attempts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz_id = kwargs.get('quiz_id')

        quiz = get_object_or_404(Quiz, pk=quiz_id)
        attempts = UserQuizAttempt.objects.filter(
            user=self.request.user,
            quiz=quiz
        ).order_by('-started_at')

        context['quiz'] = quiz
        context['attempts'] = attempts
        context['can_retry'] = quiz.allow_multiple_attempts

        # Check if can retry
        if quiz.max_attempts and attempts.count() >= quiz.max_attempts:
            context['can_retry'] = False

        if quiz.attempts_limit_period_days and attempts.exists():
            last_attempt = attempts.first()
            retry_date = last_attempt.started_at + timedelta(days=quiz.attempts_limit_period_days)
            context['retry_date'] = retry_date
            context['can_retry'] = timezone.now() >= retry_date

        return context
