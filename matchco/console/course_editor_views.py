"""
Course editor views for console - create/edit courses with modules and content.
"""

from django.utils.translation import gettext_lazy as gettext_lazy

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View
from django.db import transaction
from django.db.models import Q, Count
from django.utils.text import slugify

from courses.models import Course, Module, Content, Text, Video, File, Quiz, Question, Answer
from documents.models import Document, DocumentLink
from documents.services import sync_media_usage
from configuration.models import Organization
from matchco.core.utils import get_tenant_organization, get_tenant_user
from .views import ConsoleRecordNavigationMixin, ManagerRequiredMixin, active_content_queryset, active_organization, active_organization_queryset, service_catalog_queryset
from .quiz_editor_forms import QuizQuickCreateForm


def _set_tenant_owner(form, user):
    """Assign the tenant mirror required by course content ownership fields."""
    tenant_user = get_tenant_user(user)
    if not tenant_user:
        form.add_error(None, gettext_lazy('O usuário autenticado ainda não possui cadastro de TenantUser.'))
        return False
    form.instance.owner = tenant_user
    return True


def _scoped_modules(request):
    """Modules whose parent course belongs to the active tenant/company scope."""
    return Module.objects.filter(
        course__in=active_content_queryset(request, Course.objects.all(), write=False),
    )


def _scoped_content_items(request, model, content_type):
    item_ids = Content.objects.filter(
        content_type=content_type,
        module__course__in=active_content_queryset(request, Course.objects.all(), write=False),
    ).values('object_id')
    return model.objects.filter(pk__in=item_ids)


class RichTextEditorMixin:
    """Marks rich content fields for the shared local Quill editor."""
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'content' in form.fields:
            form.fields['content'].widget.attrs.update({
                'data-rich-editor': 'true',
                'class': 'rich-editor w-full rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white',
            })
        return form


class DocumentLinksEditorMixin:
    """Add the same tenant-safe document selector to course content editors."""

    def _document_queryset(self):
        organization = active_organization(self.request)
        tenant_organization = get_tenant_organization(organization) if organization else None
        documents = Document.objects.filter(status=Document.PUBLISHED)
        if tenant_organization:
            documents = documents.filter(
                Q(organization=tenant_organization) | Q(organization__isnull=True)
            )
        return documents.select_related('current_version').order_by('title')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['documents'] = forms.ModelMultipleChoiceField(
            queryset=self._document_queryset(),
            required=False,
            label=gettext_lazy('Documentos relacionados'),
            widget=forms.SelectMultiple(attrs={'size': 6, 'class': 'block w-full rounded-base border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading'}),
        )
        if getattr(self, 'object', None) and self.object.pk:
            content_type = ContentType.objects.get_for_model(self.object)
            form.initial['documents'] = Document.objects.filter(
                links__content_type=content_type,
                links__object_id=self.object.pk,
            )
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        rich_content = getattr(self.object, 'content', '') or getattr(self.object, 'description', '') or ''
        sync_media_usage(self.object, rich_content, actor=self.request.user)
        content_type = ContentType.objects.get_for_model(self.object)
        DocumentLink.objects.filter(
            content_type=content_type,
            object_id=self.object.pk,
        ).delete()
        creator = get_tenant_user(self.request.user)
        if creator:
            DocumentLink.objects.bulk_create([
                DocumentLink(document=document, content_type=content_type, object_id=self.object.pk, created_by=creator)
                for document in form.cleaned_data.get('documents', [])
            ])
        return response


class CourseContentNavigationMixin(ConsoleRecordNavigationMixin):
    """Navigate content records in the order shown inside the course editor."""

    content_model = None

    def get_navigation_queryset(self):
        content_type = ContentType.objects.get_for_model(self.content_model)
        current_link = get_object_or_404(
            Content.objects.select_related('module'),
            content_type=content_type,
            object_id=self.object.pk,
        )
        object_ids = list(
            Content.objects.filter(
                module__course_id=current_link.module.course_id,
                content_type=content_type,
            ).order_by('module__order', 'order', 'pk').values_list('object_id', flat=True)
        )
        records = self.content_model.objects.filter(pk__in=object_ids)
        by_id = {record.pk: record for record in records}
        return [by_id[object_id] for object_id in object_ids if object_id in by_id]

    def get_navigation_label(self, item):
        return item.title

    def get_navigation_list_url(self):
        content_type = ContentType.objects.get_for_model(self.content_model)
        current_link = get_object_or_404(
            Content.objects.select_related('module'),
            content_type=content_type,
            object_id=self.object.pk,
        )
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': current_link.module.course_id})


class CourseEditorListView(ManagerRequiredMixin, ListView):
    """List courses for editing in console"""
    model = Course
    template_name = 'console/course_editor_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_paginate_by(self, queryset):
        try:
            requested = int(self.request.GET.get('per_page', self.paginate_by))
        except (TypeError, ValueError):
            requested = self.paginate_by
        return requested if requested in (10, 20, 50, 100) else self.paginate_by

    def get_queryset(self):
        queryset = service_catalog_queryset(self.request, active_content_queryset(self.request, Course.objects), 'training')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(slug__icontains=query))
        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_organization'] = active_organization(self.request)
        context['page_size'] = self.get_paginate_by(self.get_queryset())
        context['page_size_choices'] = (10, 20, 50, 100)
        query = self.request.GET.copy()
        query.pop('page', None)
        context['list_querystring'] = query.urlencode()
        return context


