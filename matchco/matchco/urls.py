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
from home.views import home
from matchco.root_router import root as root_view
from search.views import search
from latest_changes.views import LatestChangesView
from configuration.context_views import select_organization
from matchco.core.pwa import service_worker
from matchco.views import OrganizationSelectorView, SwitchOrganizationView, no_access_view, SmartHomeView
from documents.views import LegacyProtectedMediaView
from console.certification_public_views import CertificationVerificationView


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
    # Compatibility aliases requested automatically by browsers and mobile icons.
    path('favicon.ico', RedirectView.as_view(url='/static/matchco_site/img/matchco-icone-m.svg'), name='root-favicon'),
    path('apple-touch-icon.png', RedirectView.as_view(url='/static/matchco_site/img/matchco-icone-m.svg'), name='apple-touch-icon'),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url='/static/matchco_site/img/matchco-icone-m.svg'), name='apple-touch-icon-precomposed'),

    # Raiz institucional:
    #   anônimo → landing MatchCo pública
    #   autenticado → app principal (/app/)
    #   Console nunca é destino automático.
    path('', SmartHomeView.as_view(), name='home'),
    path('app/', include('app_urls')),
    path('', include('accounts.urls')),
    path('', include('configuration.urls')),
    path('organization/select/', select_organization, name='select_organization'),
    path('select-organization/', OrganizationSelectorView.as_view(), name='select-organization'),
    path('switch-organization/', SwitchOrganizationView.as_view(), name='switch-organization'),
    path('no-access/', no_access_view, name='no-access'),
    path('gamification/', include('gamification.urls')),
    path('console/', include('console.urls')),
    # Console admin MatchCo do lojista (necessidades, EntryPoints, métricas, ledger)
    path('console/recruitment/', include('recruitment.urls')),
    # Porta Match público — landing, signup, OTP, LGPD, QR (sem prefixo /console/)
    path('', include(('recruitment.urls_public', 'recruitment_public'), namespace='recruitment_public')),
    path('notifications/', include('learning.urls')),
    path('certificacoes/verificar/<uuid:code>/', CertificationVerificationView.as_view(), name='certification-verify'),
    path('partner/', include('learning.partner_urls')),
    path('documents/', include('documents.urls')),
    # Legacy storage URLs for governed assets must still pass authorization.
    path('media/media-library/<path:file_path>', LegacyProtectedMediaView.as_view(), {'storage_prefix': 'media-library/'}, name='legacy-protected-media'),
    path('media/documents/versions/<path:file_path>', LegacyProtectedMediaView.as_view(), {'storage_prefix': 'documents/versions/'}, name='legacy-protected-document-version'),
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

    # O Console e o app autenticado são as superfícies atuais de aprendizado.
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
