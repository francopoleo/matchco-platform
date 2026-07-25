from django.urls import path

from .views import DocumentDetailView, DocumentDownloadView, DocumentEventView, DocumentListView


urlpatterns = [
    path('', DocumentListView.as_view(), name='document-list'),
    path('<slug:slug>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<slug:slug>/download/', DocumentDownloadView.as_view(), name='document-download'),
    path('<slug:slug>/event/', DocumentEventView.as_view(), name='document-event'),
]