class CourseEditorDetailView(ConsoleRecordNavigationMixin, ManagerRequiredMixin, DetailView):
    """Edit course modules and content"""
    model = Course
    template_name = 'console/course_editor_detail.html'
    context_object_name = 'course'
    navigation_url_name = 'console:course-editor-detail'
    navigation_list_url_name = 'console:course-editor-list'
    navigation_label = 'Cursos'
    navigation_item_label = 'Curso'
    navigation_ordering = ('title', 'pk')

    def get_queryset(self):
        return active_content_queryset(self.request, Course.objects, write=False).annotate(students_count=Count('students'))

    def get(self, request, *args, **kwargs):
        """Redirect to course list when the course is not accessible in this company scope."""
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            messages.warning(request, gettext_lazy('Este curso não está disponível para a empresa selecionada.'))
            return redirect('console:course-list')

    def get_navigation_queryset(self):
        queryset = self.get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(slug__icontains=query))
        return queryset.order_by(*self.navigation_ordering)

    def get_navigation_label(self, item):
        return item.title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['modules'] = course.modules.all().order_by('order')
        context['active_organization'] = active_organization(self.request)
        # Esta tela lista os módulos do curso; não há um módulo selecionado
        # para justificar um contador/navegação de registros nesse cabeçalho.
        context['hide_record_navigation'] = True
        return context


