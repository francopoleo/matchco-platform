from django.urls import path

from .api import MobileEventsApiView, MobileSyncApiView

urlpatterns = [
    path('sync/', MobileSyncApiView.as_view(), name='mobile-sync'),
    path('events/', MobileEventsApiView.as_view(), name='mobile-events'),
]
