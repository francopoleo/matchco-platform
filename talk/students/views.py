from itertools import cycle
from django.http import JsonResponse
import json
from django.urls import reverse_lazy, reverse
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import BACKEND_SESSION_KEY, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from django.utils import timezone
from django.views import View
from courses.models import Course, Content, Question, Quiz, Answer
from .forms import CourseEnrollForm
from .models import CourseEnroll, ModuleEnroll, ContentEnroll, QuizResult, QuestionResult

from gamification.utils import create_gamification_report_item
from gamification.models import GamificationReport
from learning.models import ContentEvent, CourseCertificate
from learning.models import ContentTrail
from learning.services import ensure_user_trail_assignments, enroll_user, get_enrollment, mark_content_completed, next_trail_step, track_event
from publishing.models import ContentFeedback, Publication
from documents.models import DocumentLink
from documents.services import can_view as can_view_document


class StudentRegistrationView(CreateView):
    template_name = 'students/student/registration.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('student_course_list')

    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'],
                            password=cd['password1'])
        login(self.request, user)
        return result


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course_enroll, _ = enroll_user(self.request.user, self.course)

        return super().form_valid(form)

    def get_success_url(self):
        # Criação dos pontos de gamificação para entrada no curso
        if self.course.type == 'course':
            create_gamification_report_item(self.request.user, 'course_enrollment', object_source=self.course)

        return reverse_lazy('student_course_detail', args=[self.course.id])


class StudentTrailStartView(LoginRequiredMixin, View):
    def get(self, request, pk):
        ensure_user_trail_assignments(request.user)
        trail = get_object_or_404(ContentTrail, pk=pk, status=ContentTrail.PUBLISHED)
        track_event(request.user, ContentEvent.RECOMMENDATION_OPENED, trail, metadata={'source': 'home'})
        result = next_trail_step(request.user, trail)
        if not result or result[1] is None:
            return redirect('home')
        _, step = result
        target = step.content_object
        if isinstance(target, Publication):
            return redirect(
                'publication_feed_detail' if target.kind == Publication.FEED else 'publication_detail',
                slug=target.slug,
            )
        if isinstance(target, Content):
            return redirect('student_course_detail_module_content', pk=target.module.course_id, module_id=target.module_id, content_id=target.object_id, model_name=target.content_type.model)
        if isinstance(target, Course):
            return redirect('course_detail', slug=target.slug)
        return redirect('home')


class StudentTrailListView(LoginRequiredMixin, TemplateView):
    template_name = 'students/trails/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_user_trail_assignments(self.request.user)
        assignments = list(
            self.request.user.trail_assignments.filter(trail__status=ContentTrail.PUBLISHED)
            .select_related('trail')
            .prefetch_related('trail__steps', 'progress')
        )
        for assignment in assignments:
            steps = list(assignment.trail.steps.all())
            progress = list(assignment.progress.all())
            completed_ids = {item.step_id for item in progress if item.completed_at}
            total = len(steps)
            completed = len(completed_ids)
            assignment.progress_completed = completed
            assignment.progress_total = total
            assignment.progress_percent = round(completed * 100 / total) if total else 0
            assignment.progress_status = 'completed' if assignment.completed_at else ('started' if completed else 'pending')
            assignment.completed_steps = [item for item in progress if item.completed_at]
            assignment.pending_steps = [step for step in steps if step.pk not in completed_ids]
            assignment.is_overdue = bool(assignment.due_at and assignment.due_at < timezone.now() and not assignment.completed_at)
        context['assignments'] = assignments
        return context


