from django.urls import path

from . import views


app_name = 'recruitment'

urlpatterns = [
    # Public
    path('candidato/', views.CandidateSignupView.as_view(), name='candidate_signup'),
    path('candidato/sucesso/', views.CandidateSignupSuccessView.as_view(), name='candidate_signup_success'),

    # Candidate onboarding trail
    path('onboarding/funcoes/', views.CandidateOnboardingJobFunctionsView.as_view(), name='job_functions'),
    path('onboarding/candidato/<int:candidate_id>/pesquisa/', views.CandidateProfileSurveyView.as_view(), name='candidate_survey'),
    path('onboarding/candidato/<int:candidate_id>/concluido/', views.CandidateOnboardingCompleteView.as_view(), name='onboarding_complete'),

    # Console
    path('candidatos/', views.CandidateListView.as_view(), name='candidate_list'),
    path('candidatos/<int:pk>/', views.CandidateDetailView.as_view(), name='candidate_detail'),
    path('candidatos/<int:candidate_pk>/oferta/', views.OfferCreateView.as_view(), name='offer_create'),
    path('candidatos/<int:candidate_pk>/curso/<int:course_id>/completo/', views.MarkCourseCompleteView.as_view(), name='mark_course_complete'),

    path('vagas/', views.PositionListView.as_view(), name='position_list'),
    path('vagas/nova/', views.PositionCreateView.as_view(), name='position_create'),
    path('vagas/<int:pk>/editar/', views.PositionUpdateView.as_view(), name='position_update'),
    path('api/vagas/unidade/<int:business_unit_id>/funcoes/', views.JobFunctionsForBusinessUnitView.as_view(), name='api_job_functions'),

    path('qr-code/', views.QRCodeView.as_view(), name='qr_code'),
    path('qr-code/loja/<int:store_id>/', views.QRCodeStoreView.as_view(), name='qr_code_store'),

    # Employee dashboard
    path('dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
]
