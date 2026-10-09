from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
import html as html_lib
import re
import socket
from io import BytesIO
from pathlib import Path

from audience.services import eligibility
from matchco.core.utils import get_tenant_user

from .models import Document, DocumentEvent, DocumentPermission, DocumentVersion, DocumentView, MediaAsset, MediaAssetUsage


def _tenant_actor(user):
    return get_tenant_user(user)


def _auth_actor(user):
    return getattr(user, 'user', user)


def can_access_company_scope(user, content):
    """Keep company-owned content inside its company, even for staff users.

    Organization owners/admins can manage shared company content; a staff flag
    or a content-manager group alone is not a cross-company grant.
    """
    company_id = getattr(content, 'company_id', None)
    if not company_id:
        return True
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    organization_id = getattr(content, 'organization_id', None)
    active_organization_id = getattr(user, '_active_organization_id', None)
    if active_organization_id and organization_id and int(active_organization_id) != int(organization_id):
        return False
    memberships = user.memberships.filter(active=True, organization_id=organization_id)
    direct_access = memberships.filter(company_id=company_id).exists() or memberships.filter(
        company__isnull=True, role__in=('owner', 'admin'),
    ).exists()
    if direct_access:
        return True
    return user.partner_memberships.filter(
        active=True, partner__organization_id=organization_id,
        partner__company_id=company_id,
    ).exists()


def company_scoped_queryset(user, queryset, company_field='company_id', organization_field='organization_id'):
    """Efficient queryset boundary for company-owned content consumption."""
    if not getattr(user, 'is_authenticated', False):
        return queryset.none() if hasattr(queryset, 'none') else []
    if not hasattr(queryset, 'filter'):
        return [item for item in queryset if can_access_company_scope(user, item)]
    if getattr(user, 'is_superuser', False):
        return queryset
    memberships = user.memberships.filter(active=True)
    company_ids = set(memberships.exclude(company_id__isnull=True).values_list('company_id', flat=True))
    admin_organization_ids = set(memberships.filter(
        company__isnull=True, role__in=('owner', 'admin'),
    ).values_list('organization_id', flat=True))
    partner_company_ids = set(user.partner_memberships.filter(
        active=True, partner__company_id__isnull=False,
    ).values_list('partner__company_id', flat=True))
    company_ids.update(partner_company_ids)
    return queryset.filter(
        Q(**{f'{company_field}__isnull': True})
        | Q(**{f'{company_field}__in': company_ids})
        | Q(**{f'{organization_field}__in': admin_organization_ids})
    )


def bump_access_count(instance):
    """Atomically increment access_count and update last_accessed_at."""
    from django.db.models import F
    model_class = instance.__class__
    model_class.objects.filter(pk=instance.pk).update(
        access_count=F('access_count') + 1,
        last_accessed_at=timezone.now()
    )


def _get_active_permission(user, document):
    """Get active DocumentPermission for (user, document) pair or None."""
    tenant_user = _tenant_actor(user)
    if not tenant_user:
        return None
    permission = DocumentPermission.objects.filter(document=document, user=tenant_user).first()
    if permission and (not permission.expires_at or permission.expires_at > timezone.now()):
        return permission
    return None


def can_view(user, document):
    if not document.is_available:
        return False
    if not can_access_company_scope(user, document):
        return False
    permission = _get_active_permission(user, document)
    if permission:
        return permission.can_view
    return eligibility.can_view(_auth_actor(user), document).allowed


def can_download(user, document):
    if not document.is_available:
        return False
    if not can_access_company_scope(user, document):
        return False
    permission = _get_active_permission(user, document)
    if permission:
        return permission.can_download or permission.can_manage
    return eligibility.can_view(_auth_actor(user), document).allowed


def can_view_media(user, asset):
    """Apply organization, optional company and audience rules to a media asset."""
    if not asset.is_published:
        return False
    if not getattr(user, 'is_authenticated', False):
        return False
    active_organization_id = getattr(user, '_active_organization_id', None)
    if active_organization_id and asset.organization_id and int(active_organization_id) != int(asset.organization_id):
        return False
    if not can_access_company_scope(user, asset):
        return False
    return eligibility.can_view(user, asset).allowed


ALLOWED_UPLOAD_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.html', '.htm', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
    '.mp4', '.webm',
}


