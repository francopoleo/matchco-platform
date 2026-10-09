from django.contrib.auth.views import LogoutView
from django.urls import path, include

from .views import SignUpView, CustomLoginView, RegistrationPendingView, PublicSignupView, PublicConfirmEmailView, PublicSignupConfirmationView
from .demo_views import demo_access

urlpatterns = [
    path('cadastro-pendente/', RegistrationPendingView.as_view(), name='registration_pending'),
    path('demo/', demo_access, name='demo_access'),
    path('signup/', SignUpView.as_view(redirect_authenticated_user=True), name='signup'),
    path('login/', CustomLoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Public signup flows
    path('signup/public/<str:category>/', PublicSignupView.as_view(), name='public-signup'),
    path('signup/public/confirm/<str:category>/<int:uid>/<str:token>/', PublicConfirmEmailView.as_view(), name='public-confirm-email'),
    path('signup/public/<str:category>/confirmation/', PublicSignupConfirmationView.as_view(), name='public-signup-confirmation'),

    # Reset password
    path('', include('django.contrib.auth.urls')),
]
