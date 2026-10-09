from django.utils.translation import gettext_lazy as gettext_lazy
import hashlib
import json
import os
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, F, OuterRef, Subquery, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from audience.services import eligibility
from matchco.core.utils import get_tenant_organization, get_tenant_user
from console.views import (
    ManagerRequiredMixin, active_company_id, active_content_queryset,
    active_organization_queryset, content_company_queryset,
)

from .forms import DocumentForm, MediaAssetForm, MediaBulkUploadForm, MediaCollectionForm
from .models import Document, DocumentEvent, DocumentLink, DocumentShareLink, DocumentView, MediaAsset, MediaAssetAuditEvent, MediaAssetShareLink, MediaAssetUserState, MediaAssetVersion, MediaCollection, MediaTag, DocumentVersion
from .services import _announce_change, archive_document, can_download, can_view, can_view_media, create_version, generate_document_pdf, generate_document_thumbnail, generate_media_derivatives, record_view, remove_media_reference, sync_media_usage


def _audit_media(asset, request, event_name, **metadata):
    MediaAssetAuditEvent.objects.create(
        asset=asset,
        organization=asset.organization,
        actor=get_tenant_user(request.user) if getattr(request.user, 'is_authenticated', False) else None,
        event_name=event_name,
        metadata=metadata,
    )


def _audit_document(document, request, action, version=None, **metadata):
    actor = get_tenant_user(request.user) if getattr(request.user, 'is_authenticated', False) else None
    if actor:
        DocumentEvent.objects.create(
            document=document, version=version or document.current_version, user=actor,
            event_name=DocumentEvent.MANAGED, metadata={'action': action, **metadata},
        )


def _content_admin_url(content_type, object_id):
    route_names = {
        ('publishing', 'publication'): 'console:publication-edit',
        ('courses', 'course'): 'console:course-edit',
        ('courses', 'module'): 'console:module-edit',
        ('courses', 'text'): 'console:text-edit',
        ('courses', 'video'): 'console:video-edit',
        ('courses', 'file'): 'console:file-edit',
    }
    route_name = route_names.get((content_type.app_label, content_type.model))
    if not route_name:
        return ''
    try:
        return reverse(route_name, kwargs={'pk': object_id})
    except Exception:
        return ''


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'documents/list.html'
    context_object_name = 'documents'
    paginate_by = 24

    def get_queryset(self):
        queryset = Document.objects.filter(status=Document.PUBLISHED).select_related('organization', 'current_version')
        queryset = active_content_queryset(self.request, queryset)
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(code__icontains=query)
        return [document for document in queryset if can_view(self.request.user, document)]


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'document'

    def get_object(self, queryset=None):
        document = super().get_object(queryset or active_content_queryset(
            self.request, Document.objects.select_related('current_version'),
        ))
        if not can_view(self.request.user, document):
            raise Http404
        version = document.current_version
        mime_type = (version.display_mime_type if version else '').lower()
        filename = (version.display_file.name if version and version.display_file else '').lower()
        if mime_type == 'application/pdf' or filename.endswith('.pdf'):
            document.preview_kind = 'pdf'
        elif mime_type.startswith('image/') or filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
            document.preview_kind = 'image'
        elif mime_type in ('text/html', 'application/xhtml+xml') or filename.endswith(('.html', '.htm')) or (version and version.body):
            document.preview_kind = 'html'
        else:
            document.preview_kind = ''
        document.file_url = reverse('document-file', kwargs={'slug': document.slug})
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
        if not can_download(request.user, document) or not version or not version.display_file:
            if version and version.external_url and can_download(request.user, document):
                return redirect(version.external_url)
            raise Http404
        record_view(request.user, document, version, session_id=request.GET.get('session', ''), downloaded=True)
        file = version.display_file
        return FileResponse(file.open('rb'), as_attachment=True, filename=file.name.rsplit('/', 1)[-1])


class DocumentFileView(View):
    def get(self, request, slug):
        document = get_object_or_404(Document.objects.select_related('current_version'), slug=slug, status=Document.PUBLISHED)
        if not can_view(request.user, document):
            raise Http404
        version = document.current_version
        if not version:
            raise Http404
        if version.external_url:
            return redirect(version.external_url)
        if not version.display_file:
            raise Http404
        return FileResponse(version.display_file.open('rb'), content_type=version.display_mime_type or 'application/octet-stream')


class DocumentShareView(View):
    def get(self, request, token):
        link = get_object_or_404(DocumentShareLink.objects.select_related('document__current_version'), token=token, active=True)
        if not link.is_valid:
            raise Http404
        version = link.document.current_version
        if not version:
            raise Http404
        if version.external_url:
            return redirect(version.external_url)
        if not version.display_file:
            raise Http404
        bump_access_count(link)
        return FileResponse(version.display_file.open('rb'), content_type=version.display_mime_type or 'application/octet-stream')


class DocumentThumbnailView(View):
    def get(self, request, slug):
        document = get_object_or_404(Document.objects.select_related('current_version'), slug=slug, status=Document.PUBLISHED)
        if not can_view(request.user, document):
            raise Http404
        version = document.current_version
        if not version or not version.thumbnail_file:
            raise Http404
        return FileResponse(version.thumbnail_file.open('rb'), content_type='image/jpeg')


