from django.urls import path

from .views import DocumentDetailView, DocumentDownloadView, DocumentEventView, DocumentFileView, DocumentListView, DocumentShareView, DocumentThumbnailView, MediaAssetServeView, MediaAssetShareView, MediaAssetConsolePreviewView


urlpatterns = [
    path('', DocumentListView.as_view(), name='document-list'),
    path('<slug:slug>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<slug:slug>/download/', DocumentDownloadView.as_view(), name='document-download'),
    path('<slug:slug>/file/', DocumentFileView.as_view(), name='document-file'),
    path('<slug:slug>/thumbnail/', DocumentThumbnailView.as_view(), name='document-thumbnail'),
    path('<slug:slug>/event/', DocumentEventView.as_view(), name='document-event'),
    path('share/<uuid:token>/', DocumentShareView.as_view(), name='document-share'),
    path('media/<int:pk>/', MediaAssetServeView.as_view(), name='media-asset-serve'),
    path('media/<int:pk>/<str:variant>/', MediaAssetServeView.as_view(), name='media-asset-variant'),
    path('media/share/<uuid:token>/', MediaAssetShareView.as_view(), name='media-share'),
]