def validate_upload(file):
    if not file:
        return
    max_bytes = int(getattr(settings, 'DOCUMENT_MAX_UPLOAD_MB', 100)) * 1024 * 1024
    if getattr(file, 'size', 0) > max_bytes:
        raise ValidationError(f'O arquivo excede o limite de {max_bytes // (1024 * 1024)} MB.')
    from pathlib import Path
    extension = Path(getattr(file, 'name', '')).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError('Tipo de arquivo não permitido para documentos enterprise.')
    if extension == '.svg':
        try:
            position = file.tell()
            file.seek(0)
            payload = file.read(max_bytes + 1)
            file.seek(position)
        except (AttributeError, OSError, ValueError):
            payload = b''
        lowered = payload.lower() if isinstance(payload, bytes) else str(payload).lower().encode()
        if b'<script' in lowered or b'javascript:' in lowered or re.search(rb'\bon[a-z]+\s*=', lowered):
            raise ValidationError('SVG com scripts ou eventos embutidos não é permitido.')
    scan_upload_for_malware(file)


def scan_upload_for_malware(file):
    """Scan with ClamAV when configured; fail closed when policy requires it."""
    socket_path = getattr(settings, 'CLAMAV_UNIX_SOCKET', '')
    required = bool(getattr(settings, 'CLAMAV_REQUIRED', False))
    if not socket_path:
        if required:
            raise ValidationError('A verificação antivírus obrigatória não está configurada.')
        return
    try:
        import clamd
        scanner = clamd.ClamdUnixSocket(path=socket_path)
        position = file.tell()
        file.seek(0)
        try:
            result = scanner.instream(file)
        finally:
            file.seek(position)
    except (ImportError, OSError, socket.error, ValueError) as exc:
        if required:
            raise ValidationError('Não foi possível concluir a verificação antivírus.') from exc
        return
    status = (result or {}).get('stream', ('UNKNOWN', ''))[0]
    if status == 'FOUND':
        raise ValidationError('O arquivo foi bloqueado pela verificação antivírus.')
    if status != 'OK' and required:
        raise ValidationError('A verificação antivírus não retornou um resultado seguro.')


def generate_media_derivatives(asset):
    """Create lightweight previews while preserving the uploaded original."""
    if asset.kind != MediaAsset.IMAGE or not asset.file:
        for field in ('preview_file', 'webp_file', 'avif_file'):
            stored = getattr(asset, field, None)
            if stored:
                stored.delete(save=False)
        asset.width = asset.height = 0
        asset.preview_file = asset.webp_file = asset.avif_file = ''
        asset.save(update_fields=('preview_file', 'webp_file', 'avif_file', 'width', 'height', 'updated_at'))
        return False
    try:
        from PIL import Image, ImageOps
        with asset.file.open('rb') as stream:
            image = ImageOps.exif_transpose(Image.open(stream))
            image.load()
        asset.width, asset.height = image.size
        preview = image.copy()
        preview.thumbnail((900, 900), Image.Resampling.LANCZOS)
        if preview.mode not in ('RGB', 'RGBA'):
            preview = preview.convert('RGBA' if 'A' in preview.getbands() else 'RGB')
        base = Path(asset.file.name).stem
        for field, image_format, extension in (
            ('preview_file', 'WEBP', 'webp'),
            ('webp_file', 'WEBP', 'webp'),
            ('avif_file', 'AVIF', 'avif'),
        ):
            buffer = BytesIO()
            preview.save(buffer, format=image_format, quality=84, method=6)
            buffer.seek(0)
            old = getattr(asset, field)
            if old:
                old.delete(save=False)
            getattr(asset, field).save(f'{asset.pk}-{base}.{extension}', ContentFile(buffer.read()), save=False)
        asset.save(update_fields=('preview_file', 'webp_file', 'avif_file', 'width', 'height', 'updated_at'))
        return True
    except (OSError, ValueError, ImportError):
        asset.width = asset.height = 0
        return False


