from django.urls import path

from .views import ContentItemDetailView


urlpatterns = [
    path('content/<int:pk>/', ContentItemDetailView.as_view(), name='library_content_detail'),
]
