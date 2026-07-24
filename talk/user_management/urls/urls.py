from django.contrib.auth import login
from django.urls import path
from django.contrib.auth.decorators import login_required

from user_management import views
from user_management.views import UserProfileDetailView, UserProfileGamificationPoints

app_name = 'user_management_profile'
urlpatterns = [
    path('<int:pk>/', login_required(UserProfileDetailView.as_view(), login_url='/login/'), name='user_profile_detail'),
    path('settings', login_required(views.redirect_profile_settings, login_url='/login'), name='user_profile_settings_menu'),

    path('gamification-points/<int:pk>/', login_required(UserProfileGamificationPoints.as_view(), login_url='/login/'), name='user_gamification_points')
]
