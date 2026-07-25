from django.contrib.auth.views import LogoutView
from django.urls import path, include

from .views import SignUpView, CustomLoginView, PublicLandingView, RegistrationPendingView
from .demo_views import demo_access

urlpatterns = [
    path('sobre-talk/', PublicLandingView.as_view(), name='public_landing'),
    path('cadastro-pendente/', RegistrationPendingView.as_view(), name='registration_pending'),
    path('demo/', demo_access, name='demo_access'),
    path('signup/', SignUpView.as_view(redirect_authenticated_user=True), name='signup'),
    path('login/', CustomLoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Reset password
    path('', include('django.contrib.auth.urls')),
]
