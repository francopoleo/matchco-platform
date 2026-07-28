from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from audience.services import eligibility
from cep.core.utils import get_tenant_user

from .models import Document, DocumentEvent, DocumentPermission, DocumentVersion, DocumentView


def _tenant_actor(user):
    return get_tenant_user(user)


def _auth_actor(user):
    return getattr(user, 'user', user)


def can_view(user, document):
    if not document.is_available:
        return False
    tenant_user = _tenant_actor(user)
    permission = DocumentPermission.objects.filter(document=document, user=tenant_user).first() if tenant_user else None
    if permission and (not permission.expires_at or permission.expires_at > timezone.now()):
        return permission.can_view
    return eligibility.can_view(_auth_actor(user), document).allowed


def can_download(user, document):
    if not can_view(user, document):
        return False
    tenant_user = _tenant_actor(user)
    permission = DocumentPermission.objects.filter(document=document, user=tenant_user).first() if tenant_user else None
    if permission and (not permission.expires_at or permission.expires_at > timezone.now()):
        return permission.can_download or permission.can_manage
    return True


ALLOWED_UPLOAD_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
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


@transaction.atomic
def create_version(document, user, *, file=None, body='', change_summary='', mime_type='', expires_at=None):
    validate_upload(file)
    user = _tenant_actor(user)
    if not user:
        raise ValidationError('O usuário autenticado não possui cadastro de TenantUser.')
    had_current_version = bool(document.current_version_id)
    last = document.versions.order_by('-version_number').first()
    version = DocumentVersion.objects.create(
        document=document,
        version_number=(last.version_number + 1 if last else 1),
        file=file,
        body=body,
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
    if document.status == Document.PUBLISHED and document.announce_changes:
        _announce_change(document, user, version, archived=False, is_first=not had_current_version)
    return version


def _announce_change(document, user, version, *, archived=False, is_first=False):
    """Publish a controlled Feed notice using the document's own audience."""
    from publishing.models import Publication

    action = 'Novo documento publicado' if is_first else ('Documento arquivado' if archived else 'Documento atualizado')
    suffix = 'archived' if archived else f'v{version.version_number}'
    slug = slugify(f'{document.slug}-{suffix}')[:230]
    if Publication.objects.filter(slug=slug).exists():
        return
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
