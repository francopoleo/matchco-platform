from django.urls import path
from configuration.views import GetCompanyApi, GetBusinessUnitApi, GetBusinessChannelApi, GetOperationalUnitApi, GetJobFunctionApi, GetJobFunctionApiToUser
from configuration.setup_views import SetupView

urlpatterns = [
    path('setup/', SetupView.as_view(), name='setup'),
    path('companies/api/', GetCompanyApi.as_view()),
    path('business-units/api/', GetBusinessUnitApi.as_view()),
    path('operational-units/api/', GetOperationalUnitApi.as_view()),
    path('business-channels/api/', GetBusinessChannelApi.as_view()),
    path('job-functions/api/', GetJobFunctionApi.as_view()),
    path('job-functions/users/api/', GetJobFunctionApiToUser.as_view()),
]
