from django.urls import path

from .views import (
    ConsoleDashboardView,
    CourseConsoleCreateView,
    CourseConsoleListView,
    CourseConsoleUpdateView,
    PolicyConsoleCreateView,
    PolicyConsoleListView,
    PublicationConsoleCreateView,
    PublicationConsoleListView,
    PublicationConsoleUpdateView,
    AudienceSimulationView,
    MembershipAssignmentView,
    ManagementAssignmentListView, ManagementAssignmentFormView,
    ManagementReportView,
    PolicyConsoleUpdateView,
    UserConsoleCreateView,
    UserConsoleListView,
    UserConsoleUpdateView,
    OrganizationSettingsView,
)

app_name = 'console'

urlpatterns = [
    path('', ConsoleDashboardView.as_view(), name='dashboard'),
    path('publications/', PublicationConsoleListView.as_view(), name='publication-list'),
    path('publications/new/', PublicationConsoleCreateView.as_view(), name='publication-create'),
    path('publications/<int:pk>/edit/', PublicationConsoleUpdateView.as_view(), name='publication-edit'),
    path('audience/simulation/', AudienceSimulationView.as_view(), name='audience-simulation'),
    path('users/assign/', MembershipAssignmentView.as_view(), name='assignment'),
    path('management-assignments/', ManagementAssignmentListView.as_view(), name='management-assignments'),
    path('management-assignments/new/', ManagementAssignmentFormView.as_view(), name='management-assignment-new'),
    path('management-assignments/<int:pk>/edit/', ManagementAssignmentFormView.as_view(), name='management-assignment-edit'),
    path('management-reports/', ManagementReportView.as_view(), name='management-reports'),
    path('courses/', CourseConsoleListView.as_view(), name='course-list'),
    path('courses/new/', CourseConsoleCreateView.as_view(), name='course-create'),
    path('courses/<int:pk>/edit/', CourseConsoleUpdateView.as_view(), name='course-edit'),
    path('policies/', PolicyConsoleListView.as_view(), name='policy-list'),
    path('policies/new/', PolicyConsoleCreateView.as_view(), name='policy-create'),
    path('policies/<int:pk>/edit/', PolicyConsoleUpdateView.as_view(), name='policy-edit'),
    path('users/', UserConsoleListView.as_view(), name='user-list'),
    path('users/new/', UserConsoleCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/edit/', UserConsoleUpdateView.as_view(), name='user-edit'),
    path('organization-settings/', OrganizationSettingsView.as_view(), name='organization-settings'),
]
