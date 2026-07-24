from django.urls import path

from .views import PublicationDetailView, PublicationListView


urlpatterns = [
    path('wiki/', PublicationListView.as_view(), {'kind': 'wiki'}, name='publication_list'),
    path('wiki/<slug:slug>/', PublicationDetailView.as_view(), {'kind': 'wiki'}, name='publication_detail'),
    path('feed/', PublicationListView.as_view(), {'kind': 'feed'}, name='publication_feed_list'),
    path('feed/<slug:slug>/', PublicationDetailView.as_view(), {'kind': 'feed'}, name='publication_feed_detail'),
]