class MediaAssetServeView(View):
    def get(self, request, pk, variant=''):
        asset = get_object_or_404(MediaAsset, pk=pk, active=True, workflow_status__in=('approved', 'published'))
        if asset.is_expired:
            raise Http404
        if not asset.public_access:
            if not can_view_media(request.user, asset):
                raise Http404
        tenant_user = get_tenant_user(request.user) if request.user.is_authenticated else None
        if tenant_user:
            state, _ = MediaAssetUserState.objects.get_or_create(asset=asset, user=tenant_user)
            state.open_count += 1
            state.last_opened_at = timezone.now()
            state.save(update_fields=('open_count', 'last_opened_at', 'updated_at'))
        if variant:
            variant_fields = {'preview': 'preview_file', 'webp': 'webp_file', 'avif': 'avif_file'}
            stored_file = getattr(asset, variant_fields.get(variant, ''), None)
            if not stored_file:
                raise Http404
            bump_access_count(asset)
            return FileResponse(stored_file.open('rb'), content_type=f'image/{"avif" if variant == "avif" else "webp"}')
        if asset.external_url:
            if not asset.public_access:
                raise Http404
            bump_access_count(asset)
            return redirect(asset.external_url)
        if not asset.file:
            raise Http404
        bump_access_count(asset)
        return FileResponse(asset.file.open('rb'), content_type=asset.mime_type or 'application/octet-stream')


class MediaAssetShareView(View):
    def get(self, request, token):
        link = get_object_or_404(MediaAssetShareLink.objects.select_related('asset'), token=token, active=True)
        if not link.is_valid or link.asset.is_expired or link.asset.workflow_status not in ('approved', 'published'):
            raise Http404
        asset = link.asset
        bump_access_count(link)
        if asset.external_url:
            return redirect(asset.external_url)
        if not asset.file:
            raise Http404
        return FileResponse(asset.file.open('rb'), content_type=asset.mime_type or 'application/octet-stream')


class LegacyProtectedMediaView(View):
    """Compatibility endpoint for old storage URLs without public storage bypass."""

    def get(self, request, file_path, storage_prefix=''):
        normalized = f'{storage_prefix}{file_path}'.lstrip('/')
        if normalized.startswith('media-library/versions/'):
            raise Http404
        if normalized.startswith('media-library/'):
            asset = get_object_or_404(MediaAsset, file=normalized, active=True, workflow_status__in=('approved', 'published'))
            if asset.is_expired:
                raise Http404
            if not asset.public_access:
                if not request.user.is_authenticated:
                    raise Http404
                if not can_view_media(request.user, asset):
                    raise Http404
            bump_access_count(asset)
            return FileResponse(asset.file.open('rb'), content_type=asset.mime_type or 'application/octet-stream')
        if normalized.startswith('documents/versions/'):
            version = get_object_or_404(DocumentVersion.objects.select_related('document'), file=normalized)
            if not version.file or not can_view(request.user, version.document):
                raise Http404
            return FileResponse(version.file.open('rb'), content_type=version.mime_type or 'application/octet-stream')
        raise Http404


