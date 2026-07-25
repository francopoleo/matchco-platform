from django.urls import path

from .views import NotificationListView, NotificationReadAllView, NotificationReadView, OperationalActionEventView, PushSubscriptionView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications'),
    path('<int:pk>/read/', NotificationReadView.as_view(), name='notification-read'),
    path('read-all/', NotificationReadAllView.as_view(), name='notifications-read-all'),
    path('push/subscribe/', PushSubscriptionView.as_view(), name='notifications-push-subscribe'),
    path('events/action/', OperationalActionEventView.as_view(), name='learning-action-event'),
]
