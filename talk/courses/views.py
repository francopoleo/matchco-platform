from django import forms
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.list import ListView
from django.shortcuts import redirect, get_object_or_404
from django.http import Http404
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from students.forms import CourseEnrollForm
from courses.models import Course, Module, Content, Subject, Tests
from courses.forms import CourseManagementForm, ModuleFormSet
from cep.utils import filter_entries
from audience.selectors import eligible_items
from learning.services import get_enrollment, enrollment_progress
from django.contrib.contenttypes.models import ContentType
from documents.models import DocumentLink
from documents.services import can_view as can_view_document


class OwnerMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin(object):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin,
                       LoginRequiredMixin,
                       PermissionRequiredMixin):
    login_url = reverse_lazy('login')
    model = Course
    form_class = CourseManagementForm
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'
    permission_required = 'courses.view_course'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'


class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        formset = ModuleFormSet(instance=self.course, data=data)
        for form in formset.forms:
            form.form_user = self.request.user
        return formset

    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course,
                                        id=pk,
                                        owner=request.user)
        return super().dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course,
                                        'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course,
                                        'formset': formset})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    def get(self, request, module_id, model_name, id=None):
        self.request.session['module'] = module_id
        return redirect(f'/admin/courses/{model_name}/create/')


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module,
                                   id=module_id,
                                   course__owner=request.user)

        return self.render_to_response({'module': module})


class ModuleOrderView(CsrfExemptMixin,
                      JsonRequestResponseMixin,
                      View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id,
                                  course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin,
                       JsonRequestResponseMixin,
                       View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id,
                                   module__course__owner=request.user) \
                .update(order=order)
        return self.render_json_response({'saved': 'OK'})


class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course/list.html'

    def get(self, request, subject=None):
        active_organization_id = getattr(request.user, '_active_organization_id', None)
        subject_courses = Course.objects.filter(type='course', state='published')
        if active_organization_id:
            subject_courses = subject_courses.filter(organization_id=active_organization_id)
        subjects = Subject.objects.filter(courses__in=subject_courses).annotate(total_courses=Count('courses', distinct=True))

        my_courses = Course.objects.filter(students__in=[self.request.user], type="course")
        if active_organization_id:
            my_courses = my_courses.filter(organization_id=active_organization_id)
        all_courses = Course.objects.filter(state="published", type="course").annotate(
            total_modules=Count('modules')).exclude(
            students__in=[self.request.user])
        if active_organization_id:
            all_courses = all_courses.filter(organization_id=active_organization_id)

        all_courses = filter_entries(all_courses, self.request.user)
        all_courses = eligible_items(all_courses, self.request.user)

        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            if my_courses:
                my_courses = my_courses.filter(subject=subject)
            if all_courses:
                all_courses = [course for course in all_courses if course.subject == subject]

        return self.render_to_response({'subjects': subjects,
                                        'subject': subject,
                                        'courses': all_courses,
                                        'my_courses': my_courses,
                                        'available_course_count': len(all_courses),
                                        'enrolled_course_count': my_courses.count(),
                                        'visible_course_count': len(all_courses) + my_courses.count(),
                                        'course_state': True
                                        })


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_queryset(self):
        return super().get_queryset().filter(state='published')

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        slug = self.kwargs.get(self.slug_url_kwarg, self.kwargs.get('slug'))
        for course in eligible_items(queryset, self.request.user):
            if course.slug == slug:
                return course
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(
            initial={'course': self.object})
        context['course_enroll'] = get_enrollment(self.request.user, self.object)
        context['course_progress'] = enrollment_progress(context['course_enroll']) if context['course_enroll'] else 0
        linked_documents = DocumentLink.objects.filter(
            content_type=ContentType.objects.get_for_model(Course), object_id=self.object.pk,
        ).select_related('document', 'document__current_version')
        context['linked_documents'] = [link for link in linked_documents if can_view_document(self.request.user, link.document)]
        if self.object.type == 'test':
            context['test_state'] = True
        else:
            context['course_state'] = True
        return context


class QuestionCreateRedirectView(TemplateResponseMixin, View):
    def get(self, request, item_id):
        self.request.session['quiz_id'] = item_id
        return redirect('/admin/courses/question/')


class TestListView(TemplateResponseMixin, View):
    model = Tests
    template_name = 'tests/test/list.html'

    def get(self, request, subject=None):
        subjects = Subject.objects.annotate(total_courses=Count('courses'))

        my_tests = Tests.objects.filter(students__in=[self.request.user], type="test")
        all_tests = Tests.objects.filter(state="published", type="test").annotate(
            total_modules=Count('modules')).exclude(
            students__in=[self.request.user])

        all_tests = filter_entries(all_tests, self.request.user)

        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            if my_tests:
                my_tests = my_tests.filter(subject=subject)
            if all_tests:
                all_tests = [test for test in all_tests if test.subject == subject]

        return self.render_to_response({'subjects': subjects,
                                        'subject': subject,
                                        'tests': all_tests,
                                        'my_tests': my_tests,
                                        'test_state': True
                                        })
