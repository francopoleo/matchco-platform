from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from courses.models import Course
from publishing.models import Publication


def home(request):
    visible_apps = [
        {
            'label': _('Courses'),
            'description': _('Continue your learning journey.'),
            'url': reverse('course_list'),
            'icon': 'course',
            'tone': 'cyan',
        },
        {
            'label': _('Feed'),
            'description': _('See the latest updates.'),
            'url': reverse('publication_feed_list'),
            'icon': 'feed',
            'tone': 'emerald',
        },
        {
            'label': _('Wiki'),
            'description': _('Explore the knowledge base.'),
            'url': reverse('publication_list'),
            'icon': 'wiki',
            'tone': 'amber',
        },
        {
            'label': _('Gamification'),
            'description': _('Track your points and achievements.'),
            'url': reverse('user_management_profile:user_gamification_points', kwargs={'pk': request.user.pk}) if request.user.is_authenticated else reverse('login'),
            'icon': 'game',
            'tone': 'fuchsia',
        },
    ]
    if request.user.is_staff or request.user.is_superuser:
        visible_apps.append({
            'label': _('Management console'),
            'description': _('Manage content and audience policies.'),
            'url': reverse('console:dashboard'),
            'icon': 'console',
            'tone': 'violet',
        })

    return render(request, 'home/home.html', {
        'visible_apps': visible_apps,
        'course_count': Course.objects.count(),
        'publication_count': Publication.objects.count(),
        'published_publication_count': Publication.objects.filter(status=Publication.PUBLISHED).count(),
    })