class ModuleCreateView(DocumentLinksEditorMixin, ManagerRequiredMixin, CreateView):
    """Create a new module in a course"""
    model = Module
    template_name = 'console/module_form.html'
    fields = ['title', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        context['course'] = get_object_or_404(
            active_content_queryset(self.request, Course.objects),
            id=course_id
        )
        return context

    def form_valid(self, form):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(
            active_content_queryset(self.request, Course.objects, write=False),
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


class ModuleUpdateView(ConsoleRecordNavigationMixin, DocumentLinksEditorMixin, ManagerRequiredMixin, UpdateView):
    """Edit a module"""
    model = Module
    template_name = 'console/module_form.html'
    fields = ['title', 'description']
    navigation_url_name = 'console:module-edit'
    navigation_list_url_name = 'console:course-editor-detail'
    navigation_label = 'Módulos'
    navigation_item_label = 'Módulo'
    navigation_ordering = ('order', 'pk')

    def get_queryset(self):
        # Only allow editing modules from courses in the active organization
        return Module.objects.filter(
            course__in=active_content_queryset(self.request, Course.objects, write=False)
        )

    def get_navigation_queryset(self):
        return self.get_queryset().filter(course_id=self.object.course_id).order_by(*self.navigation_ordering)

    def get_navigation_label(self, item):
        return item.title

    def get_navigation_list_url(self):
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': self.object.course_id})

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
        module = get_object_or_404(_scoped_modules(request), id=kwargs['pk'])
        course_id = module.course_id

        # Verify organization access
        get_object_or_404(
            active_content_queryset(request, Course.objects, write=False),
            id=course_id
        )

        module.delete()
        messages.success(request, gettext_lazy('Module deleted successfully.'))
        return redirect('console:course-editor-detail', pk=course_id)


class ModuleReorderView(ManagerRequiredMixin, View):
    """Reorder modules via drag and drop"""
    def post(self, request, *args, **kwargs):
        course_id = kwargs['course_id']
        course = get_object_or_404(
            active_content_queryset(request, Course.objects, write=False),
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

        messages.success(request, gettext_lazy('Order updated successfully.'))
        return redirect('console:course-editor-detail', pk=course_id)


class ContentCreateView(ManagerRequiredMixin, CreateView):
    """Create content (Text, Video, File, etc) in a module"""
    model = Content
    template_name = 'console/content_form.html'
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        organization = getattr(self.request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        context['module'] = get_object_or_404(
            Module.objects.filter(
                Q(course__organization=tenant_organization) | Q(course__organization__isnull=True)
            ),
            id=module_id,
        )
        context['course'] = context['module'].course
        return context

    def get_success_url(self):
        module = get_object_or_404(_scoped_modules(self.request), id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class TextCreateView(RichTextEditorMixin, DocumentLinksEditorMixin, ManagerRequiredMixin, CreateView):
    """Create text content"""
    model = Text
    template_name = 'console/text_form.html'
    fields = ['title', 'content']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(_scoped_modules(self.request), id=module_id)
        context['course'] = context['module'].course
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        organization = getattr(self.request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        module = get_object_or_404(
            Module.objects.filter(
                Q(course__organization=tenant_organization) | Q(course__organization__isnull=True)
            ),
            id=module_id,
        )

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
        module = get_object_or_404(_scoped_modules(self.request), id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class TextUpdateView(CourseContentNavigationMixin, RichTextEditorMixin, DocumentLinksEditorMixin, ManagerRequiredMixin, UpdateView):
    """Edit text content"""
    model = Text
    template_name = 'console/text_form.html'
    fields = ['title', 'content']
    navigation_url_name = 'console:text-edit'
    navigation_list_url_name = 'console:course-editor-detail'
    navigation_label = 'Conteúdos de texto'
    content_model = Text

    def get_queryset(self):
        return _scoped_content_items(
            self.request, Text, ContentType.objects.get_for_model(Text),
        )

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


class VideoCreateView(DocumentLinksEditorMixin, ManagerRequiredMixin, CreateView):
    """Create video content"""
    model = Video
    template_name = 'console/video_form.html'
    fields = ['title', 'url']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(_scoped_modules(self.request), id=module_id)
        context['course'] = context['module'].course
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        organization = getattr(self.request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        module = get_object_or_404(
            Module.objects.filter(
                Q(course__organization=tenant_organization) | Q(course__organization__isnull=True)
            ),
            id=module_id,
        )

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
        module = get_object_or_404(_scoped_modules(self.request), id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class VideoUpdateView(CourseContentNavigationMixin, DocumentLinksEditorMixin, ManagerRequiredMixin, UpdateView):
    """Edit video content"""
    model = Video
    template_name = 'console/video_form.html'
    fields = ['title', 'url']
    navigation_url_name = 'console:video-edit'
    navigation_list_url_name = 'console:course-editor-detail'
    navigation_label = 'Vídeos'
    content_model = Video

    def get_queryset(self):
        return _scoped_content_items(
            self.request, Video, ContentType.objects.get_for_model(Video),
        )

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


class FileCreateView(DocumentLinksEditorMixin, ManagerRequiredMixin, CreateView):
    """Create file content (PDF, attachments, etc)"""
    model = File
    template_name = 'console/file_form.html'
    fields = ['title', 'file']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(_scoped_modules(self.request), id=module_id)
        context['course'] = context['module'].course
        context['file_types'] = 'PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ZIP'
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(_scoped_modules(self.request), id=module_id)

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
        module = get_object_or_404(_scoped_modules(self.request), id=self.kwargs['module_id'])
        return reverse_lazy('console:course-editor-detail', kwargs={'pk': module.course_id})


class FileUpdateView(CourseContentNavigationMixin, DocumentLinksEditorMixin, ManagerRequiredMixin, UpdateView):
    """Edit file content"""
    model = File
    template_name = 'console/file_form.html'
    fields = ['title', 'file']
    navigation_url_name = 'console:file-edit'
    navigation_list_url_name = 'console:course-editor-detail'
    navigation_label = 'Arquivos'
    content_model = File

    def get_queryset(self):
        return _scoped_content_items(
            self.request, File, ContentType.objects.get_for_model(File),
        )

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
        context['module'] = get_object_or_404(_scoped_modules(self.request), id=module_id)
        context['course'] = context['module'].course
        return context

    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        organization = getattr(self.request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        module = get_object_or_404(
            Module.objects.filter(
                Q(course__organization=tenant_organization) | Q(course__organization__isnull=True)
            ),
            id=module_id,
        )

        # Set owner and organization
        if not _set_tenant_owner(form, self.request.user):
            return self.form_invalid(form)
        if tenant_organization:
            form.instance.organization = tenant_organization

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
        content = get_object_or_404(
            Content.objects.filter(
                module__course__in=active_content_queryset(request, Course.objects.all(), write=False),
            ),
            id=kwargs['pk'],
        )
        module = content.module
        course_id = module.course_id

        content.delete()
        messages.success(request, gettext_lazy('Content deleted successfully.'))
        return redirect('console:course-editor-detail', pk=course_id)


class ContentReorderView(ManagerRequiredMixin, View):
    """Reorder content via drag and drop"""
    def post(self, request, *args, **kwargs):
        module_id = kwargs['module_id']
        module = get_object_or_404(_scoped_modules(request), id=module_id)

        # Get new order from request
        order_data = request.POST.getlist('content_order[]')

        with transaction.atomic():
            for position, content_id in enumerate(order_data, 1):
                Content.objects.filter(id=content_id, module=module).update(order=position)

        messages.success(request, gettext_lazy('Content order updated.'))
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
        return Module.objects.filter(
            Q(course__organization=tenant_organization) | Q(course__organization__isnull=True)
        )

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
        tenant_organization = get_tenant_organization(organization) if organization else None
        all_quizzes = Quiz.objects.filter(
            organization=tenant_organization
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

        organization = getattr(request, 'active_organization', None)
        tenant_organization = get_tenant_organization(organization) if organization else None
        module = get_object_or_404(
            Module.objects.filter(
                Q(course__organization=tenant_organization) | Q(course__organization__isnull=True)
            ),
            id=module_id,
        )
        quiz = get_object_or_404(
            active_organization_queryset(request, Quiz.objects.all(), 'organization_id'),
            id=quiz_id,
        )

        # Check organization access
        if not tenant_organization or quiz.organization_id != tenant_organization.id:
            messages.error(request, gettext_lazy('You do not have access to this quiz.'))
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