def generate_document_thumbnail(version):
    """Create a first-page/image thumbnail without changing the source file."""
    source = version.generated_pdf or version.file
    if not source and not version.body:
        return False
    mime_type = (version.mime_type or '').lower()
    filename = source.name.lower() if source else ''
    try:
        if version.body and not source:
            from weasyprint import HTML
            from pdf2image import convert_from_bytes
            pages = convert_from_bytes(HTML(string=_version_html(version)).write_pdf(), first_page=1, last_page=1, size=900, fmt='jpeg')
            if not pages:
                return False
            image = pages[0].convert('RGB')
            extension = 'html'
        elif mime_type == 'application/pdf' or filename.endswith('.pdf'):
            from pdf2image import convert_from_bytes
            with source.open('rb') as stream:
                pages = convert_from_bytes(stream.read(), first_page=1, last_page=1, size=900, fmt='jpeg')
            if not pages:
                return False
            image = pages[0].convert('RGB')
            extension = 'pdf'
        elif mime_type.startswith('image/') or filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            from PIL import Image, ImageOps
            with source.open('rb') as stream:
                image = ImageOps.exif_transpose(Image.open(stream))
                image.load()
            image.thumbnail((900, 900), Image.Resampling.LANCZOS)
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            extension = 'image'
        elif mime_type in ('text/html', 'application/xhtml+xml') or filename.endswith(('.html', '.htm')):
            from weasyprint import HTML
            from pdf2image import convert_from_bytes
            with source.open('rb') as stream:
                raw = stream.read()
            pages = convert_from_bytes(HTML(string=raw.decode('utf-8', errors='replace')).write_pdf(), first_page=1, last_page=1, size=900, fmt='jpeg')
            if not pages:
                return False
            image = pages[0].convert('RGB')
            extension = 'html'
        else:
            return False
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=84, optimize=True)
        buffer.seek(0)
        if version.thumbnail_file:
            version.thumbnail_file.delete(save=False)
        version.thumbnail_file.save(f'{version.document_id}-v{version.version_number}-{extension}.jpg', ContentFile(buffer.read()), save=False)
        version.save(update_fields=('thumbnail_file',))
        return True
    except (OSError, ValueError, ImportError):
        return False


def _version_html(version):
    """Return a self-contained HTML document for the current version."""
    if version.body:
        body = version.body
    elif version.file and (version.mime_type or '').lower() in ('text/html', 'application/xhtml+xml'):
        with version.file.open('rb') as stream:
            body = stream.read().decode('utf-8', errors='replace')
    else:
        raise ValidationError('Esta versão não possui conteúdo HTML para gerar um PDF.')
    title = html_lib.escape(version.document.title)
    return '<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:Arial,sans-serif;color:#172033;line-height:1.55;margin:42px}h1{font-size:24px;margin-bottom:22px}img{max-width:100%}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:6px;text-align:left}</style></head><body>' + f'<h1>{title}</h1>{body}</body></html>'


def generate_document_pdf(version, user):
    """Render the current version's HTML into PDF without changing its source."""
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise ValidationError('A geração de PDF não está instalada neste ambiente.') from exc
    html = _version_html(version)
    pdf_bytes = HTML(string=html).write_pdf()
    if version.generated_pdf:
        version.generated_pdf.delete(save=False)
    version.generated_pdf.save(f'{version.document.slug}-v{version.version_number}.pdf', ContentFile(pdf_bytes), save=False)
    version.generated_at = timezone.now()
    version.generated_by = _tenant_actor(user)
    version.save(update_fields=('generated_pdf', 'generated_at', 'generated_by'))
    return version


@transaction.atomic
def create_version(document, user, *, file=None, body='', change_summary='', mime_type='', expires_at=None, source_type='', external_url=''):
    validate_upload(file)
    user = _tenant_actor(user)
    if not user:
        raise ValidationError('O usuário autenticado não possui cadastro de TenantUser.')
    if file:
        source_type = DocumentVersion.SOURCE_UPLOAD
    elif external_url:
        source_type = DocumentVersion.SOURCE_EXTERNAL
    else:
        source_type = source_type or DocumentVersion.SOURCE_RICH_TEXT
    had_current_version = bool(document.current_version_id)
    last = document.versions.order_by('-version_number').first()
    version = DocumentVersion.objects.create(
        document=document,
        version_number=(last.version_number + 1 if last else 1),
        source_type=source_type,
        file=file,
        body=body,
        external_url=external_url,
        change_summary=change_summary,
        mime_type=mime_type,
        created_by=user,
        effective_at=timezone.now(),
        expires_at=expires_at,
    )
    if document.current_version_id:
        document.versions.filter(pk=document.current_version_id, superseded_at__isnull=True).update(superseded_at=timezone.now())
    document.current_version = version
    document.updated_at = timezone.now()
    document.save(update_fields=('current_version', 'updated_at'))
    if file or body:
        generate_document_thumbnail(version)
    if document.status == Document.PUBLISHED and document.announce_changes:
        _announce_change(document, user, version, archived=False, is_first=not had_current_version)
    return version


