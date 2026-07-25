from django.contrib.auth import login
from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView

from rest_framework import permissions, routers
from rest_framework_simplejwt import views as jwt_views


from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from user_management.api.viewsets import UserViewSet
from user_management.views import UserProfileDetailView
from courses.views import CourseListView, TestListView
from home.views import home
from search.views import search
from latest_changes.views import LatestChangesView
from configuration.context_views import select_organization
from cep.core.pwa import service_worker


schema_view = get_schema_view(
    openapi.Info(
        title="CEP API",
        default_version='v1',
        description="Welcome",
        terms_of_service="https://www.epson.com",
        contact=openapi.Contact(email="teste@epson.com"),
        license=openapi.License(name="Awesome IP"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [

    path('service-worker.js', service_worker, name='service-worker'),

    # Revisar login
    path('', login_required(home, login_url='/login/'), name='home'),
    path('', include('accounts.urls')),
    path('accounts/login/', RedirectView.as_view(pattern_name='login', query_string=True), name='legacy_login'),
    path('', include('configuration.urls')),
    path('organization/select/', select_organization, name='select_organization'),
    path('gamification/', include('gamification.urls')),
    path('console/', include('console.urls')),
    path('notifications/', include('learning.urls')),
    path('partner/', include('learning.partner_urls')),
    path('documents/', include('documents.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    # Django Admin is the primary application admin during the migration.
    path('admin/', admin.site.urls),
    path('admin/users-management/', include('user_management.urls.urls_admin')),
    path('reset_password/', include('password_reset.urls')),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),

    re_path(r'^doc(?P<format>\.json|\.yaml)$', schema_view.without_ui(
        cache_timeout=0), name='schema-json'),
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0)),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    #     Course
    path('course/', include('courses.urls')),
    path('course-list/', login_required(CourseListView.as_view(), login_url='/login/'), name='course_list'),
    path('test-list/', login_required(TestListView.as_view(), login_url='/login/'), name='test_list'),
    path('students/', include('students.urls')),
    path('', include('publishing.urls')),
    path('api/', include('courses.api.urls', namespace='api')),
    path('api/v1/', include('learning.api_urls', namespace='learning_api')),
    path('api/mobile/', include('learning.mobile_urls')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('user-profile/', include('user_management.urls.urls')),
    path('search/', search, name='search'),
    path('latest-changes/', LatestChangesView.as_view(), name='latest_changes'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
