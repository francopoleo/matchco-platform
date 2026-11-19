"""
URLs da Web App MatchCo - /app/* namespace

Estrutura completa da aplicação para usuários autenticados.
Todas as rotas requerem login e organização selecionada.
"""

from django.urls import path, include
from django.contrib.auth.decorators import login_required
from app_views import (
    AppDashboardView, AppProfileView, AppProfileEditView, AppSettingsView,
    AppCourseDetailView, AppCoursePlayerView, AppCourseProgressView,
    AppOpportunitiesView,
    AppMatchesView, AppMatchDetailView,
    AppHelpView, AppHelpTopicView,
    AppNotificationReadView
)


def lazy_tenant_view(module_path, class_name):
    """Importa views de TENANT_APPS apenas quando a requisição chega.
    
    Os apps de tenant (courses, publishing, students, learning) só estão
    disponíveis após o TenantMainMiddleware selecionar o schema.
    Importar no topo do módulo falharia porque o Django carrega as URLs
    antes de ter um tenant ativo.
    """
    def view(request, *args, **kwargs):
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        return cls.as_view()(request, *args, **kwargs)
    return view


app_name = 'app'

urlpatterns = [
    # Dashboard Principal
    path('', AppDashboardView.as_view(), name='dashboard'),

    # Perfil do Usuário
    path('profile/', AppProfileView.as_view(), name='profile'),
    path('profile/edit/', AppProfileEditView.as_view(), name='profile_edit'),
    path('settings/', AppSettingsView.as_view(), name='settings'),

    # Cursos e Aprendizado (lazy import - tenant apps)
    path('courses/', login_required(lazy_tenant_view('courses.views', 'CourseListView'), login_url='/login/'), name='courses'),
    path('courses/<slug:course_id>/', AppCourseDetailView.as_view(), name='course_detail'),
    path('courses/<slug:course_id>/play/', AppCoursePlayerView.as_view(), name='course_play'),
    path('courses/<slug:course_id>/progress/', AppCourseProgressView.as_view(), name='course_progress'),

    # Feed, Trails, Wiki / Oportunidades (lazy import - tenant apps)
    path('feed/', login_required(lazy_tenant_view('publishing.views', 'PublicationListView'), login_url='/login/'), {'kind': 'feed'}, name='feed'),
    path('trails/', login_required(lazy_tenant_view('students.views', 'StudentTrailListView'), login_url='/login/'), name='trails'),
    path('wiki/', login_required(lazy_tenant_view('publishing.views', 'PublicationListView'), login_url='/login/'), {'kind': 'wiki'}, name='wiki'),
    path('opportunities/', AppOpportunitiesView.as_view(), name='opportunities'),

    # Matches e Conversas
    path('matches/', AppMatchesView.as_view(), name='matches'),
    path('matches/<int:match_id>/', AppMatchDetailView.as_view(), name='match_detail'),

    # Help e Documentação
    path('help/', AppHelpView.as_view(), name='help'),
    path('help/<str:topic>/', AppHelpTopicView.as_view(), name='help_topic'),

    # Notificações (lazy import - tenant app)
    path('notifications/', login_required(lazy_tenant_view('learning.views', 'NotificationListView'), login_url='/login/'), name='notifications'),
    path('notifications/<int:notification_id>/read/', AppNotificationReadView.as_view(), name='notification_read'),

    # Students (enroll, courses, trails, quizzes, certificates)
    path('', include('students.urls')),

    # Courses (catalog, subjects, modules, content management)
    path('', include('courses.urls')),

    # API endpoints (future)
    # path('api/', include('app.api_urls')),
]
