"""
URLs da Web App MatchCo - /app/* namespace

Estrutura completa da aplicação para usuários autenticados.
Todas as rotas requerem login e organização selecionada.
"""

from django.urls import path, include
from django.contrib.auth.decorators import login_required
from courses.views import CourseListView
from students.views import StudentTrailListView
from publishing.views import PublicationListView
from learning.views import NotificationListView
from app_views import (
    AppDashboardView, AppProfileView, AppProfileEditView, AppSettingsView,
    AppCourseDetailView, AppCoursePlayerView, AppCourseProgressView,
    AppOpportunitiesView,
    AppMatchesView, AppMatchDetailView,
    AppHelpView, AppHelpTopicView,
    AppNotificationReadView
)

app_name = 'app'

urlpatterns = [
    # Dashboard Principal
    path('', AppDashboardView.as_view(), name='dashboard'),

    # Perfil do Usuário
    path('profile/', AppProfileView.as_view(), name='profile'),
    path('profile/edit/', AppProfileEditView.as_view(), name='profile_edit'),
    path('settings/', AppSettingsView.as_view(), name='settings'),

    # Cursos e Aprendizado
    path('courses/', login_required(CourseListView.as_view(), login_url='/login/'), name='courses'),
    path('courses/<int:course_id>/', AppCourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:course_id>/play/', AppCoursePlayerView.as_view(), name='course_play'),
    path('courses/<int:course_id>/progress/', AppCourseProgressView.as_view(), name='course_progress'),

    # Feed, Trails, Wiki / Oportunidades
    path('feed/', login_required(PublicationListView.as_view(), login_url='/login/'), {'kind': 'feed'}, name='feed'),
    path('trails/', login_required(StudentTrailListView.as_view(), login_url='/login/'), name='trails'),
    path('wiki/', login_required(PublicationListView.as_view(), login_url='/login/'), {'kind': 'wiki'}, name='wiki'),
    path('opportunities/', AppOpportunitiesView.as_view(), name='opportunities'),

    # Matches e Conversas
    path('matches/', AppMatchesView.as_view(), name='matches'),
    path('matches/<int:match_id>/', AppMatchDetailView.as_view(), name='match_detail'),

    # Help e Documentação
    path('help/', AppHelpView.as_view(), name='help'),
    path('help/<str:topic>/', AppHelpTopicView.as_view(), name='help_topic'),

    # Notificações
    path('notifications/', login_required(NotificationListView.as_view(), login_url='/login/'), name='notifications'),
    path('notifications/<int:notification_id>/read/', AppNotificationReadView.as_view(), name='notification_read'),

    # API endpoints (future)
    # path('api/', include('app.api_urls')),
]
