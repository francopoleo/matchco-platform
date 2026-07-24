from django.urls import path

from .views.gamification import (
    GamificationSettingsDetailView,
    GamificationSettingsUpdateView,
    HistoricPointsListView,
)
from .views.api.gamification_api import GetGamificationSettingsApi


app_name = 'cepgamification'
urlpatterns = [
    path('settings/<int:pk>/', GamificationSettingsDetailView.as_view(), name='settings-detail'),
    path('settings/<int:pk>/edit/', GamificationSettingsUpdateView.as_view(), name='settings-edit'),
    path('settings/api/', GetGamificationSettingsApi.as_view()),

    path('user-points/<int:pk>/', HistoricPointsListView.as_view(), name='user-points'),

]
