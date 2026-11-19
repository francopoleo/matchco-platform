from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View

from .models import ContentEvent, PointLedger, PushSubscription, UserNotification
from .services import track_event
from matchco.core.utils import get_tenant_user


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = 'learning/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        tenant_user = get_tenant_user(self.request.user)
        if not tenant_user:
            return UserNotification.objects.none()
        queryset = UserNotification.objects.filter(user=tenant_user)
        active_organization_id = getattr(self.request.user, '_active_organization_id', None)
        if active_organization_id:
            queryset = queryset.filter(
                Q(organization_id=active_organization_id) | Q(organization__isnull=True)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['notification_total'] = queryset.count()
        context['unread_count'] = queryset.filter(read_at__isnull=True).count()
        context['read_count'] = queryset.filter(read_at__isnull=False).count()
        return context


class NotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tenant_user = get_tenant_user(request.user)
        if not tenant_user:
            from django.http import Http404
            raise Http404
        notifications = UserNotification.objects.filter(pk=pk, user=tenant_user)
        active_organization_id = getattr(request.user, '_active_organization_id', None)
        if active_organization_id:
            notifications = notifications.filter(
                Q(organization_id=active_organization_id) | Q(organization__isnull=True)
            )
        notification = get_object_or_404(notifications)
        from django.utils import timezone
        notification.read_at = timezone.now()
        notification.save(update_fields=('read_at',))
        from .models import NotificationDelivery
        NotificationDelivery.objects.filter(notification=notification, opened_at__isnull=True).update(opened_at=timezone.now())
        return redirect(notification.url or 'notifications')


class NotificationReadAllView(LoginRequiredMixin, View):
    def post(self, request):
        from django.utils import timezone
        tenant_user = get_tenant_user(request.user)
        if tenant_user:
            notifications = UserNotification.objects.filter(user=tenant_user, read_at__isnull=True)
            active_organization_id = getattr(request.user, '_active_organization_id', None)
            if active_organization_id:
                notifications = notifications.filter(
                    Q(organization_id=active_organization_id) | Q(organization__isnull=True)
                )
            notifications.update(read_at=timezone.now())
        return redirect('notifications')


class LeaderboardView(LoginRequiredMixin, ListView):
    template_name = 'learning/leaderboard.html'
    context_object_name = 'entries'

    def get_queryset(self):
        organization_id = getattr(self.request.user, '_active_organization_id', None)
        queryset = PointLedger.objects.select_related('user')
        if organization_id:
            queryset = queryset.filter(
                organization_id=organization_id,
                user__memberships__organization_id=organization_id,
                user__memberships__active=True,
            )
        return list(queryset.values('user_id').annotate(points=Sum('points')).order_by('-points', 'user_id')[:50])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries = context['entries']
        users = {user.pk: user for user in get_user_model().objects.filter(pk__in=[item['user_id'] for item in entries])}
        context['entries'] = [
            {
                **item,
                'rank': index,
                'user': users.get(item['user_id']),
                'is_current_user': item['user_id'] == self.request.user.pk,
            }
            for index, item in enumerate(entries, start=1)
            if users.get(item['user_id'])
        ]
        context['organization_id'] = getattr(self.request.user, '_active_organization_id', None)
        return context


class PushSubscriptionView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            payload = json.loads(request.body or '{}')
            subscription = payload.get('subscription') or {}
            endpoint = subscription.get('endpoint', '').strip()
            keys = subscription.get('keys') or {}
            active = bool(payload.get('active', True))
            if not endpoint:
                raise ValueError('endpoint ausente')
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'Inscrição inválida.'}, status=400)
        organization_id = getattr(request.user, '_active_organization_id', None)
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user, 'organization_id': organization_id, 'keys': keys,
                'active': active, 'user_agent': request.headers.get('User-Agent', '')[:500],
            },
        )
        return JsonResponse({'ok': True, 'active': active})


class OperationalActionEventView(LoginRequiredMixin, View):
    """Provider-neutral endpoint for connecting learning to an operational action."""
    def post(self, request):
        try:
            payload = json.loads(request.body or '{}')
            action_type = str(payload.get('action_type', '')).strip()[:120]
            if not action_type:
                raise ValueError('action_type ausente')
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'Ação inválida.'}, status=400)
        track_event(
            request.user,
            ContentEvent.ACTION_COMPLETED,
            organization=None,
            metadata={
                'action_type': action_type,
                'reference': str(payload.get('reference', ''))[:180],
                'source': str(payload.get('source', ''))[:120],
            },
        )
        return JsonResponse({'ok': True})
