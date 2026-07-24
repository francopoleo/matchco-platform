from django.contrib.auth.views import LogoutView
from django.urls import path, include

from .views import SignUpView, CustomLoginView

urlpatterns = [
    path('signup/', SignUpView.as_view(redirect_authenticated_user=True), name='signup'),
    path('login/', CustomLoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Reset password
    path('', include('django.contrib.auth.urls')),
]