class TrailStepFeedbackView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from learning.models import TrailProgress, TrailStep
        step = get_object_or_404(TrailStep, pk=pk)
        progress = get_object_or_404(
            TrailProgress.objects.select_related('assignment'),
            step=step, assignment__user=request.user, completed_at__isnull=False,
        )
        usefulness = request.POST.get('usefulness', '')
        if usefulness not in ('helpful', 'partial', 'not_helpful'):
            return redirect('student_trail_list')
        progress.usefulness = usefulness
        progress.save(update_fields=('usefulness',))
        if step.content_object:
            track_event(request.user, ContentEvent.FEEDBACK_SUBMITTED, step.content_object, metadata={'trail_step_id': step.pk, 'usefulness': usefulness})
        return redirect('student_trail_list')


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentCourseDetailView(DetailView):
    model = Course
    template_name = 'students/course/course_detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get course object
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # get current module
            context['module'] = course.modules.get(
                id=self.kwargs['module_id'])
        else:
            # get first module
            context['module'] = course.modules.all()[0]

        context['course_enroll'] = get_enrollment(self.request.user, course)
        context['course_certificate'] = CourseCertificate.objects.filter(course=course, user=self.request.user).first()
        course_links = DocumentLink.objects.filter(
            content_type=ContentType.objects.get_for_model(Course), object_id=course.pk,
        ).select_related('document', 'document__current_version')
        context['linked_documents'] = [link for link in course_links if can_view_document(self.request.user, link.document)]
        return context


class CourseCertificateView(LoginRequiredMixin, DetailView):
    model = CourseCertificate
    template_name = 'students/course/certificate.html'
    context_object_name = 'certificate'

    def get_queryset(self):
        return CourseCertificate.objects.filter(user=self.request.user).select_related('course', 'user')


# class StudentCourseCompletedView(TemplateView):
#     model = Course
#     template_name = 'students/course/course_completed.html'


