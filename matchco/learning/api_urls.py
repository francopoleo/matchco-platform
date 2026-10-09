from django.urls import path

from .api import (
    DocumentCollectionApiView, DocumentDetailApiView, DocumentDownloadsApiView,
    DocumentVersionApiView, EngagementAnalyticsApiView, GamificationLeaderboardApiView, GamificationSummaryApiView, IntegrationCredentialApiView, IntegrationCredentialRotateApiView, MobileEventsApiView, PartnerPortalApiView,
    MobileSyncApiView,
)

app_name = 'learning_api'

urlpatterns = [
    path('documents/', DocumentCollectionApiView.as_view(), name='documents'),
    path('documents/<int:pk>/', DocumentDetailApiView.as_view(), name='document-detail'),
    path('documents/<int:pk>/downloads/', DocumentDownloadsApiView.as_view(), name='document-downloads'),
    path('documents/<int:pk>/versions/', DocumentVersionApiView.as_view(), name='document-versions'),
    path('analytics/engagement/', EngagementAnalyticsApiView.as_view(), name='analytics-engagement'),
    path('gamification/summary/', GamificationSummaryApiView.as_view(), name='gamification-summary'),
    path('gamification/leaderboard/', GamificationLeaderboardApiView.as_view(), name='gamification-leaderboard'),
    path('integrations/credentials/', IntegrationCredentialApiView.as_view(), name='integration-credentials'),
    path('integrations/credentials/<int:pk>/rotate/', IntegrationCredentialRotateApiView.as_view(), name='integration-credential-rotate'),
    path('partner/me/', PartnerPortalApiView.as_view(), name='partner-me'),
    path('mobile/sync/', MobileSyncApiView.as_view(), name='mobile-sync'),
    path('mobile/events/', MobileEventsApiView.as_view(), name='mobile-events'),
]
