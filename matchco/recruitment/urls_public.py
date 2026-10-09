"""URLs públicas MatchCo — três portais externos + LGPD.

- /candidato/*  — portal do candidato (OTP passwordless)
- /portal/*     — portal operacional genérico (login+senha)
- /matchco/*    — landing pública comercial
- /privacidade/*— páginas LGPD

Console admin permanece em /console/recruitment/ para ops/superuser.
"""
from django.urls import path

from . import portal_views as pv
from . import views


app_name = 'recruitment_public'

urlpatterns = [
    # ---- Landing pública -------------------------------------------------
    path('matchco/', views.MatchcoLandingView.as_view(), name='matchco_landing'),
    path('matchco/acessos/', views.MatchcoAccessView.as_view(), name='matchco_access'),

    # ---- Novas rotas do site institucional MatchCo ----
    path('matchco/como-funciona/', views.TemplateView.as_view(template_name='recruitment/matchco_site/como-funciona.html'), name='matchco_como_funciona'),
    path('matchco/para-shoppings/', views.TemplateView.as_view(template_name='recruitment/matchco_site/para-shoppings.html'), name='matchco_para_shoppings'),
    path('matchco/para-lojas/', views.TemplateView.as_view(template_name='recruitment/matchco_site/para-lojas.html'), name='matchco_para_lojas'),
    path('matchco/para-voce/', views.TemplateView.as_view(template_name='recruitment/matchco_site/para-voce.html'), name='matchco_para_voce'),
    path('matchco/perguntas/', views.TemplateView.as_view(template_name='recruitment/matchco_site/perguntas.html'), name='matchco_perguntas'),

    path('matchco/entrar/', views.MatchcoRoleChooserView.as_view(), name='matchco_role_chooser'),
    path('matchco/entrada/<uuid:entry_point_id>/', views.EntryPointChoiceView.as_view(), name='entry_point_choice'),
    path('matchco/programa/<uuid:entry_point_id>/', views.ProgramEntryView.as_view(), name='program_entry'),
    path('matchco/programa/id/<int:program_id>/', views.ProgramDirectView.as_view(), name='program_direct'),
    path('matchco/programa/convite/<str:token>/', views.ProgramInviteAcceptView.as_view(), name='program_invite_accept'),

    # ---- Área do candidato ----------------------------------------------
    path('candidato/', pv.CandidatoHomeView.as_view(), name='candidato_home'),
    path('candidato/entrar/', views.OtpRequestView.as_view(), name='candidato_entrar'),
    path('candidato/entrar/codigo/', views.OtpVerifyView.as_view(), name='candidato_entrar_codigo'),
    path('candidato/signup/', views.MatchcoSignupView.as_view(), name='candidato_signup'),
    path('candidato/signup/pronto/', views.MatchcoSignupDoneView.as_view(), name='candidato_signup_done'),

    # --- QR Redesign: Store Selection & Custom Signup ---
    path('candidato/loja/escolher/', views.StoreChooserView.as_view(), name='candidato_store_choose'),
    path('candidato/acao/escolher/', views.ActionChooserView.as_view(), name='candidato_action_choose'),
    path('candidato/formulario/', views.CustomSignupView.as_view(), name='candidato_custom_signup'),
    path('candidato/enriquecimento/<str:token>/', views.EnrichmentCampaignView.as_view(), name='candidate_enrichment_campaign'),
    path('candidato/dados/exportar/', views.CandidateDataExportView.as_view(), name='candidate_data_export'),
    path('candidato/dados/corrigir/', views.CandidateDataCorrectionView.as_view(), name='candidate_data_correction'),
    path('candidato/dados/anonimizar/', views.CandidateAnonymizeView.as_view(), name='candidate_data_anonymize'),
    path('candidato/onboarding/funcoes/', views.CandidateOnboardingJobFunctionsView.as_view(), name='candidate_job_functions'),
    path('candidato/onboarding/<int:candidate_id>/pesquisa/', views.CandidateProfileSurveyView.as_view(), name='candidate_survey'),
    path('candidato/onboarding/<int:candidate_id>/concluido/', views.CandidateOnboardingCompleteView.as_view(), name='candidate_onboarding_complete'),
    path('candidato/oportunidades/', pv.CandidatoFeedView.as_view(), name='candidato_feed'),
    path('candidato/oportunidades/<int:opportunity_id>/interesse/',
         pv.CandidatoInteresseView.as_view(), name='candidato_interesse'),
    path('candidato/oportunidades/<int:opportunity_id>/recusar/',
         pv.CandidatoRecusarView.as_view(), name='candidato_recusar'),
    path('candidato/matches/', pv.CandidatoMatchesView.as_view(), name='candidato_matches'),
    path('candidato/relation/<uuid:relation_id>/negociacao/',
         views.CandidateRelationNegotiationView.as_view(), name='candidato_negotiation'),
    path('candidato/perfil/', pv.CandidatoPerfilView.as_view(), name='candidato_perfil'),
    path('candidato/perfil/consent/', pv.CandidatoConsentToggleView.as_view(), name='candidato_consent_toggle'),
    path('candidato/perfil/circulacao/', pv.CandidatoCirculacaoToggleView.as_view(),
         name='candidato_circulacao_toggle'),
    path('candidato/contexto/', pv.CandidatoContextoView.as_view(), name='candidato_contexto'),
    path('candidato/sair/', pv.CandidatoLogoutView.as_view(), name='candidato_sair'),

    # ---- Portal operacional genérico -------------------------------------
    path('portal/', pv.LojistaHomeView.as_view(), name='lojista_home'),
    path('portal/entrar/', pv.LojistaEntrarView.as_view(), name='lojista_entrar'),
    path('portal/contexto/', pv.LojistaContextoView.as_view(), name='lojista_contexto'),
    path('portal/contexto/unidade/', pv.LojistaUnidadeContextoView.as_view(), name='lojista_unidade_contexto'),
    path('portal/necessidades/', pv.LojistaNecessidadesView.as_view(), name='lojista_necessidades'),
    path('portal/necessidades/nova/', pv.LojistaDeclararView.as_view(), name='lojista_declarar'),
    path('portal/necessidades/simular/', pv.LojistaSimularView.as_view(), name='lojista_simular'),
    path('portal/necessidades/unidade/<int:business_unit_id>/funcoes/', pv.LojistaJobFunctionsView.as_view(), name='lojista_job_functions'),
    path('portal/gestao/funcoes/', pv.LojistaFunctionCatalogView.as_view(), name='lojista_funcoes'),
    path('portal/oportunidades/<int:opportunity_id>/',
         pv.LojistaOportunidadePilhaView.as_view(), name='lojista_oportunidade_pilha'),
    path('portal/relation/<uuid:relation_id>/',
         pv.LojistaRelationDetailView.as_view(), name='lojista_relation'),
    path('portal/relation/<uuid:relation_id>/interessar/',
         pv.LojistaInteressarView.as_view(), name='lojista_interessar'),
    path('portal/relation/<uuid:relation_id>/declinar/',
         pv.LojistaDeclinarView.as_view(), name='lojista_declinar'),
    path('portal/relation/<uuid:relation_id>/liberar-contato/',
         pv.LojistaLiberarContatoView.as_view(), name='lojista_liberar_contato'),
    path('portal/relation/<uuid:relation_id>/responder/',
         pv.LojistaResponderView.as_view(), name='lojista_responder'),
    path('portal/pontos/', pv.LojistaPontosView.as_view(), name='lojista_pontos'),
    path('portal/pontos/<uuid:entry_point_id>/', pv.LojistaPontoDetalheView.as_view(),
         name='lojista_ponto_detalhe'),
    path('portal/metricas/', pv.LojistaMetricasView.as_view(), name='lojista_metricas'),
    path('portal/atores/', pv.LojistaAtoresView.as_view(), name='lojista_atores'),
    path('portal/convites/', pv.LojistaInvitesView.as_view(), name='lojista_invites'),
    path('portal/convite/<str:token>/', pv.LojistaInviteAcceptView.as_view(),
         name='lojista_invite_accept'),

    # ---- Onboarding de uma organização -----------------------------------
    path('portal/cadastrar/', pv.ShoppingCadastrarView.as_view(), name='shopping_cadastrar'),

    # ---- LGPD público ----------------------------------------------------
    path('privacidade/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('privacidade/direitos/', views.PrivacyRightsView.as_view(), name='privacy_rights'),
    path('privacidade/processadores/', views.PrivacyProcessorsView.as_view(), name='privacy_processors'),

    # ---- QR resolver + imagem PNG ---------------------------------------
    path('qr/<uuid:entry_point_id>/', views.EntryPointResolveView.as_view(), name='entry_point_resolve'),
    path('qr-image/<uuid:entry_point_id>.png', views.EntryPointQrImageView.as_view(), name='entry_point_qr_image'),
    path('qr-print/<uuid:entry_point_id>/', views.EntryPointPrintView.as_view(), name='entry_point_print'),
]