class StudentContentDetailView(DetailView):
    model = Course
    template_name = 'students/content/detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get course object
        course = self.get_object()

        context['course'] = course

        if 'module_id' in self.kwargs:
            # get current module
            context['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            # get first module
            context['module'] = course.modules.all()[0]

        course_enroll = CourseEnroll.objects.filter(course_id=course, student_id=self.request.user).first()

        if 'content_id' in self.kwargs:
            # get current module
            content = Content.objects.get(
                module_id=self.kwargs['module_id'],
                object_id=self.kwargs['content_id'],
                content_type__model=self.kwargs['model_name'],
            )
            context['current_content'] = content
            context['feedback_content_id'] = content.pk
            context['content_feedback'] = ContentFeedback.objects.filter(
                content_type=ContentType.objects.get_for_model(Content),
                object_id=content.pk,
                user=self.request.user,
            ).first()
            track_event(self.request.user, ContentEvent.CONTENT_OPENED, content)
            previous_open = ContentEvent.objects.filter(
                user=self.request.user,
                event_name=ContentEvent.CONTENT_OPENED,
                content_type=ContentType.objects.get_for_model(Content),
                object_id=content.pk,
            ).exclude(pk__isnull=True).exists()
            if previous_open:
                track_event(self.request.user, ContentEvent.CONTENT_RESUMED, content)
            if content.content_type.model == 'quiz':
                track_event(self.request.user, ContentEvent.QUIZ_STARTED, content)
            if content.content_type.model == 'video':
                track_event(self.request.user, ContentEvent.VIDEO_PROGRESS, content, progress_percent=0)

            if content.content_type.model == 'quiz':
                module_enroll = course_enroll.modules_enroll.filter(module_id=content.module).first()
                content_enroll = ContentEnroll.objects.filter(module_enroll_id=module_enroll,
                                                              content_id=content).first()
                if content_enroll:
                    quiz_result = content_enroll.quiz_result.first()
                    context['quiz_result'] = quiz_result

        context['course_enroll'] = course_enroll
        module_links = DocumentLink.objects.filter(
            content_type=ContentType.objects.get_for_model(context['module']),
            object_id=context['module'].pk,
        ).select_related('document', 'document__current_version')
        context['module_documents'] = [link for link in module_links if can_view_document(self.request.user, link.document)]
        context['course_documents'] = [
            link for link in DocumentLink.objects.filter(
                content_type=ContentType.objects.get_for_model(Course), object_id=course.pk,
            ).select_related('document', 'document__current_version')
            if can_view_document(self.request.user, link.document)
        ]

        return context


def get_next_content(request, *args, **kwargs):
    content_id = kwargs.get('content_id')
    content = Content.objects.get(
        module_id=kwargs['module_id'],
        object_id=content_id,
        content_type__model=kwargs['model_name'],
    )
    contents_all = content.module.contents.all().order_by('order')

    make_content_as_done(request.user, content)

    licycle = cycle(contents_all)
    nextelem = next(licycle)

    while True:
        thiselem, nextelem = nextelem, next(licycle)
        if thiselem == content:
            break

    if nextelem != contents_all.first():
        kwargs.update({
            'content_id': nextelem.object_id,
            'model_name': nextelem.content_type.model
        })
    else:
        modules_all = content.module.course.modules.all().order_by('order')

        licycle = cycle(modules_all)
        nextmodule = next(licycle)

        while True:
            thismodule, nextmodule = nextmodule, next(licycle)
            if thismodule == content.module:
                break
        
        if nextmodule != modules_all.first():
            content_next_module = nextmodule.contents.all().order_by('order').first()

            if content_next_module:
                kwargs.update({
                    'module_id': nextmodule.id,
                    'content_id': content_next_module.object_id,
                    'model_name': content_next_module.content_type.model
                })
        else:
            course_id = kwargs.get('pk')
            course = Course.objects.get(pk=course_id)
            event = 'course_completation'

            if not is_course_completed(course, event):
                if course.type == 'course':
                    create_gamification_report_item(request.user, event, object_source=course)
                
                # TODO
                # Aqui era pra redirecionar pra uma tela de "parabens" pelo curso concluído,
                # mas isso ta dando ruim no momento

    url = reverse_lazy('student_course_detail_module_content', kwargs=kwargs)
    return HttpResponseRedirect(url)

def get_back_content(request, *args, **kwargs):

    content_id = kwargs.get('content_id')
    content = Content.objects.get(
        module_id=kwargs['module_id'],
        object_id=content_id,
        content_type__model=kwargs['model_name'],
    )
    contents_all = content.module.contents.all().order_by('-order')

    make_content_as_done(request.user, content)

    licycle = cycle(contents_all)
    nextelem = next(licycle)

    while True:
        thiselem, nextelem = nextelem, next(licycle)
        if thiselem == content:
            break

    if nextelem != contents_all.first():
        kwargs.update({
            'content_id': nextelem.object_id,
            'model_name': nextelem.content_type.model
        })
    else:
        modules_all = content.module.course.modules.all().order_by('-order')

        licycle = cycle(modules_all)
        nextmodule = next(licycle)

        while True:
            thismodule, nextmodule = nextmodule, next(licycle)
            if thismodule == content.module:
                break
        
        if nextmodule != modules_all.first():
            content_next_module = nextmodule.contents.all().order_by('-order').first()

            if content_next_module:
                kwargs.update({
                    'module_id': nextmodule.id,
                    'content_id': content_next_module.object_id,
                    'model_name': content_next_module.content_type.model
                })
        else:
            course_id = kwargs.get('pk')
            course = Course.objects.get(pk=course_id)
            event = 'course_completation'

            if not is_course_completed(course, event):
                if course.type == 'course':
                    create_gamification_report_item(request.user, event, object_source=course)
                
                # TODO
                # Aqui era pra redirecionar pra uma tela de "parabens" pelo curso concluído,
                # mas isso ta dando ruim no momento

    url = reverse_lazy('student_course_detail_module_content', kwargs=kwargs)
    return HttpResponseRedirect(url)






def make_content_as_done(user, content):
    return mark_content_completed(user, content)


def track_content_event_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método não permitido.'}, status=405)
    try:
        payload = json.loads(request.body or '{}')
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido.'}, status=400)

    event_name = payload.get('event_name')
    allowed_events = {
        ContentEvent.CONTENT_ACTIVE,
        ContentEvent.VIDEO_PROGRESS,
        ContentEvent.ATTACHMENT_OPENED,
    }
    if event_name not in allowed_events:
        return JsonResponse({'ok': False, 'error': 'Evento não permitido.'}, status=400)

    try:
        content = Content.objects.select_related('module__course').get(
            module_id=int(payload.get('module_id')),
            object_id=int(payload.get('content_id')),
            content_type__model=payload.get('model_name'),
        )
    except (Content.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Conteúdo não encontrado.'}, status=404)

    if not CourseEnroll.objects.filter(course_id=content.module.course, student_id=request.user).exists():
        return JsonResponse({'ok': False, 'error': 'Curso não matriculado.'}, status=403)

    progress = payload.get('progress_percent')
    if progress is not None:
        progress = max(0, min(100, int(progress)))
    track_event(
        request.user,
        event_name,
        content,
        session_id=str(payload.get('session_id', ''))[:80],
        active_seconds=min(300, max(0, int(payload.get('active_seconds', 0) or 0))),
        progress_percent=progress,
    )
    return JsonResponse({'ok': True})


def save_quiz_view(request, *args, **kwargs):
    content_id = kwargs.get('content_id')
    content = Content.objects.get(
        module_id=kwargs['module_id'],
        object_id=content_id,
        content_type__model='quiz',
    )
    questions = []

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = request.POST
        data_ = dict(data.lists())
        data_.pop('csrfmiddlewaretoken')

        for k in data_.keys():
            question = Question.objects.get(pk=k)
            questions.append(question)

        user = request.user
        quiz = content.item

        score = 0
        multiplier = 100 / quiz.question.all().count()
        results = []
        correct_answer = None

        for q in questions:
            a_selected = request.POST.get(str(q.id))
            for a in q.answers.all():
                if a_selected == str(a.id):
                    if a.correct:
                        score += 1
                        correct_answer = a.id
                elif a.correct:
                    correct_answer = a.id

            results.append({
                str(q.id): {
                    'correct_answer': correct_answer,
                    'answered': a_selected
                }
            })
        score_ = score * multiplier

        course_enroll = CourseEnroll.objects.filter(course_id=content.module.course, student_id=user).first()
        module_enroll = ModuleEnroll.objects.filter(course_enroll_id=course_enroll, module_id=content.module).first()
        content_enroll = ContentEnroll.objects.filter(module_enroll_id=module_enroll, content_id=content).first()

        if not content_enroll:
            make_content_as_done(user, content)
            module_enroll = ModuleEnroll.objects.filter(course_enroll_id=course_enroll,
                                                        module_id=content.module).first()
            content_enroll = ContentEnroll.objects.filter(module_enroll_id=module_enroll, content_id=content).first()

        quiz_result = content_enroll.quiz_result.all().first()

        if not quiz_result:
            quiz_result = QuizResult.objects.create(content_enroll=content_enroll, score=score_)
            quiz_result.save()

            if score_ >= quiz.required_score_to_pass:
                create_gamification_report_item(user, 'passed_tests', object_source=quiz)

            track_event(
                user,
                ContentEvent.QUIZ_COMPLETED,
                content,
                progress_percent=round(score_),
                metadata={
                    'score': round(score_, 2),
                    'required_score': quiz.required_score_to_pass,
                    'wrong_questions': [item.pk for item in questions if not next((answer.correct for answer in item.answers.all() if str(answer.pk) == str(request.POST.get(str(item.pk)))), False)],
                },
            )

            for r in results:
                for k, v in r.items():
                    question = Question.objects.get(pk=int(k))

                    correct_answer_id = Answer.objects.get(pk=int(v.get('correct_answer')))
                    student_answer_id = Answer.objects.get(pk=int(v.get('answered')))

                    question_result = QuestionResult.objects.create(quiz_result_id=quiz_result,
                                                                    question_id=question,
                                                                    correct_answer_id=correct_answer_id,
                                                                    student_answer_id=student_answer_id)
                    question_result.save()

    return JsonResponse({'success': True, 'message': 'works', 'score': score_, 'results': results})


def is_course_completed(object, event):
    gr = GamificationReport.objects.filter(
        type_event=event, model_name=object.__class__.__name__, id_source=object.id)
    
    return True if gr else False
