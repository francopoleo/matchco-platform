from itertools import cycle
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import BACKEND_SESSION_KEY, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from courses.models import Course, Content, Question, Quiz, Answer
from .forms import CourseEnrollForm
from .models import CourseEnroll, ModuleEnroll, ContentEnroll, QuizResult, QuestionResult

from gamification.utils import create_gamification_report_item
from gamification.models import GamificationReport
from learning.services import enroll_user, get_enrollment, mark_content_completed


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
        return context


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
            content = Content.objects.get(object_id=self.kwargs['content_id'],
                                          content_type__model=self.kwargs['model_name'])
            context['current_content'] = content

            if content.content_type.model == 'quiz':
                module_enroll = course_enroll.modules_enroll.filter(module_id=content.module).first()
                content_enroll = ContentEnroll.objects.filter(module_enroll_id=module_enroll,
                                                              content_id=content).first()
                if content_enroll:
                    quiz_result = content_enroll.quiz_result.first()
                    context['quiz_result'] = quiz_result

        context['course_enroll'] = course_enroll

        return context


def get_next_content(request, *args, **kwargs):
    content_id = kwargs.get('content_id')
    content = Content.objects.get(object_id=content_id, content_type__model=kwargs['model_name'])
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
    content = Content.objects.get(object_id=content_id, content_type__model=kwargs['model_name'])
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


def save_quiz_view(request, *args, **kwargs):
    content_id = kwargs.get('content_id')
    content = Content.objects.get(object_id=content_id, content_type__model='quiz')
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