class DocumentConsoleListView(ManagerRequiredMixin, ListView):
    model = Document
    template_name = 'console/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        queryset = active_content_queryset(self.request, Document.objects.all()).select_related('organization', 'company', 'owner', 'current_version')
        query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(code__icontains=query)
        if status in dict(Document.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_companies'] = content_company_queryset(self.request)
        context['active_company_id'] = active_company_id(self.request)
        return context


class DocumentConsoleCreateView(ManagerRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'console/document_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['active_organization'] = getattr(self.request, 'active_organization', None)
        kwargs['company_queryset'] = content_company_queryset(self.request)
        kwargs['default_company_id'] = active_company_id(self.request)
        kwargs['company_required'] = bool(getattr(getattr(self.request, 'active_membership', None), 'company_id', None))
        return kwargs

    def form_valid(self, form):
        tenant_user = get_tenant_user(self.request.user)
        if form.cleaned_data.get('requires_approval') and form.cleaned_data.get('status') == Document.PUBLISHED:
            form.instance.status = Document.IN_REVIEW
        if tenant_user:
            form.instance.owner = tenant_user
        form.instance.organization = form.cleaned_data.get('organization')
        response = super().form_valid(form)
        if (form.cleaned_data.get('initial_file') or form.cleaned_data.get('initial_body')) and tenant_user:
            version = create_version(
                self.object, tenant_user,
                file=form.cleaned_data.get('initial_file'),
                body=form.cleaned_data.get('initial_body', ''),
                source_type=form.cleaned_data.get('initial_source_type', ''),
                change_summary=form.cleaned_data.get('change_summary', 'Versão inicial'),
                expires_at=form.cleaned_data.get('initial_expires_at'),
            )
        else:
            version = None
        _audit_document(self.object, self.request, 'created', version=version)
        return response

    def get_success_url(self):
        return reverse('console:document-edit', kwargs={'pk': self.object.pk})

class DocumentConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'console/document_form.html'

    def get_queryset(self):
        return active_content_queryset(self.request, Document.objects.all(), write=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['active_organization'] = getattr(self.request, 'active_organization', None)
        kwargs['company_queryset'] = content_company_queryset(self.request)
        kwargs['default_company_id'] = active_company_id(self.request)
        kwargs['company_required'] = bool(getattr(getattr(self.request, 'active_membership', None), 'company_id', None))
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        version = self.object.current_version
        # Keep the current text visible in the editor. It is only versioned
        # again when the editor value is actually changed.
        initial['initial_body'] = version.body if version else ''
        initial['initial_source_type'] = version.source_type if version else DocumentVersion.SOURCE_RICH_TEXT
        return initial

    def form_valid(self, form):
        tenant_user = get_tenant_user(self.request.user)
        if form.cleaned_data.get('requires_approval') and self.object.status == Document.PUBLISHED:
            form.instance.status = Document.IN_REVIEW
        response = super().form_valid(form)
        body_changed = 'initial_body' in form.changed_data
        if (form.cleaned_data.get('initial_file') or body_changed) and tenant_user:
            version = create_version(
                self.object, tenant_user,
                file=form.cleaned_data.get('initial_file'),
                body=form.cleaned_data.get('initial_body', ''),
                source_type=form.cleaned_data.get('initial_source_type', ''),
                change_summary=form.cleaned_data.get('change_summary', 'Nova versão'),
                expires_at=form.cleaned_data.get('initial_expires_at'),
            )
            _audit_document(self.object, self.request, 'new_version', version=version)
        else:
            _audit_document(self.object, self.request, 'updated')
        return response

    def get_success_url(self):
        return reverse('console:document-edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_share_links'] = self.object.share_links.filter(active=True, expires_at__gt=timezone.now())
        context['document_usage_count'] = self.object.links.count()
        context['document_links'] = list(self.object.links.select_related('content_type', 'created_by').order_by('-created_at'))
        for link in context['document_links']:
            link.content_admin_url = _content_admin_url(link.content_type, link.object_id)
        return context


class DocumentUsageConsoleView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/document_usage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = get_object_or_404(active_content_queryset(self.request, Document.objects.all(), write=True), pk=self.kwargs['pk'])
        links = list(document.links.select_related('content_type', 'created_by').order_by('-created_at'))
        for link in links:
            link.content_admin_url = _content_admin_url(link.content_type, link.object_id)
        context['document'] = document
        context['document_links'] = links
        return context


class DocumentLinkDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk, link_pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        link = get_object_or_404(document.links, pk=link_pk)
        link.delete()
        _audit_document(document, request, 'unlinked', metadata_content_id=link_pk)
        messages.success(request, gettext_lazy('Documento removido deste conteúdo.'))
        return redirect('console:document-usage', pk=document.pk)


class DocumentUnlinkAllView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        count = document.links.count()
        document.links.all().delete()
        _audit_document(document, request, 'unlinked_all', removed_links=count)
        messages.success(request, f'Documento removido de {count} conteúdo(s). Agora ele pode ser arquivado ou excluído.')
        return redirect('console:document-edit', pk=document.pk)


class DocumentApprovalView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        action = request.POST.get('action')
        reviewer = get_tenant_user(request.user)
        if action == 'approve':
            document.status = Document.PUBLISHED
            document.rejection_reason = ''
            document.reviewed_by = reviewer
            document.reviewed_at = timezone.now()
            if not document.published_at:
                document.published_at = timezone.now()
            document.save(update_fields=('status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'published_at', 'updated_at'))
            if document.current_version:
                _announce_change(document, reviewer, document.current_version, is_first=document.current_version.version_number == 1)
            _audit_document(document, request, 'approved')
            message = 'Documento aprovado e publicado.'
        elif action == 'reject':
            document.status = Document.DRAFT
            document.rejection_reason = request.POST.get('rejection_reason', '').strip()[:500]
            document.reviewed_by = reviewer
            document.reviewed_at = timezone.now()
            document.save(update_fields=('status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'))
            _audit_document(document, request, 'rejected', reason=document.rejection_reason)
            message = 'Documento devolvido para ajustes.'
        else:
            message = 'Ação de aprovação não reconhecida.'
        messages.success(request, message)
        return redirect('console:document-edit', pk=document.pk)


class DocumentVersionCreateView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        version = create_version(
            document, request.user, file=request.FILES.get('file'),
            body=request.POST.get('body', ''),
            change_summary=request.POST.get('change_summary', ''),
            expires_at=parse_datetime(request.POST.get('expires_at', '') or '')
                if request.POST.get('expires_at') else None,
        )
        if document.requires_approval and document.status == Document.PUBLISHED:
            document.status = Document.IN_REVIEW
            document.rejection_reason = ''
            document.save(update_fields=('status', 'rejection_reason', 'updated_at'))
        _audit_document(document, request, 'new_version', version=version)
        return redirect('console:document-edit', pk=document.pk)


class DocumentGeneratePdfView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.select_related('current_version'), write=True), pk=pk)
        version = document.current_version
        can_render_html = bool(version and version.has_html_source)
        if not can_render_html:
            messages.error(request, gettext_lazy('Crie ou selecione uma versão com conteúdo editável antes de gerar o PDF.'))
            return redirect('console:document-edit', pk=document.pk)
        try:
            version = generate_document_pdf(version, request.user)
            generate_document_thumbnail(version)
            messages.success(request, gettext_lazy('PDF gerado e associado à versão atual. O conteúdo editável foi preservado.'))
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('console:document-edit', pk=document.pk)


class DocumentVersionCompareView(ManagerRequiredMixin, View):
    template_name = 'console/document_version_compare.html'

    def get(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.prefetch_related('versions'), write=True), pk=pk)
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
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        archive_document(document, request.user)
        _audit_document(document, request, 'archived')
        return redirect('console:document-edit', pk=document.pk)


class DocumentDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        usage_count = document.links.count()
        if usage_count:
            messages.error(request, f'Este documento não pode ser excluído porque está vinculado a {usage_count} conteúdo(s). Arquive-o ou remova os vínculos primeiro.')
            return redirect('console:document-edit', pk=document.pk)
        document.delete()
        messages.success(request, gettext_lazy('Documento excluído definitivamente.'))
        return redirect('console:document-list')


class DocumentShareLinkCreateView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        try:
            days = min(365, max(1, int(request.POST.get('days', '7'))))
        except (TypeError, ValueError):
            days = 7
        link = DocumentShareLink.objects.create(
            document=document, created_by=get_tenant_user(request.user), expires_at=timezone.now() + timedelta(days=days),
        )
        _audit_document(document, request, 'shared', expires_at=link.expires_at.isoformat())
        messages.success(request, f'Link temporário criado e válido por {days} dia(s).')
        return redirect('console:document-edit', pk=document.pk)


class DocumentShareLinkRevokeView(ManagerRequiredMixin, View):
    def post(self, request, pk, link_pk):
        document = get_object_or_404(active_content_queryset(request, Document.objects.all(), write=True), pk=pk)
        link = get_object_or_404(document.share_links, pk=link_pk, active=True)
        link.active = False
        link.save(update_fields=('active',))
        _audit_document(document, request, 'share_revoked', link_id=link.pk)
        return redirect('console:document-edit', pk=document.pk)


class DocumentBulkActionView(ManagerRequiredMixin, View):
    def post(self, request):
        documents = active_content_queryset(request, Document.objects.all(), write=True).filter(pk__in=request.POST.getlist('document_ids'))
        action = request.POST.get('action')
        if action == 'archive':
            for document in documents:
                archive_document(document, request.user)
                _audit_document(document, request, 'archived_bulk')
            messages.success(request, gettext_lazy('Documentos selecionados arquivados. O histórico de versões foi preservado.'))
        elif action == 'delete':
            blocked = list(documents.filter(links__isnull=False).distinct())
            deletable = documents.exclude(links__isnull=False).distinct()
            count = deletable.count()
            for document in deletable:
                document.delete()
            message = f'{count} documento(s) excluído(s) definitivamente.'
            if blocked:
                message += f' {len(blocked)} documento(s) não foram excluídos porque ainda possuem vínculos; use arquivamento.'
            messages.success(request, message)
        return redirect('console:document-list')


class ContentAuditConsoleView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/content_audit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        media = active_organization_queryset(
            self.request, MediaAssetAuditEvent.objects.select_related('asset', 'actor', 'organization')
        )
        company_id = active_company_id(self.request)
        if company_id:
            media = media.filter(asset__company_id__in=(company_id, None))
        documents = DocumentEvent.objects.filter(event_name=DocumentEvent.MANAGED).select_related('document', 'version', 'user')
        organization = getattr(self.request, 'active_organization', None)
        organization_id = getattr(organization, 'pk', None) or getattr(self.request.user, '_active_organization_id', None)
        if organization_id:
            documents = documents.filter(document__organization_id=organization_id)
        if company_id:
            documents = documents.filter(document__company_id__in=(company_id, None))
        if query:
            media = media.filter(asset__title__icontains=query)
            documents = documents.filter(document__title__icontains=query)
        context['media_events'] = media.order_by('-occurred_at')[:100]
        context['document_events'] = documents.order_by('-occurred_at')[:100]
        return context


class MediaMetricsConsoleView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/media_metrics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scoped_assets = active_content_queryset(self.request, MediaAsset.objects.all())
        assets = scoped_assets.annotate(
            usage_total=Count('usages', distinct=True)
        )
        context['metrics'] = scoped_assets.aggregate(
            total=Count('pk'), storage=Sum('file_size'), accesses=Sum('access_count'), links=Count('usages', distinct=True),
        )
        context['most_accessed'] = assets.order_by('-access_count', '-updated_at')[:10]
        context['most_linked'] = assets.order_by('-usage_total', '-updated_at')[:10]
        context['never_accessed'] = assets.filter(access_count=0).order_by('-updated_at')[:10]
        context['expiring'] = assets.filter(valid_until__isnull=False).order_by('valid_until')[:10]
        context['retention_due'] = assets.filter(retention_until__isnull=False).order_by('retention_until')[:10]
        return context


class DocumentPickerView(ManagerRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        documents = active_content_queryset(request, Document.objects.filter(status=Document.PUBLISHED))
        if query:
            documents = documents.filter(title__icontains=query) | documents.filter(code__icontains=query)
        return JsonResponse({'items': [
            {'id': item.pk, 'title': item.title, 'code': item.code,
             'url': reverse('document-detail', kwargs={'slug': item.slug})}
            for item in documents.order_by('title')[:100]
        ]})


class MediaAssetConsoleListView(ManagerRequiredMixin, ListView):
    model = MediaAsset
    template_name = 'console/media_list.html'
    context_object_name = 'assets'

    def get_queryset(self):
        assets = active_content_queryset(self.request, MediaAsset.objects.all())
        query = self.request.GET.get('q', '').strip()
        kind = self.request.GET.get('kind', '').strip()
        collection = self.request.GET.get('collection', '').strip()
        tag = self.request.GET.get('tag', '').strip()
        sort = self.request.GET.get('sort', 'updated').strip()
        workflow_status = self.request.GET.get('workflow_status', '').strip()
        if query:
            assets = assets.filter(title__icontains=query)
        if kind in dict(MediaAsset.KIND_CHOICES):
            assets = assets.filter(kind=kind)
        if collection.isdigit():
            assets = assets.filter(collection_id=collection)
        if tag.isdigit():
            assets = assets.filter(tags__pk=tag)
        if workflow_status in dict(MediaAsset.WORKFLOW_CHOICES):
            assets = assets.filter(workflow_status=workflow_status)
        sort_fields = {
            'name': 'title',
            'size': '-file_size',
            'access': '-access_count',
            'last_access': '-last_accessed_at',
            'updated': '-updated_at',
        }
        return assets.select_related('owner', 'organization', 'collection', 'company', 'audience_policy').annotate(
            usage_count=Count('usages', distinct=True)
        ).order_by(sort_fields.get(sort, '-updated_at')).prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scoped_assets = active_content_queryset(self.request, MediaAsset.objects.all())
        metrics = scoped_assets.aggregate(total_size=Sum('file_size'), total_count=Count('pk'))
        context['media_metrics'] = metrics
        context['orphan_count'] = scoped_assets.filter(usages__isnull=True).distinct().count()
        tenant_user = get_tenant_user(self.request.user)
        context['favorite_ids'] = set()
        context['favorite_assets'] = []
        context['recent_assets'] = []
        if tenant_user:
            states = MediaAssetUserState.objects.filter(user=tenant_user, favorite=True, asset__in=scoped_assets).values_list('asset_id', flat=True)
            context['favorite_ids'] = set(states)
            context['favorite_assets'] = list(scoped_assets.filter(pk__in=context['favorite_ids'], active=True).order_by('title')[:8])
            recent_states = MediaAssetUserState.objects.filter(user=tenant_user, asset=OuterRef('pk'), last_opened_at__isnull=False).order_by('-last_opened_at')
            context['recent_assets'] = list(
                scoped_assets.filter(active=True, user_states__user=tenant_user, user_states__last_opened_at__isnull=False)
                .annotate(recent_opened_at=Subquery(recent_states.values('last_opened_at')[:1]))
                .order_by('-recent_opened_at')[:8]
            )
        context['collections'] = active_organization_queryset(self.request, MediaCollection.objects.filter(active=True)).order_by('name')
        context['available_tags'] = active_organization_queryset(self.request, MediaTag.objects.all()).order_by('name')
        context['content_companies'] = content_company_queryset(self.request)
        context['active_company_id'] = active_company_id(self.request)
        return context


class MediaAssetConsoleCreateView(ManagerRequiredMixin, CreateView):
    model = MediaAsset
    form_class = MediaAssetForm
    template_name = 'console/media_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['active_organization'] = getattr(self.request, 'active_organization', None)
        kwargs['company_queryset'] = content_company_queryset(self.request)
        kwargs['default_company_id'] = active_company_id(self.request)
        kwargs['company_required'] = bool(getattr(getattr(self.request, 'active_membership', None), 'company_id', None))
        return kwargs

    def form_valid(self, form):
        form.instance.owner = get_tenant_user(self.request.user)
        form.instance.organization = get_tenant_organization(getattr(self.request, 'active_organization', None))
        if form.cleaned_data.get('requires_approval'):
            form.instance.workflow_status = 'review'
        response = super().form_valid(form)
        generate_media_derivatives(self.object)
        _audit_media(self.object, self.request, MediaAssetAuditEvent.UPLOADED, public_access=self.object.public_access)
        return response

    def get_success_url(self):
        return reverse('console:media-list')


class MediaAssetConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = MediaAsset
    form_class = MediaAssetForm
    template_name = 'console/media_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['active_organization'] = getattr(self.request, 'active_organization', None)
        kwargs['company_queryset'] = content_company_queryset(self.request)
        kwargs['default_company_id'] = active_company_id(self.request)
        kwargs['company_required'] = bool(getattr(getattr(self.request, 'active_membership', None), 'company_id', None))
        return kwargs

    def get_queryset(self):
        return active_content_queryset(self.request, MediaAsset.objects.all(), write=True)

    def form_valid(self, form):
        previous_public = self.object.public_access
        previous_file = self.object.file.name if self.object.file else ''
        if form.cleaned_data.get('requires_approval') and self.object.workflow_status == 'published':
            form.instance.workflow_status = 'review'
        response = super().form_valid(form)
        generate_media_derivatives(self.object)
        event = MediaAssetAuditEvent.REPLACED if form.cleaned_data.get('file') and previous_file != self.object.file.name else (
            MediaAssetAuditEvent.PUBLICATED if previous_public != self.object.public_access else MediaAssetAuditEvent.UPDATED
        )
        _audit_media(self.object, self.request, event, public_access_changed=previous_public != self.object.public_access)
        return response

    def get_success_url(self):
        return reverse('console:media-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['media_versions'] = self.object.versions.select_related('created_by').all()
        context['media_usages'] = list(self.object.usages.select_related('content_type', 'created_by').order_by('-last_seen_at'))
        for usage in context['media_usages']:
            usage.content_admin_url = _content_admin_url(usage.content_type, usage.object_id)
        context['media_usage_count'] = len(context['media_usages'])
        context['media_share_links'] = self.object.share_links.filter(active=True, expires_at__gt=timezone.now())
        tenant_user = get_tenant_user(self.request.user)
        context['media_is_favorite'] = bool(tenant_user and MediaAssetUserState.objects.filter(asset=self.object, user=tenant_user, favorite=True).exists())
        return context


class MediaAssetDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        if request.POST.get('action') == 'archive':
            asset.active = False
            asset.workflow_status = 'archived'
            asset.save(update_fields=('active', 'workflow_status', 'updated_at'))
            _audit_media(asset, request, MediaAssetAuditEvent.UPDATED, action='archived_from_console')
            messages.success(request, gettext_lazy('Mídia arquivada. Os conteúdos antigos continuam protegidos contra links quebrados.'))
            return redirect('console:media-list')
        usage_count = asset.usages.count()
        if usage_count:
            _audit_media(asset, request, MediaAssetAuditEvent.UPDATED, deletion_blocked=True, usage_count=usage_count)
            messages.error(request, f'Esta mídia não pode ser excluída porque está vinculada a {usage_count} conteúdo(s). Arquive-a ou remova os vínculos primeiro.')
            return redirect('console:media-edit', pk=asset.pk)
        _audit_media(asset, request, MediaAssetAuditEvent.DELETED, individual=True)
        asset.delete()
        messages.success(request, gettext_lazy('Mídia excluída da biblioteca.'))
        return redirect('console:media-list')


class MediaAssetVersionRestoreView(ManagerRequiredMixin, View):
    def post(self, request, pk, version_pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        version = get_object_or_404(asset.versions, pk=version_pk)
        if not version.file:
            return redirect('console:media-edit', pk=asset.pk)
        old_file = asset.file
        with version.file.open('rb') as stream:
            asset.file.save(f'{asset.pk}-restored-v{version.version_number}-{os.path.basename(version.file.name)}', ContentFile(stream.read()), save=False)
        asset.mime_type = version.mime_type
        asset.file_size = version.file_size
        asset.checksum = version.checksum
        asset.save(update_fields=('file', 'mime_type', 'file_size', 'checksum', 'updated_at'))
        generate_media_derivatives(asset)
        if old_file:
            old_file.delete(save=False)
        _audit_media(asset, request, MediaAssetAuditEvent.REPLACED, restored_version=version.version_number)
        return redirect('console:media-edit', pk=asset.pk)


class MediaAssetUsageConsoleView(ManagerRequiredMixin, TemplateView):
    template_name = 'console/media_usage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = get_object_or_404(active_content_queryset(self.request, MediaAsset.objects.all(), write=True), pk=self.kwargs['pk'])
        context['asset'] = asset
        usages = list(asset.usages.select_related('content_type', 'created_by').order_by('-last_seen_at'))
        for usage in usages:
            usage.content_admin_url = _content_admin_url(usage.content_type, usage.object_id)
        context['usages'] = usages
        return context


class MediaAssetUsageDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk, usage_pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        usage = get_object_or_404(asset.usages.select_related('content_type'), pk=usage_pk)
        content_object = usage.content_object
        if content_object is not None:
            field_name = usage.field_name
            current_html = getattr(content_object, field_name, '') or ''
            cleaned_html = remove_media_reference(current_html, asset)
            setattr(content_object, field_name, cleaned_html)
            content_object.save(update_fields=[field_name])
            sync_media_usage(content_object, cleaned_html, actor=request.user, field_name=field_name)
        else:
            usage.delete()
        _audit_media(asset, request, MediaAssetAuditEvent.UPDATED, usage_removed=usage_pk)
        messages.success(request, gettext_lazy('A mídia foi removida deste conteúdo. O arquivo continua na biblioteca.'))
        return redirect('console:media-usage', pk=asset.pk)


class MediaAssetFavoriteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        user = get_tenant_user(request.user)
        state, _ = MediaAssetUserState.objects.get_or_create(asset=asset, user=user)
        state.favorite = not state.favorite
        state.save(update_fields=('favorite', 'updated_at'))
        return redirect(request.POST.get('next') or reverse('console:media-edit', kwargs={'pk': asset.pk}))


class MediaAssetShareLinkCreateView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        try:
            days = min(365, max(1, int(request.POST.get('days', '7'))))
        except (TypeError, ValueError):
            days = 7
        link = MediaAssetShareLink.objects.create(
            asset=asset, created_by=get_tenant_user(request.user), expires_at=timezone.now() + timedelta(days=days),
        )
        _audit_media(asset, request, MediaAssetAuditEvent.SHARED, expires_at=link.expires_at.isoformat())
        messages.success(request, f'Link temporário criado e válido por {days} dia(s).')
        return redirect('console:media-edit', pk=asset.pk)


class MediaAssetShareLinkRevokeView(ManagerRequiredMixin, View):
    def post(self, request, pk, link_pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        link = get_object_or_404(asset.share_links, pk=link_pk, active=True)
        link.active = False
        link.save(update_fields=('active',))
        _audit_media(asset, request, MediaAssetAuditEvent.UPDATED, share_link_revoked=True, link_id=link.pk)
        return redirect('console:media-edit', pk=asset.pk)


class MediaAssetApprovalView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(active_content_queryset(request, MediaAsset.objects.all(), write=True), pk=pk)
        action = request.POST.get('action')
        if action == 'approve':
            asset.workflow_status = 'published'
            asset.rejection_reason = ''
            asset.approved_by = get_tenant_user(request.user)
            asset.approved_at = timezone.now()
            asset.save(update_fields=('workflow_status', 'rejection_reason', 'approved_by', 'approved_at', 'updated_at'))
            _audit_media(asset, request, MediaAssetAuditEvent.PUBLICATED, workflow_status='published')
            message = 'Mídia aprovada e publicada.'
        elif action == 'reject':
            asset.workflow_status = 'draft'
            asset.rejection_reason = request.POST.get('rejection_reason', '').strip()[:500]
            asset.save(update_fields=('workflow_status', 'rejection_reason', 'updated_at'))
            _audit_media(asset, request, MediaAssetAuditEvent.UPDATED, workflow_status='draft', rejection_reason=asset.rejection_reason)
            message = 'Mídia devolvida para ajustes.'
        else:
            message = 'Ação de aprovação não reconhecida.'
        messages.success(request, message)
        return redirect('console:media-edit', pk=asset.pk)


class MediaBulkUploadView(ManagerRequiredMixin, View):
    template_name = 'console/media_bulk_upload.html'

    def get_form(self, data=None, files=None):
        return MediaBulkUploadForm(
            data=data, files=files,
            active_organization=getattr(self.request, 'active_organization', None),
            company_queryset=content_company_queryset(self.request),
            default_company_id=active_company_id(self.request),
            company_required=bool(getattr(getattr(self.request, 'active_membership', None), 'company_id', None)),
        )

    def get(self, request):
        return render(request, self.template_name, {'form': self.get_form()})

    def post(self, request):
        form = self.get_form(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        organization = get_tenant_organization(getattr(request, 'active_organization', None))
        owner = get_tenant_user(request.user)
        tag_names = [name.strip() for name in form.cleaned_data['tags'].split(',') if name.strip()]
        tags = []
        for name in tag_names:
            tag, _ = MediaTag.objects.get_or_create(organization=organization, name=name)
            tags.append(tag)
        created = 0
        skipped = []
        for uploaded in form.cleaned_data['files']:
            digest = hashlib.sha256()
            current_position = uploaded.tell() if hasattr(uploaded, 'tell') else 0
            uploaded.seek(0)
            for chunk in uploaded.chunks():
                digest.update(chunk)
            uploaded.seek(current_position)
            if MediaAsset.objects.filter(organization=organization, checksum=digest.hexdigest()).exists():
                skipped.append(uploaded.name)
                continue
            asset = MediaAsset.objects.create(
                organization=organization, owner=owner, title=uploaded.name,
                kind=form.cleaned_data['kind'], file=uploaded,
                company=form.cleaned_data.get('company'), audience_policy=form.cleaned_data.get('audience_policy'),
                collection=form.cleaned_data.get('collection'), description=form.cleaned_data['description'],
                alt_text=form.cleaned_data.get('alt_text', '') if form.cleaned_data['kind'] == MediaAsset.IMAGE else '',
                public_access=form.cleaned_data.get('public_access', False),
            )
            asset.tags.set(tags)
            generate_media_derivatives(asset)
            try:
                with asset.file.open('rb') as stream:
                    snapshot = stream.read()
                version = MediaAssetVersion(asset=asset, version_number=1, mime_type=asset.mime_type, file_size=len(snapshot), checksum=asset.checksum, created_by=owner)
                version.file.save(f'{asset.pk}-v1-{os.path.basename(asset.file.name)}', ContentFile(snapshot), save=False)
                version.save()
            except (FileNotFoundError, OSError, ValueError):
                pass
            _audit_media(asset, request, MediaAssetAuditEvent.UPLOADED, bulk=True, public_access=asset.public_access)
            created += 1
        messages.success(request, f'{created} mídia(s) adicionada(s) à biblioteca.')
        if skipped:
            messages.warning(request, f'{len(skipped)} arquivo(s) ignorado(s) por duplicidade: {", ".join(skipped[:5])}.')
        return redirect('console:media-list')


class MediaCollectionCreateView(ManagerRequiredMixin, CreateView):
    model = MediaCollection
    form_class = MediaCollectionForm
    template_name = 'console/media_collection_form.html'

    def form_valid(self, form):
        form.instance.organization = get_tenant_organization(getattr(self.request, 'active_organization', None))
        form.instance.owner = get_tenant_user(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('console:media-list')


class MediaCollectionConsoleListView(ManagerRequiredMixin, ListView):
    model = MediaCollection
    template_name = 'console/media_collection_list.html'
    context_object_name = 'collections'

    def get_queryset(self):
        return active_organization_queryset(self.request, MediaCollection.objects.all()).annotate(
            asset_count=Count('assets')
        ).order_by('name')


class MediaCollectionConsoleUpdateView(ManagerRequiredMixin, UpdateView):
    model = MediaCollection
    form_class = MediaCollectionForm
    template_name = 'console/media_collection_form.html'

    def get_queryset(self):
        return active_organization_queryset(self.request, MediaCollection.objects.all())

    def get_success_url(self):
        return reverse('console:media-collection-list')


class MediaAssetPickerView(ManagerRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        kind = request.GET.get('kind', '').strip()
        assets = active_organization_queryset(request, MediaAsset.objects.filter(active=True, workflow_status__in=('approved', 'published'))).exclude(valid_until__lte=timezone.now())
        if query:
            assets = assets.filter(title__icontains=query)
        if kind in dict(MediaAsset.KIND_CHOICES):
            assets = assets.filter(kind=kind)
        return JsonResponse({'items': [
            {'id': item.pk, 'title': item.title, 'kind': item.kind,
             'alt_text': item.alt_text, 'url': item.url}
            for item in assets.order_by('title')[:100] if item.url
        ]})


class MediaBulkActionView(ManagerRequiredMixin, View):
    def post(self, request):
        assets = active_organization_queryset(request, MediaAsset.objects.all()).filter(pk__in=request.POST.getlist('asset_ids'))
        action = request.POST.get('action')
        if action == 'delete':
            blocked = list(assets.filter(usages__isnull=False).distinct())
            deletable = assets.exclude(usages__isnull=False).distinct()
            count = deletable.count()
            for asset in blocked:
                _audit_media(
                    asset,
                    request,
                    MediaAssetAuditEvent.UPDATED,
                    deletion_blocked=True,
                    usage_count=asset.usages.count(),
                    bulk=True,
                )
            for asset in deletable:
                _audit_media(asset, request, MediaAssetAuditEvent.DELETED, bulk=True)
                asset.delete()
            message = f'{count} mídia(s) removida(s).'
            if blocked:
                message += f' {len(blocked)} mídia(s) não foram removidas porque ainda estão vinculadas a conteúdos.'
        elif action in ('activate', 'deactivate'):
            count = assets.update(active=(action == 'activate'))
            message = f'{count} mídia(s) atualizada(s).'
        elif action in ('set_collection', 'clear_collection'):
            collection = None
            if action == 'set_collection':
                collection = get_object_or_404(
                    active_organization_queryset(request, MediaCollection.objects.filter(active=True)),
                    pk=request.POST.get('collection_id'),
                )
            count = assets.update(collection=collection)
            for asset in assets:
                _audit_media(asset, request, MediaAssetAuditEvent.MOVED, collection_id=collection.pk if collection else None, bulk=True)
            message = f'{count} mídia(s) movida(s) para a coleção selecionada.' if collection else f'{count} mídia(s) removida(s) da coleção.'
        elif action in ('add_tags', 'replace_tags'):
            organization = get_tenant_organization(getattr(request, 'active_organization', None))
            names = [item.strip() for item in request.POST.get('tags', '').split(',') if item.strip()]
            tags = [MediaTag.objects.get_or_create(organization=organization, name=name)[0] for name in names]
            for asset in assets:
                if action == 'replace_tags':
                    asset.tags.set(tags)
                else:
                    asset.tags.add(*tags)
                _audit_media(asset, request, MediaAssetAuditEvent.TAGGED, tags=names, bulk=True)
            count = assets.count()
            message = f'Tags atualizadas em {count} mídia(s).'
        else:
            message = 'Nenhuma ação reconhecida.'
        messages.success(request, message)
        return redirect('console:media-list')


class MediaCollectionDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        collection = get_object_or_404(active_organization_queryset(request, MediaCollection.objects.all()), pk=pk)
        collection.assets.update(collection=None)
        collection.delete()
        messages.success(request, gettext_lazy('Coleção removida. As mídias foram preservadas sem coleção.'))
        return redirect('console:media-collection-list')