def _announce_change(document, user, version, *, archived=False, is_first=False):
    """Publish a controlled Feed notice using the document's own audience."""
    from publishing.models import Publication
    from django.db import IntegrityError

    action = 'Novo documento publicado' if is_first else ('Documento arquivado' if archived else 'Documento atualizado')
    suffix = 'archived' if archived else f'v{version.version_number}'
    slug = slugify(f'{document.slug}-{suffix}')[:230]
    try:
        Publication.objects.create(
            kind=Publication.FEED,
            organization=document.organization,
            title=f'{action}: {document.title}',
            slug=slug,
            excerpt=document.description,
            body=version.change_summary or f'{action}: consulte a versão vigente no repositório documental.',
            author=user,
            audience_policy=document.audience_policy,
            status=Publication.PUBLISHED,
            published_at=timezone.now(),
            importance=Publication.IMPORTANT,
            content_category='document_update' if not archived else 'obsolete',
            requires_acknowledgement=not archived,
            reminder_hours=24,
        )
    except IntegrityError:
        pass

    from learning.services import evaluate_notification_rules
    evaluate_notification_rules(
        'document_archived' if archived else ('document_published' if is_first else 'document_updated'),
        document,
        actor=user,
    )
    from learning.integrations import enqueue_webhook_event
    if document.organization:
        enqueue_webhook_event(
            organization=document.organization,
            event_type='document_archived' if archived else ('document_published' if is_first else 'document_updated'),
            payload={'document_id': document.pk, 'version_id': version.pk, 'title': document.title, 'actor_id': user.pk},
        )


@transaction.atomic
def archive_document(document, user):
    user = _tenant_actor(user)
    if not user:
        raise ValidationError('O usuário autenticado não possui cadastro de TenantUser.')
    if document.status == Document.ARCHIVED:
        return document
    document.status = Document.ARCHIVED
    document.archived_at = timezone.now()
    document.save(update_fields=('status', 'archived_at', 'updated_at'))
    if document.announce_changes and document.current_version:
        _announce_change(document, user, document.current_version, archived=True)
    return document


def record_view(user, document, version, *, session_id='', active_seconds=0, downloaded=False):
    if not can_view(user, document):
        return None
    tenant_user = _tenant_actor(user)
    if not tenant_user:
        return None
    view, _ = DocumentView.objects.get_or_create(
        document=document, version=version, user=tenant_user, session_id=session_id[:80],
    )
    if active_seconds:
        view.active_seconds += min(300, max(0, int(active_seconds)))
    if downloaded:
        view.download_count += 1
    view.save(update_fields=('active_seconds', 'download_count', 'last_seen_at'))
    DocumentEvent.objects.create(
        document=document, version=version, user=tenant_user,
        event_name=DocumentEvent.DOWNLOADED if downloaded else (DocumentEvent.ACTIVE if active_seconds else DocumentEvent.OPENED),
        active_seconds=min(300, max(0, int(active_seconds or 0))),
        metadata={'session_id': session_id[:80]},
    )
    return view


def sync_media_usage(content_object, html, *, actor=None, field_name='content'):
    """Rebuild usage links from protected media URLs embedded in rich content."""
    if not content_object or not getattr(content_object, 'pk', None):
        return 0
    content_type = ContentType.objects.get_for_model(content_object)
    rich_html = html or ''
    asset_ids = {int(value) for value in re.findall(r'/documents/media/(\d+)(?:/|"|\')', rich_html)}
    legacy_paths = {
        f'media-library/{value}'
        for value in re.findall(r'/(?:media/)?media-library/([^"\'\s)]+)', rich_html)
    }
    MediaAssetUsage.objects.filter(content_type=content_type, object_id=content_object.pk, field_name=field_name).delete()
    assets = MediaAsset.objects.filter(Q(pk__in=asset_ids) | Q(file__in=legacy_paths)).distinct()
    actor = get_tenant_user(actor) if actor else None
    MediaAssetUsage.objects.bulk_create([
        MediaAssetUsage(asset=asset, content_type=content_type, object_id=content_object.pk, field_name=field_name, created_by=actor)
        for asset in assets
    ], ignore_conflicts=True)
    return assets.count()


def remove_media_reference(html, asset):
    """Remove a media embed from rich HTML while leaving the rest untouched."""
    content = html or ''
    patterns = [
        rf'<[^>]*(?:/documents/media/{asset.pk}/|/documents/media/{asset.pk}/[^"\'\s>]*)[^>]*>',
    ]
    if asset.file:
        filename = re.escape(asset.file.name)
        patterns.append(rf'<[^>]*{filename}[^>]*>')
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
    content = content.replace(f'/documents/media/{asset.pk}/', '')
    return content
