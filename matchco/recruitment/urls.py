from django.urls import path
from . import views


app_name = 'recruitment'

urlpatterns = [
    # A criação e edição de vagas foi retirada. Necessidades de alto giro usam
    # exclusivamente a rota Match abaixo; o endpoint de funções permanece
    # porque é consumido pelo formulário canônico da necessidade.
    path('api/necessidades/unidade/<int:business_unit_id>/funcoes/', views.JobFunctionsForBusinessUnitView.as_view(), name='api_need_job_functions'),

    path('qr-code/', views.QRCodeView.as_view(), name='qr_code'),
    path('qr-code/loja/<int:store_id>/', views.QRCodeStoreView.as_view(), name='qr_code_store'),

    # Porta Match — EmployerInterestView (AA-6) e ContactChannel (AA-8)
    path('empregador/oportunidades/<int:opportunity_id>/interesse/',
         views.EmployerOpportunityInterestListView.as_view(),
         name='employer_opportunity_interest'),
    path('empregador/matches/<uuid:relation_id>/contato/',
         views.EmployerRelationContactView.as_view(),
         name='employer_relation_contact'),
    path('empregador/matches/<uuid:relation_id>/responder/',
         views.EmployerRelationRespondView.as_view(),
         name='employer_relation_respond'),
    path('empregador/relation/<uuid:relation_id>/',
         views.EmployerRelationDetailView.as_view(),
         name='employer_relation_detail'),
    path('empregador/relation/<uuid:relation_id>/interessar/',
         views.EmployerRelationInterestView.as_view(),
         name='employer_relation_interest'),
    path('empregador/relation/<uuid:relation_id>/declinar/',
         views.EmployerRelationDeclineView.as_view(),
         name='employer_relation_decline'),
    path('empregador/relation/<uuid:relation_id>/liberar-contato/',
         views.EmployerRelationEnableContactView.as_view(),
         name='employer_relation_enable_contact'),
    path('empregador/relation/<uuid:relation_id>/negociar/',
         views.EmployerRelationNegotiationView.as_view(),
         name='employer_relation_negotiate'),

    # Porta Match — observabilidade (D1/D2)
    path('ops/metrics/', views.OpsMetricsView.as_view(), name='ops_metrics'),
    path('ops/ledger/', views.OpsLedgerView.as_view(), name='ops_ledger'),
    path('ops/access-audit/', views.RecruitmentAccessAuditView.as_view(), name='access_audit'),

    # Porta Match — gestão de EntryPoints (A5)
    path('empregador/programas/', views.ProgramListCreateView.as_view(), name='program_list'),
    path('empregador/programas/convites/', views.ProgramInviteListCreateView.as_view(), name='program_invites'),
    path('empregador/pontos/', views.EntryPointListView.as_view(), name='entry_point_list'),
    path('empregador/pontos/novo/', views.EntryPointCreateView.as_view(), name='entry_point_create'),
    path('empregador/pontos/<uuid:entry_point_id>/',
         views.EntryPointDetailView.as_view(), name='entry_point_detail'),
    path('empregador/pontos/<uuid:entry_point_id>/editar/',
         views.EntryPointUpdateView.as_view(), name='entry_point_edit'),

    # Porta Match — listagem de necessidades
    path('empregador/necessidades/', views.MatchcoOpportunityListView.as_view(),
         name='matchco_opportunity_list'),

    # Porta Match — declaração de necessidade (A4)
    path('empregador/necessidade/nova/', views.EmployerDeclareNeedView.as_view(),
         name='employer_declare_need'),
    path('empregador/necessidade/simular/', views.EmployerNeedSimulateView.as_view(),
         name='employer_need_simulate'),
    path('empregador/lojas/<int:store_id>/funcoes/', views.StoreFunctionCatalogView.as_view(),
         name='store_function_catalog'),

    # Portal interno MatchCo — rota agnóstica; o escopo vem da organização e do usuário
    path('matchco/portal/', views.LojistaHomeView.as_view(), name='portal_home'),

]
