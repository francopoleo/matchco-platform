from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from courses.models import Course
from documents.models import Document, DocumentEvent, DocumentVersion
from documents.services import archive_document, can_access_company_scope, can_download, can_view, create_version, record_view
from learning.models import BadgeDefinition, ChallengeProgress, ContentEvent, PointLedger, UserBadge, UserNotification
from learning.services import track_event
from publishing.models import Publication
from configuration.models import Company, IntegrationCredential, Partner, PartnerMembership
from audience.models import AudiencePolicy
from configuration.services import service_enabled
from .api_auth import IntegrationAPIKeyAuthentication
from matchco.core.utils import get_tenant_user, get_tenant_organization


PARTNER_AUTHENTICATION = (IntegrationAPIKeyAuthentication, SessionAuthentication, JWTAuthentication)


def _manager(user):
    return user.is_superuser or user.is_staff or user.groups.filter(
        name__in=('content_manager', 'audience_manager'),
    ).exists()


def _scope_allowed(request, scope):
    credential = getattr(request, 'integration_credential', None)
    return credential is None or credential.allows(scope)


def _active_organization(request):
    # API keys are commonly used without a browser session. In that case the
    # credential's tenant is the authoritative organization boundary.
    return getattr(request, 'active_organization', None) or getattr(
        getattr(request, 'integration_credential', None), 'organization', None,
    )


def _service_enabled_for_request(request, service_code):
    """Resolve the service entitlement in the active organization/company."""
    organization = _active_organization(request)
    if organization is None:
        return False
    session = getattr(request, 'session', None)
    company_id = getattr(request, 'active_company_id', None)
    if not company_id and session is not None:
        company_id = session.get('active_company_id')
    company = None
    if company_id:
        company = Company.objects.filter(
            pk=company_id, organization_id=organization.pk,
        ).first()
        if company is None:
            return False
    return service_enabled(organization, service_code, company=company)


def _document_payload(request, document):
    version = document.current_version
    return {
        'id': document.pk,
        'title': document.title,
        'slug': document.slug,
        'code': document.code,
        'category': document.category,
        'description': document.description,
        'audience_policy_id': document.audience_policy_id,
        'status': document.status,
        'updated_at': document.updated_at,
        'version': {
            'id': version.pk,
            'number': version.version_number,
            'mime_type': version.mime_type,
            'file_size': version.file_size,
            'effective_at': version.effective_at,
            'expires_at': version.expires_at,
            'url': request.build_absolute_uri(version.file.url) if version and version.file else None,
        } if version else None,
        'can_download': can_download(request.user, document),
    }


class DocumentCollectionApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def get_queryset(self, request):
        queryset = Document.objects.filter(status=Document.PUBLISHED).select_related('current_version', 'organization')
        organization = _active_organization(request)
        if organization:
            tenant_org = get_tenant_organization(organization)
            if tenant_org:
                queryset = queryset.filter(organization=tenant_org)
        return queryset

    def get(self, request):
        if not _scope_allowed(request, 'documents:read'):
            return Response({'detail': 'A credencial não possui o escopo documents:read.'}, status=status.HTTP_403_FORBIDDEN)
        query = request.query_params.get('q', '').strip()
        queryset = self.get_queryset(request)
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(code__icontains=query)
        return Response([_document_payload(request, item) for item in queryset if can_view(request.user, item)])

    def post(self, request):
        if not _scope_allowed(request, 'documents:write'):
            return Response({'detail': 'A credencial não possui o escopo documents:write.'}, status=status.HTTP_403_FORBIDDEN)
        if not _manager(request.user):
            return Response({'detail': 'Acesso de gestão necessário.'}, status=status.HTTP_403_FORBIDDEN)
        from django.utils.text import slugify

        title = str(request.data.get('title', '')).strip()
        if not title:
            return Response({'detail': 'title é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        slug = str(request.data.get('slug') or slugify(title))
        if Document.objects.filter(slug=slug).exists():
            return Response({'detail': 'slug já existe.'}, status=status.HTTP_409_CONFLICT)
        document = Document.objects.create(
            title=title,
            slug=slug,
            code=str(request.data.get('code', ''))[:80],
            category=str(request.data.get('category', 'other')),
            description=str(request.data.get('description', '')),
            status=Document.PUBLISHED if str(request.data.get('status', 'draft')) == Document.PUBLISHED else Document.DRAFT,
            organization=_active_organization(request),
            owner=request.user,
        )
        policy_id = request.data.get('audience_policy_id')
        if policy_id:
            policy = AudiencePolicy.objects.filter(
                pk=policy_id, organization=_active_organization(request),
            ).first()
            if not policy:
                document.delete()
                return Response({'detail': 'audience_policy_id inválida para a organização ativa.'}, status=status.HTTP_400_BAD_REQUEST)
            document.audience_policy = policy
            document.save(update_fields=('audience_policy',))
        if request.data.get('body') or request.FILES.get('file'):
            expires_at = request.data.get('expires_at')
            create_version(
                document, request.user, file=request.FILES.get('file'),
                body=str(request.data.get('body', '')), change_summary='Versão inicial',
                expires_at=parse_datetime(str(expires_at)) if expires_at else None,
            )
        return Response(_document_payload(request, document), status=status.HTTP_201_CREATED)


class DocumentDetailApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def get_document(self, request, pk):
        queryset = Document.objects.select_related('current_version', 'organization').filter(pk=pk)
        organization = _active_organization(request)
        if organization:
            tenant_org = get_tenant_organization(organization)
            if tenant_org:
                queryset = queryset.filter(organization=tenant_org)
        document = queryset.first()
        if not document or not can_view(request.user, document):
            return None
        return document

    def get(self, request, pk):
        if not _scope_allowed(request, 'documents:read'):
            return Response({'detail': 'A credencial não possui o escopo documents:read.'}, status=status.HTTP_403_FORBIDDEN)
        document = self.get_document(request, pk)
        if not document:
            return Response({'detail': 'Documento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_document_payload(request, document))

    def _update(self, request, pk):
        if not _scope_allowed(request, 'documents:write'):
            return Response({'detail': 'A credencial não possui o escopo documents:write.'}, status=status.HTTP_403_FORBIDDEN)
        if not _manager(request.user):
            return Response({'detail': 'Acesso de gestão necessário.'}, status=status.HTTP_403_FORBIDDEN)
        document = self.get_document(request, pk)
        if not document:
            return Response({'detail': 'Documento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        fields = ('title', 'code', 'description', 'announce_changes')
        for field in fields:
            if field in request.data:
                setattr(document, field, request.data[field])
        if 'category' in request.data and request.data['category'] in dict(Document.CATEGORY_CHOICES):
            document.category = request.data['category']
        if 'audience_policy_id' in request.data:
            policy = AudiencePolicy.objects.filter(
                pk=request.data['audience_policy_id'], organization=document.organization,
            ).first()
            if not policy:
                return Response({'detail': 'audience_policy_id inválida para a organização do documento.'}, status=status.HTTP_400_BAD_REQUEST)
            document.audience_policy = policy
        if request.data.get('status') == Document.PUBLISHED and not document.current_version_id:
            return Response({'detail': 'Um documento publicado precisa ter uma versão.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('status') in dict(Document.STATUS_CHOICES):
            document.status = request.data['status']
        document.save()
        return Response(_document_payload(request, document))

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        if not _scope_allowed(request, 'documents:write'):
            return Response({'detail': 'A credencial não possui o escopo documents:write.'}, status=status.HTTP_403_FORBIDDEN)
        if not _manager(request.user):
            return Response({'detail': 'Acesso de gestão necessário.'}, status=status.HTTP_403_FORBIDDEN)
        document = self.get_document(request, pk)
        if not document:
            return Response({'detail': 'Documento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        archive_document(document, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadsApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def get(self, request, pk):
        if not _scope_allowed(request, 'documents:download'):
            return Response({'detail': 'A credencial não possui o escopo documents:download.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = Document.objects.filter(pk=pk)
        organization = _active_organization(request)
        if organization:
            tenant_org = get_tenant_organization(organization)
            if tenant_org:
                queryset = queryset.filter(organization=tenant_org)
        document = queryset.first()
        if not document or not can_view(request.user, document) or not _manager(request.user):
            return Response({'detail': 'Acesso não autorizado.'}, status=status.HTTP_403_FORBIDDEN)
        events = DocumentEvent.objects.filter(document=document, event_name=DocumentEvent.DOWNLOADED)
        stats = events.aggregate(total=Count('id'), readers=Count('user', distinct=True), last=Sum('active_seconds'))
        return Response({'document': document.pk, 'downloads': stats['total'] or 0, 'readers': stats['readers'] or 0, 'active_seconds': stats['last'] or 0})


class DocumentVersionApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def post(self, request, pk):
        if not _scope_allowed(request, 'documents:write'):
            return Response({'detail': 'A credencial não possui o escopo documents:write.'}, status=status.HTTP_403_FORBIDDEN)
        if not _manager(request.user):
            return Response({'detail': 'Acesso de gestão necessário.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = Document.objects.filter(pk=pk)
        organization = _active_organization(request)
        if organization:
            tenant_org = get_tenant_organization(organization)
            if tenant_org:
                queryset = queryset.filter(organization=tenant_org)
        document = queryset.first()
        if not document:
            return Response({'detail': 'Documento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        expires_at = request.data.get('expires_at')
        version = create_version(
            document, request.user, file=request.FILES.get('file'),
            body=str(request.data.get('body', '')),
            change_summary=str(request.data.get('change_summary', '')),
            expires_at=parse_datetime(str(expires_at)) if expires_at else None,
        )
        return Response({'id': version.pk, 'number': version.version_number, 'document': document.pk}, status=status.HTTP_201_CREATED)


class MobileSyncApiView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        organization = _active_organization(request)
        tenant_user = get_tenant_user(request.user)
        tenant_org = get_tenant_organization(organization) if organization else None
        content_enabled = _service_enabled_for_request(request, 'content')
        training_enabled = _service_enabled_for_request(request, 'training')
        documents = (
            Document.objects.filter(status=Document.PUBLISHED)
            .select_related('current_version', 'organization')
            if content_enabled and tenant_org else Document.objects.none()
        )
        courses = (
            Course.objects.filter(state='published', students=tenant_user)
            .select_related('organization')
            if training_enabled and tenant_user and tenant_org else Course.objects.none()
        )
        if tenant_org:
            documents = documents.filter(organization=tenant_org) if content_enabled else documents
            courses = courses.filter(organization=tenant_org) if training_enabled else courses
        notifications = (
            UserNotification.objects.filter(user=tenant_user, organization=tenant_org)
            if tenant_user and tenant_org else UserNotification.objects.none()
        )
        last_sync = request.query_params.get('last_sync')
        if last_sync:
            try:
                parsed = timezone.datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                notifications = notifications.filter(created_at__gt=parsed)
            except ValueError:
                pass
        return Response({
            'documents': [_document_payload(request, item) for item in documents if can_view(request.user, item)],
            'courses': [{'id': course.pk, 'title': course.title, 'slug': course.slug, 'progress': 0} for course in courses if can_access_company_scope(request.user, course)],
            'notifications': [{'id': item.pk, 'title': item.title, 'message': item.message, 'url': item.url, 'priority': item.priority, 'read': bool(item.read_at), 'created_at': item.created_at} for item in notifications[:100]],
            'sync_complete_at': timezone.now(),
        })


class MobileEventsApiView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        events = request.data.get('events', []) if isinstance(request.data, dict) else []
        if not isinstance(events, list) or len(events) > 200:
            return Response({'detail': 'events deve ser uma lista com no máximo 200 itens.'}, status=status.HTTP_400_BAD_REQUEST)
        if _active_organization(request) is None:
            return Response({'accepted': 0, 'received': len(events)})
        content_enabled = _service_enabled_for_request(request, 'content')
        training_enabled = _service_enabled_for_request(request, 'training')
        accepted = 0
        for payload in events:
            if not isinstance(payload, dict):
                continue
            event_type = str(payload.get('type', ''))
            if event_type in {'document_viewed', 'document_downloaded'} and not content_enabled:
                continue
            if event_type in {
                'course_completed', 'course_started', 'content_opened',
                'content_active', 'video_progress',
            } and not training_enabled:
                continue
            session_id = str(payload.get('session_id', ''))[:80]
            active_seconds = min(300, max(0, int(payload.get('active_seconds', 0) or 0)))
            if event_type in {'document_viewed', 'document_downloaded'}:
                document_queryset = Document.objects.filter(pk=payload.get('document_id'))
                organization = _active_organization(request)
                tenant_org = get_tenant_organization(organization) if organization else None
                if tenant_org:
                    document_queryset = document_queryset.filter(organization=tenant_org)
                else:
                    document_queryset = Document.objects.none()
                document = document_queryset.first()
                if document and can_view(request.user, document):
                    version = document.current_version
                    record_view(request.user, document, version, session_id=session_id, active_seconds=active_seconds, downloaded=event_type.endswith('downloaded'))
                    accepted += 1
                continue
            event_name = {
                'course_completed': ContentEvent.COURSE_COMPLETED,
                'course_started': ContentEvent.COURSE_ENROLLED,
                'content_opened': ContentEvent.CONTENT_OPENED,
                'content_active': ContentEvent.CONTENT_ACTIVE,
                'video_progress': ContentEvent.VIDEO_PROGRESS,
            }.get(event_type)
            if not event_name:
                continue
            obj = None
            if payload.get('course_id'):
                tenant_user = get_tenant_user(request.user)
                if tenant_user:
                    course_queryset = Course.objects.filter(pk=payload['course_id'], students=tenant_user)
                    organization = _active_organization(request)
                    tenant_org = get_tenant_organization(organization) if organization else None
                    obj = course_queryset.filter(organization=tenant_org).first() if tenant_org else None
                    if obj and not can_access_company_scope(request.user, obj):
                        obj = None
            if obj is not None:
                track_event(request.user, event_name, obj, session_id=session_id, active_seconds=active_seconds, progress_percent=payload.get('progress_percent'), metadata={'source': 'mobile', 'client_timestamp': payload.get('timestamp')})
                accepted += 1
        return Response({'accepted': accepted, 'received': len(events)})


class EngagementAnalyticsApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def get(self, request):
        if not _scope_allowed(request, 'analytics:read'):
            return Response({'detail': 'A credencial não possui o escopo analytics:read.'}, status=status.HTTP_403_FORBIDDEN)
        if not _manager(request.user):
            return Response({'detail': 'Acesso de gestão necessário.'}, status=status.HTTP_403_FORBIDDEN)
        days = int(request.query_params.get('days', 30) or 30)
        days = min(365, max(1, days))
        events = ContentEvent.objects.filter(occurred_at__gte=timezone.now() - timedelta(days=days))
        organization = _active_organization(request)
        if organization:
            tenant_org = get_tenant_organization(organization)
            if tenant_org:
                events = events.filter(organization=tenant_org)
        return Response({'period_days': days, 'events': events.count(), 'users': events.values('user_id').distinct().count(), 'active_seconds': events.aggregate(total=Sum('active_seconds'))['total'] or 0, 'by_event': list(events.values('event_name').annotate(total=Count('id')).order_by('-total'))})


class GamificationSummaryApiView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not _scope_allowed(request, 'gamification:read'):
            return Response({'detail': 'A credencial não possui o escopo gamification:read.'}, status=status.HTTP_403_FORBIDDEN)
        tenant_user = get_tenant_user(request.user)
        if not tenant_user:
            return Response({'points': 0, 'recent_points': [], 'badges': [], 'challenges': []})
        total = PointLedger.objects.filter(user=tenant_user).aggregate(total=Sum('points'))['total'] or 0
        badges = UserBadge.objects.filter(user=tenant_user).select_related('badge')
        challenges = ChallengeProgress.objects.filter(user=tenant_user).select_related('challenge').order_by('-updated_at')[:20]
        return Response({
            'points': total,
            'recent_points': list(PointLedger.objects.filter(user=tenant_user).values('points', 'reason', 'created_at').order_by('-created_at')[:20]),
            'badges': [{'code': item.badge.code, 'title': item.badge.title, 'description': item.badge.description, 'awarded_at': item.awarded_at} for item in badges],
            'challenges': [{'title': item.challenge.title, 'points': item.points, 'target_points': item.challenge.target_points, 'completed': bool(item.completed_at)} for item in challenges],
        })


class GamificationLeaderboardApiView(APIView):
    """Return a tenant-scoped, aggregated leaderboard.

    The leaderboard never crosses organization boundaries. API-key requests
    inherit the organization attached to the credential even when there is
    no selected browser session.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def get(self, request):
        if not _scope_allowed(request, 'gamification:read'):
            return Response({'detail': 'A credencial não possui o escopo gamification:read.'}, status=status.HTTP_403_FORBIDDEN)
        organization = _active_organization(request)
        ledger = PointLedger.objects.select_related('user').all()
        if organization:
            tenant_org = get_tenant_organization(organization)
            if tenant_org:
                ledger = ledger.filter(organization=tenant_org)
                ledger = ledger.filter(
                    user__memberships__organization_id=organization.pk,
                    user__memberships__active=True,
                )
        limit = min(100, max(1, int(request.query_params.get('limit', 10) or 10)))
        rows = list(ledger.values('user_id').annotate(points=Sum('points')).order_by('-points', 'user_id')[:limit])
        user_ids = [row['user_id'] for row in rows]
        users = {user.pk: user for user in get_user_model().objects.filter(pk__in=user_ids)}
        leaderboard = []
        for rank, row in enumerate(rows, start=1):
            user = users.get(row['user_id'])
            if not user:
                continue
            leaderboard.append({
                'rank': rank,
                'user_id': user.pk,
                'display_name': user.get_full_name() or user.get_username(),
                'points': row['points'] or 0,
                'is_current_user': user.pk == request.user.pk,
            })
        current = ledger.filter(user_id=request.user.pk).aggregate(points=Sum('points'))['points'] or 0
        return Response({
            'organization_id': organization.pk if organization else None,
            'limit': limit,
            'entries': leaderboard,
            'current_user': {'user_id': request.user.pk, 'points': current},
        })


class IntegrationCredentialApiView(APIView):
    """Tenant manager endpoint; plaintext keys are returned only at issue/rotate time."""
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, JWTAuthentication)

    def _organization(self, request):
        return _active_organization(request)

    def _authorized(self, request):
        return _manager(request.user) and self._organization(request) is not None

    def get(self, request):
        if not self._authorized(request):
            return Response({'detail': 'Acesso de gestão e organização ativa necessários.'}, status=status.HTTP_403_FORBIDDEN)
        credentials = IntegrationCredential.objects.filter(organization=self._organization(request)).order_by('-created_at')
        return Response([{'id': item.pk, 'name': item.name, 'key_prefix': item.key_prefix, 'scopes': item.scopes, 'active': item.active, 'expires_at': item.expires_at, 'last_used_at': item.last_used_at} for item in credentials])

    def post(self, request):
        if not self._authorized(request):
            return Response({'detail': 'Acesso de gestão e organização ativa necessários.'}, status=status.HTTP_403_FORBIDDEN)
        name = str(request.data.get('name', '')).strip()
        if not name:
            return Response({'detail': 'name é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        scopes = request.data.get('scopes', ['documents:read', 'analytics:read'])
        if not isinstance(scopes, list) or not all(isinstance(scope, str) for scope in scopes):
            return Response({'detail': 'scopes deve ser uma lista de textos.'}, status=status.HTTP_400_BAD_REQUEST)
        partner = None
        if request.data.get('partner_id'):
            partner = Partner.objects.filter(
                pk=request.data.get('partner_id'), organization=self._organization(request), status=Partner.ACTIVE,
            ).first()
            if not partner:
                return Response({'detail': 'Parceiro inválido para a organização ativa.'}, status=status.HTTP_400_BAD_REQUEST)
        credential, raw_key = IntegrationCredential.issue(organization=self._organization(request), name=name, created_by=request.user, scopes=scopes)
        if partner:
            credential.partner = partner
            credential.save(update_fields=('partner',))
        return Response({'id': credential.pk, 'name': credential.name, 'partner_id': credential.partner_id, 'key': raw_key, 'scopes': credential.scopes, 'warning': 'Guarde esta chave; ela não será exibida novamente.'}, status=status.HTTP_201_CREATED)


class IntegrationCredentialRotateApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, JWTAuthentication)

    def post(self, request, pk):
        organization = _active_organization(request)
        if not _manager(request.user) or not organization:
            return Response({'detail': 'Acesso de gestão e organização ativa necessários.'}, status=status.HTTP_403_FORBIDDEN)
        credential = IntegrationCredential.objects.filter(pk=pk, organization=organization).first()
        if not credential:
            return Response({'detail': 'Credencial não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        raw_key = credential.rotate()
        return Response({'id': credential.pk, 'key': raw_key, 'warning': 'A chave anterior foi invalidada.'})


class PartnerPortalApiView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = PARTNER_AUTHENTICATION

    def get(self, request):
        if not _scope_allowed(request, 'partner:read'):
            return Response({'detail': 'A credencial não possui o escopo partner:read.'}, status=status.HTTP_403_FORBIDDEN)
        credential = getattr(request, 'integration_credential', None)
        partner_filter = {'partner_id': credential.partner_id} if credential and credential.partner_id else {}
        memberships = PartnerMembership.objects.filter(
            user=request.user, active=True, partner__status=Partner.ACTIVE, **partner_filter,
        ).select_related('partner', 'partner__organization', 'partner__company')
        if not memberships.exists():
            return Response({'detail': 'Nenhum portal de parceiro ativo para este usuário.'}, status=status.HTTP_404_NOT_FOUND)
        result = []
        tenant_user = get_tenant_user(request.user)
        for membership in memberships:
            partner = membership.partner
            tenant_org = get_tenant_organization(partner.organization)
            if tenant_org:
                documents = Document.objects.filter(status=Document.PUBLISHED, organization=tenant_org).select_related('current_version')
                visible_documents = [item for item in documents if can_view(request.user, item)]
                courses = Course.objects.filter(state='published', organization=tenant_org, students=tenant_user) if tenant_user else Course.objects.none()
                courses = [course for course in courses if can_access_company_scope(request.user, course)]
                events = ContentEvent.objects.filter(user=tenant_user, organization=tenant_org) if tenant_user else ContentEvent.objects.none()
            else:
                visible_documents = []
                courses = Course.objects.none()
                events = ContentEvent.objects.none()
            points = 0
            if tenant_user and tenant_org:
                points = PointLedger.objects.filter(user=tenant_user, organization=tenant_org).aggregate(total=Sum('points'))['total'] or 0
            result.append({
                'id': partner.pk,
                'name': partner.name,
                'company': partner.company.name if partner.company else None,
                'role': membership.role,
                'documents': [{'id': item.pk, 'title': item.title, 'version': item.current_version.version_number if item.current_version else None} for item in visible_documents],
                'documents_count': len(visible_documents),
                'courses_completed': events.filter(event_name=ContentEvent.COURSE_COMPLETED).values('object_id').distinct().count() if tenant_user else 0,
                'courses_enrolled': courses.count() if tenant_user else 0,
                'last_activity': events.order_by('-occurred_at').values_list('occurred_at', flat=True).first() if tenant_user else None,
                'points': points,
            })
        return Response({'partners': result})
