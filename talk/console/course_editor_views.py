"""
Course editor views for console - create/edit courses with modules and content.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from courses.models import Course, Module, Content, Text, Video, File, Quiz, Question, Answer
from configuration.models import Organization
from cep.core.utils import get_tenant_organization, get_tenant_user
from .views import ManagerRequiredMixin, active_organization_queryset, active_organization
from .quiz_editor_forms import QuizQuickCreateForm


def _set_tenant_owner(form, user):
    """Assign the tenant mirror required by course content ownership fields."""
    tenant_user = get_tenant_user(user)
    if not tenant_user:
        form.add_error(None, 'O usuário autenticado ainda não possui cadastro de TenantUser.')
        return False
    form.instance.owner = tenant_user
    return True


class CourseEditorListView(ManagerRequiredMixin, ListView):
    """List courses for editing in console"""
    model = Course
    template_name = 'console/course_editor_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        queryset = active_organization_queryset(self.request, Course.objects)
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(slug__icontains=query))
        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_organization'] = active_organization(self.request)
        return context


class CourseEditorDetailView(ManagerRequiredMixin, DetailView):
    """Edit course modules and content"""
    model = Course
    template_name = 'console/course_editor_detail.html'
    context_object_name = 'course'

    def get_queryset(self):
        return active_organization_queryset(self.request, Course.objects)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['modules'] = course.modules.all().order_by('order')
        context['active_organization'] = active_organization(self.request)
        return context


class ModuleCreateView(ManagerRequiredMixin, CreateView):
    """Create a new module in a course"""
    model = Module
    template_name = 'console/module_form.html'
    fields = ['title', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        context['course'] = get_object_or_404(
            active_organization_queryset(self.request, Course.objects),
            id=course_id
        )
        return context

    def form_valid(self, form):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(
            active_organization_queryset(self.request, Course.objects),
            id=course_id
        )
        form.instance.course = course
        # Auto-set order to last + 1
        last_module = course.modules.order_by('order').last()
        form.instance.order = (last_module.order + 1) if last_module else 1
        messages.success(self.request, f'Module "{form.instance.title}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': self.kwargs['course_id']})


class ModuleUpdateView(ManagerRequiredMixin, UpdateView):
    """Edit a module"""
    model = Module
    template_name = 'console/module_form.html'
    fields = ['title', 'description']

    def get_queryset(self):
        # Only allow editing modules from courses in the active organization
        return Module.objects.filter(
            course__in=active_organization_queryset(self.request, Course.objects)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context

    def get_success_url(self):
        if self.object.course_id:
            return reverse_lazy('console:course-editor-detail', kwargs={'pk': self.object.course_id})
        return reverse_lazy('console:course-editor-list')


class ModuleDeleteView(ManagerRequiredMixin, View):
    """Delete a module"""
    def post(self, request, *args, **kwargs):
        module = get_object_or_404(Module, id=kwargs['pk'])
        course_id = module.course_id

        # Verify organization access
        get_object_or_404(
            active_organization_queryset(request, Course.objects),
            id=course_id
        )

        module.delete()
        messages.success(request, 'Module deleted successfully.')
        return redirect('console:course-editor-detail', pk=course_id)


class ModuleReorderView(ManagerRequiredMixin, View):
    """Reorder modules via drag and drop"""
    def post(self, request, *args, **kwargs):
        course_id = kwargs['course_id']
        course = get_object_or_404(
            active_organization_queryset(request, Course.objects),
            id=course_id
        )

        # Get new order from request
        order_data = request.POST.getlist('module_order[]')

        with transaction.atomic():
            for position, module_id in enumerate(order_data, 1):
                Module.objects.filter(id=module_id, course=course).update(order=position)

            # Also handle content order within each module
            for module_id in order_data:
                content_order_key = f'content_order_{module_id}'
                if content_order_key in request.POST:
                    content_ids = request.POST.get(content_order_key, '').split(',')
                    module = Module.objects.get(id=module_id, course=course)
                    for position, content_id in enumerate(content_ids, 1):
                        if content_id:  # Skip empty strings
                            Content.objects.filter(id=content_id, module=module).update(order=position)

        messages.success(request, 'Order updated successfully.')
        return redirect('console:course-editor-detail', pk=course_id)


class ContentCreateView(ManagerRequiredMixin, CreateView):
    """Create content (Text, Video, File, etc) in a module"""
    model = Content
    template_name = 'console/content_form.html'
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(Module, id=module_id)
        context['course'] = context['module'].course
        return context

    def get_success_url(self):
        module = Module.objects.get(id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class TextCreateView(ManagerRequiredMixin, CreateView):
    """Create text content"""
    model = Text
    template_name = 'console/text_form.html'
    fields = ['title']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(Module, id=module_id)
        context['course'] = context['module'].course
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)

        if not _set_tenant_owner(form, self.request.user):
            return self.form_invalid(form)

        response = super().form_valid(form)

        # Create Content link
        content_type_id = 12  # Text content type ID - adjust if needed
        from django.contrib.contenttypes.models import ContentType
        text_ct = ContentType.objects.get_for_model(Text)

        last_content = module.contents.order_by('order').last()
        content_order = (last_content.order + 1) if last_content else 1

        Content.objects.create(
            module=module,
            content_type=text_ct,
            object_id=form.instance.id,
            order=content_order,
        )

        messages.success(self.request, f'Text "{form.instance.title}" created successfully.')
        return response

    def get_success_url(self):
        module = Module.objects.get(id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class TextUpdateView(ManagerRequiredMixin, UpdateView):
    """Edit text content"""
    model = Text
    template_name = 'console/text_form.html'
    fields = ['title']

    def get_queryset(self):
        return Text.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType
        text_ct = ContentType.objects.get_for_model(Text)
        content = Content.objects.get(content_type=text_ct, object_id=self.object.id)
        context['course'] = content.module.course
        context['module'] = content.module
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Text "{form.instance.title}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        # Find the module that contains this text
        from django.contrib.contenttypes.models import ContentType
        text_ct = ContentType.objects.get_for_model(Text)
        content = Content.objects.get(content_type=text_ct, object_id=self.object.id)
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': content.module.course_id})


class VideoCreateView(ManagerRequiredMixin, CreateView):
    """Create video content"""
    model = Video
    template_name = 'console/video_form.html'
    fields = ['title', 'url']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(Module, id=module_id)
        context['course'] = context['module'].course
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)

        if not _set_tenant_owner(form, self.request.user):
            return self.form_invalid(form)

        response = super().form_valid(form)

        # Create Content link
        from django.contrib.contenttypes.models import ContentType
        video_ct = ContentType.objects.get_for_model(Video)

        last_content = module.contents.order_by('order').last()
        content_order = (last_content.order + 1) if last_content else 1

        Content.objects.create(
            module=module,
            content_type=video_ct,
            object_id=form.instance.id,
            order=content_order,
        )

        messages.success(self.request, f'Video "{form.instance.title}" created successfully.')
        return response

    def get_success_url(self):
        module = Module.objects.get(id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class VideoUpdateView(ManagerRequiredMixin, UpdateView):
    """Edit video content"""
    model = Video
    template_name = 'console/video_form.html'
    fields = ['title', 'url']

    def get_queryset(self):
        return Video.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType
        video_ct = ContentType.objects.get_for_model(Video)
        content = Content.objects.get(content_type=video_ct, object_id=self.object.id)
        context['course'] = content.module.course
        context['module'] = content.module
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Video "{form.instance.title}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        # Find the module that contains this video
        from django.contrib.contenttypes.models import ContentType
        video_ct = ContentType.objects.get_for_model(Video)
        content = Content.objects.get(content_type=video_ct, object_id=self.object.id)
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': content.module.course_id})


class FileCreateView(ManagerRequiredMixin, CreateView):
    """Create file content (PDF, attachments, etc)"""
    model = File
    template_name = 'console/file_form.html'
    fields = ['title', 'file']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(Module, id=module_id)
        context['course'] = context['module'].course
        context['file_types'] = 'PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ZIP'
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)

        if not _set_tenant_owner(form, self.request.user):
            return self.form_invalid(form)

        response = super().form_valid(form)

        # Create Content link
        from django.contrib.contenttypes.models import ContentType
        file_ct = ContentType.objects.get_for_model(File)

        last_content = module.contents.order_by('order').last()
        content_order = (last_content.order + 1) if last_content else 1

        Content.objects.create(
            module=module,
            content_type=file_ct,
            object_id=form.instance.id,
            order=content_order,
        )

        messages.success(self.request, f'File "{form.instance.title}" uploaded successfully.')
        return response

    def get_success_url(self):
        module = Module.objects.get(id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class FileUpdateView(ManagerRequiredMixin, UpdateView):
    """Edit file content"""
    model = File
    template_name = 'console/file_form.html'
    fields = ['title', 'file']

    def get_queryset(self):
        return File.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType
        file_ct = ContentType.objects.get_for_model(File)
        content = Content.objects.get(content_type=file_ct, object_id=self.object.id)
        context['course'] = content.module.course
        context['module'] = content.module
        context['file_types'] = 'PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ZIP'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'File "{form.instance.title}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        # Find the module that contains this file
        from django.contrib.contenttypes.models import ContentType
        file_ct = ContentType.objects.get_for_model(File)
        content = Content.objects.get(content_type=file_ct, object_id=self.object.id)
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': content.module.course_id})


class QuizCreateView(ManagerRequiredMixin, CreateView):
    """Create quiz/test in a module"""
    model = Quiz
    form_class = QuizQuickCreateForm
    template_name = 'console/quiz_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(Module, id=module_id)
        context['course'] = context['module'].course
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)

        # Set owner and organization
        if not _set_tenant_owner(form, self.request.user):
            return self.form_invalid(form)
        organization = getattr(self.request, 'active_organization', None)
        if organization:
            form.instance.organization = organization

        response = super().form_valid(form)

        # Create Content link
        from django.contrib.contenttypes.models import ContentType
        quiz_ct = ContentType.objects.get_for_model(Quiz)

        last_content = module.contents.order_by('order').last()
        content_order = (last_content.order + 1) if last_content else 1

        Content.objects.create(
            module=module,
            content_type=quiz_ct,
            object_id=form.instance.id,
            order=content_order,
        )

        messages.success(self.request, f'Quiz "{form.instance.title}" created successfully.')
        return response

    def get_success_url(self):
        # Redirect to editor to add questions to the quiz
        quiz_id = self.object.id
        return reverse_lazy('console:quiz-editor', kwargs={'pk': quiz_id})


class ContentDeleteView(ManagerRequiredMixin, View):
    """Delete content"""
    def post(self, request, *args, **kwargs):
        content = get_object_or_404(Content, id=kwargs['pk'])
        module = content.module
        course_id = module.course_id

        content.delete()
        messages.success(request, 'Content deleted successfully.')
        return redirect('console:course-editor-detail', pk=course_id)


class ContentReorderView(ManagerRequiredMixin, View):
    """Reorder content via drag and drop"""
    def post(self, request, *args, **kwargs):
        module_id = kwargs['module_id']
        module = get_object_or_404(Module, id=module_id)

        # Get new order from request
        order_data = request.POST.getlist('content_order[]')

        with transaction.atomic():
            for position, content_id in enumerate(order_data, 1):
                Content.objects.filter(id=content_id, module=module).update(order=position)

        messages.success(request, 'Content order updated.')
        return redirect('console:course-editor-detail', pk=module.course_id)


class QuizAddToModuleSelectView(ManagerRequiredMixin, DetailView):
    """Choose between creating a new quiz or selecting existing quiz to add to module"""
    model = Module
    template_name = 'console/quiz_add_to_module_select.html'
    context_object_name = 'module'
    pk_url_kwarg = 'module_id'

    def get_queryset(self):
        # Filter modules by course organization
        organization = getattr(self.request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        if not tenant_organization:
            return Module.objects.none()
        return Module.objects.filter(course__organization=tenant_organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.get_object()
        context['course'] = module.course

        # Get existing quizzes in the organization
        organization = getattr(self.request, 'active_organization', None)

        # Get IDs of quizzes already in this module
        from django.contrib.contenttypes.models import ContentType
        quiz_ct = ContentType.objects.get_for_model(Quiz)
        quiz_ids_in_module = Content.objects.filter(
            module=module,
            content_type=quiz_ct
        ).values_list('object_id', flat=True)

        # Get all quizzes except those already in the module
        all_quizzes = Quiz.objects.filter(
            organization=organization
        ).order_by('-created')

        existing_quizzes = all_quizzes.exclude(
            id__in=quiz_ids_in_module
        )

        context['existing_quizzes'] = existing_quizzes
        context['total_quizzes'] = all_quizzes.count()
        context['quizzes_in_module'] = quiz_ids_in_module.count()

        return context


class QuizSelectAndAddView(ManagerRequiredMixin, View):
    """Add an existing quiz to a module"""
    def post(self, request, *args, **kwargs):
        module_id = kwargs.get('module_id')
        quiz_id = request.POST.get('quiz_id')

        module = get_object_or_404(Module, id=module_id)
        quiz = get_object_or_404(Quiz, id=quiz_id)

        # Check organization access
        organization = getattr(request, 'active_organization', None)
        if not organization or quiz.organization_id != organization.id:
            messages.error(request, 'You do not have access to this quiz.')
            return redirect('console:course-editor-detail', pk=module.course_id)

        # Check if quiz is already in module
        from django.contrib.contenttypes.models import ContentType
        quiz_ct = ContentType.objects.get_for_model(Quiz)

        if Content.objects.filter(module=module, content_type=quiz_ct, object_id=quiz.id).exists():
            messages.warning(request, f'Quiz "{quiz.title}" is already in this module.')
            return redirect('console:course-editor-detail', pk=module.course_id)

        # Create Content link
        last_content = module.contents.order_by('order').last()
        content_order = (last_content.order + 1) if last_content else 1

        Content.objects.create(
            module=module,
            content_type=quiz_ct,
            object_id=quiz.id,
            order=content_order,
        )

        messages.success(request, f'Quiz "{quiz.title}" added to module successfully.')
        return redirect('console:course-editor-detail', pk=module.course_id)
