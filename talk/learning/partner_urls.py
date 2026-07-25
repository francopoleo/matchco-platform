from django.urls import path

from .partner_views import PartnerPortalView

urlpatterns = [path('', PartnerPortalView.as_view(), name='partner-portal')]
