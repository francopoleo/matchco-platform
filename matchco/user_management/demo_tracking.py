from django.utils import timezone

from .models import DemoVisit


def track_demo_request(request):
    if not getattr(request.user, 'is_demo', False):
        return
    visit_id = request.session.get('demo_visit_id')
    if not visit_id:
        return
    visit = DemoVisit.objects.filter(pk=visit_id, demo_user=request.user).first()
    if not visit:
        return
    now = timezone.now()
    visit.last_seen_at = now
    visit.duration_seconds = max(0, int((now - visit.started_at).total_seconds()))
    visit.page_views += 1
    visit.last_path = request.path[:500]
    visit.save(update_fields=['last_seen_at', 'duration_seconds', 'page_views', 'last_path'])
