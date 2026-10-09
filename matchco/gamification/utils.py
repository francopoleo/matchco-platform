from django.apps import apps

from .models import GamificationSettings, GamificationReport
from matchco.core.utils import get_tenant_user
from user_management.models import User


def create_gamification_report_item(user, event, object_source=None):
    tenant_user = get_tenant_user(user)
    if not tenant_user:
        return None
    points = get_event_points(event, object=object_source)

    if points is not False:
        if object_source:
            gs = GamificationReport(
                    user=tenant_user, points=points, type_event=event, model_name=object_source.__class__.__name__, id_source=object_source.id)
        else:
            gs = GamificationReport(user=tenant_user, points=points, type_event=event)
        
        gs.save()

        public_user = User.objects.filter(pk=tenant_user.user_id).first()
        if public_user:
            public_user.update_award_points(points)

def get_event_points(event, object=None):
    settings = GamificationSettings.objects.filter(pk=1).first()
    # Gamification is optional; missing configuration must not block learning.
    if settings is None:
        return False
    if not object:
        object = settings

    events = {
        'login': ('ap_first_login', 'dp_first_login'),
        'post_view': ('ap_feed_post_view', 'points_per_view'),
        'course_enrollment': ('ap_course_enrollment', 'points_per_enrollment'),
        'course_completation': ('ap_course_completation', 'points_per_completation'),
        'passed_tests': ('ap_passed_tests', 'points_per_approval'),
    }
    settings = settings.__dict__
    is_active = settings.get(events[event][0])
    if is_active is True:
        return object.__dict__.get(events[event][1])
    
    return False
