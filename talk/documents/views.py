import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from audience.services import eligibility
from cep.core.utils import get_tenant_user
from console.views import ManagerRequiredMixin, active_organization_queryset

from .forms import DocumentForm
from .models import Document, DocumentEvent, DocumentLink, DocumentView
from .services import archive_document, can_download, can_view, create_version, record_view


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'documents/list.html'
    context_object_name = 'documents'
    paginate_by = 24

    def get_queryset(self):
        queryset = Document.objects.filter(status=Document.PUBLISHED).select_related('organization', 'current_version')
        queryset = active_organization_queryset(self.request, queryset)
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(code__icontains=query)
        return [document for document in queryset if can_view(self.request.user, document)]


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'document'

    def get_object(self, queryset=None):
        document = super().get_object(queryset or Document.objects.select_related('current_version'))
        if not can_view(self.request.user, document):
            raise Http404
        version = document.current_version
        mime_type = (version.mime_type if version else '').lower()
        filename = (version.file.name if version and version.file else '').lower()
        if mime_type == 'application/pdf' or filename.endswith('.pdf'):
            document.preview_kind = 'pdf'
        elif mime_type.startswith('image/') or filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
            document.preview_kind = 'image'
        else:
            document.preview_kind = ''
        session_id = self.request.GET.get('session', '')[:80]
        record_view(self.request.user, document, document.current_version, session_id=session_id)
        return document


class DocumentEventView(LoginRequiredMixin, View):
    def post(self, request, slug):
        document = get_object_or_404(Document.objects.select_related('current_version'), slug=slug, status=Document.PUBLISHED)
        if not can_view(request.user, document):
            raise Http404
        try:
            payload = json.loads(request.body or '{}')
            seconds = int(payload.get('active_seconds', 0) or 0)
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'Dados inválidos.'}, status=400)
        record_view(request.user, document, document.current_version, session_id=str(payload.get('session_id', '')), active_seconds=seconds)
        return JsonResponse({'ok': True})


class DocumentDownloadView(LoginRequiredMixin, View):
    def get(self, request, slug):
        document = get_object_or_404(Document.objects.select_related('current_version'), slug=slug, status=Document.PUBLISHED)
        version = document.current_version
        if not can_download(request.user, document) or not version or not version.file:
            raise Http404
        record_view(request.user, document, version, session_id=request.GET.get('session', ''), downloaded=True)
        return FileResponse(version.file.open('rb'), as_attachment=True, filename=version.file.name.rsplit('/', 1)[-1])


class DocumentConsoleListView(ManagerRequiredMixin, ListView):
    model = Document
    template_name = 'console/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        queryset = active_organization_queryset(self.request, Document.objects.all()).select_related('organization', 'owner', 'current_version')
        query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(code__icontains=query)
        if status in dict(Document.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset


class DocumentConsoleCreateView(ManagerRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'console/document_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['active_organization'] = getattr(self.request, 'active_organization', None)
        return kwargs

    def form_valid(self, form):
        tenant_user = get_tenant_user(self.request.user)
        if tenant_user:
            form.instance.owner = tenant_user
        response = super().form_valid(form)
        if (form.cleaned_data.get('initial_file') or form.cleaned_data.get('initial_body')) and tenant_user:
            create_version(
                self.object, tenant_user,
                file=form.cleaned_data.get('initial_file'),
                body=form.cleaned_data.get('initial_body', ''),
                change_summary=form.cleaned_data.get('change_summary', 'Versão inicial'),
                expires_at=form.cleaned_data.get('initial_expires_at'),
            )
        return response

    def get_success_url(self):
        return reverse('console:document-edit', kwargs={'pk': self.object.pk})


class DocumentConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'console/document_form.html'

    def get_queryset(self):
        return active_organization_queryset(self.request, Document.objects.all())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['active_organization'] = getattr(self.request, 'active_organization', None)
        return kwargs

    def get_success_url(self):
        return reverse('console:document-edit', kwargs={'pk': self.object.pk})


class DocumentVersionCreateView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_organization_queryset(request, Document.objects.all()), pk=pk)
        create_version(
            document, request.user, file=request.FILES.get('file'),
            body=request.POST.get('body', ''),
            change_summary=request.POST.get('change_summary', ''),
            expires_at=parse_datetime(request.POST.get('expires_at', '') or '')
                if request.POST.get('expires_at') else None,
        )
        return redirect('console:document-edit', pk=document.pk)


class DocumentVersionCompareView(ManagerRequiredMixin, View):
    template_name = 'console/document_version_compare.html'

    def get(self, request, pk):
        document = get_object_or_404(active_organization_queryset(request, Document.objects.prefetch_related('versions')), pk=pk)
        versions = list(document.versions.order_by('version_number'))
        if len(versions) < 2:
            return redirect('console:document-edit', pk=document.pk)
        to_version = next((item for item in versions if str(item.pk) == request.GET.get('to')), versions[-1])
        from_version = next((item for item in versions if str(item.pk) == request.GET.get('from')), versions[-2])
        for version in (from_version, to_version):
            stats = DocumentView.objects.filter(version=version).aggregate(
                views=Count('id'), readers=Count('user', distinct=True), active=Sum('active_seconds'), downloads=Sum('download_count'),
            )
            version.metric_views = stats['views'] or 0
            version.metric_readers = stats['readers'] or 0
            version.metric_active = stats['active'] or 0
            version.metric_downloads = stats['downloads'] or 0
        return render(request, self.template_name, {
            'document': document, 'versions': versions,
            'from_version': from_version, 'to_version': to_version,
        })


class DocumentArchiveView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_organization_queryset(request, Document.objects.all()), pk=pk)
        archive_document(document, request.user)
        return redirect('console:document-edit', pk=document.pk)
