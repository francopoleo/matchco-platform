from django.urls import path

from .views import ContentFeedbackView, ContentQuestionView, PublicationDetailView, PublicationEventView, PublicationListView, RecommendationDismissView, RecommendationOpenView


urlpatterns = [
    path('wiki/', PublicationListView.as_view(), {'kind': 'wiki'}, name='publication_list'),
    path('wiki/<slug:slug>/', PublicationDetailView.as_view(), {'kind': 'wiki'}, name='publication_detail'),
    path('feed/', PublicationListView.as_view(), {'kind': 'feed'}, name='publication_feed_list'),
    path('feed/<slug:slug>/', PublicationDetailView.as_view(), {'kind': 'feed'}, name='publication_feed_detail'),
    path('publication/<str:kind>/<slug:slug>/event/', PublicationEventView.as_view(), name='publication_event'),
    path('recommendations/<int:pk>/open/', RecommendationOpenView.as_view(), name='recommendation-open'),
    path('recommendations/<int:pk>/dismiss/', RecommendationDismissView.as_view(), name='recommendation-dismiss'),
    path('feedback/', ContentFeedbackView.as_view(), name='content_feedback'),
    path('questions/', ContentQuestionView.as_view(), name='content_question'),
]
