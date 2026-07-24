from .views import ChangePasswordView
from django.urls import path

urlpatterns = [
    path('api/change-password/', ChangePasswordView.as_view(), name='change-password'),
]
