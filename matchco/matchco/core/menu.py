"""Shared navigation model for the frontend and management console."""

from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from urllib.parse import parse_qsl


MENU_ITEMS = (
    # Frontend public/authenticated routes
    {"label": _("Home"), "url": "home", "icon": "home", "areas": ("frontend",), "group": "start"},

    # App principal em /app/, com o mesmo conteúdo rico da antiga raiz.
    {"label": _("Cursos"), "url": "app:courses", "icon": "course", "areas": ("frontend",), "auth": True, "group": "content"},
    {"label": _("Trilhas"), "url": "app:trails", "icon": "course", "areas": ("frontend",), "auth": True, "group": "content"},
    {"label": _("Notificações"), "url": "app:notifications", "icon": "feed", "areas": ("frontend",), "auth": True, "group": "start"},
    {"label": _("Feed"), "url": "app:feed", "icon": "feed", "areas": ("frontend",), "auth": True, "group": "content"},
    {"label": _("Wiki"), "url": "app:wiki", "icon": "wiki", "areas": ("frontend",), "auth": True, "group": "content"},
    {"label": _("Documentos"), "url": "document-list", "icon": "wiki", "areas": ("frontend",), "auth": True, "group": "content"},

    # Conta e navegação pessoal
    {"label": _("Perfil"), "url": "app:profile", "icon": "profile", "areas": ("frontend",), "auth": True, "group": "account"},
    {"label": _("Gamificação"), "url": "user_management_profile:user_gamification_points", "icon": "game", "areas": ("frontend",), "auth": True, "group": "account"},

    # Console administrativo por camadas de responsabilidade.
    {"label": _("Search"), "url": "search", "icon": "search", "areas": ("frontend",), "group": "content"},
    {"label": _("Administração global"), "url": "console:admin-dashboard", "icon": "policy", "areas": ("console",), "superuser": True, "group": "access"},
    {"label": _("Resetar dados de teste"), "url": "console:demo-reset", "icon": "policy", "areas": ("console",), "superuser": True, "group": "matchco_ops"},
    {"label": _("Cursos"), "url": "console:course-list", "icon": "course", "areas": ("console",), "staff": True, "group": "content", "service": "training"},
    {"label": _("Avaliações"), "url": "console:quiz-list", "icon": "feed", "areas": ("console",), "staff": True, "group": "content", "service": "training"},
    {"label": _("Publicações"), "url": "console:publication-list", "icon": "wiki", "areas": ("console",), "staff": True, "group": "content", "service": "content"},
    {"label": _("Documentos"), "url": "console:document-list", "icon": "wiki", "areas": ("console",), "staff": True, "group": "content", "service": "content"},
    {"label": _("Biblioteca de mídia"), "url": "console:media-list", "icon": "feed", "areas": ("console",), "staff": True, "group": "content", "service": "content"},
    {"label": _("Métricas da biblioteca"), "url": "console:media-metrics", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence", "service": "analytics"},
    {"label": _("Auditoria de conteúdo"), "url": "console:content-audit", "icon": "policy", "areas": ("console",), "staff": True, "group": "intelligence", "service": "content"},
    {"label": _("Métricas de conteúdo"), "url": "console:content-metrics", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence", "service": "analytics"},
    {"label": _("Funil de engajamento"), "url": "console:engagement-funnel", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence", "service": "analytics"},
    {"label": _("Métricas de aprendizagem"), "url": "console:learning-metrics", "icon": "course", "areas": ("console",), "staff": True, "group": "intelligence", "service": "analytics"},
    {"label": _("Dúvidas e feedback"), "url": "console:content-questions", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence", "service": "content"},
    {"label": _("Auditoria de conteúdos"), "url": "console:latest-changes", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence", "service": "content"},
    {"label": _("Trilhas e recomendações"), "url": "console:trail-list", "icon": "course", "areas": ("console",), "staff": True, "group": "content", "service": "training"},
    {"label": _("Certificações"), "url": "console:certification-list", "icon": "policy", "areas": ("console",), "staff": True, "group": "content", "service": "certification"},
    {"label": _("Políticas de audiência"), "url": "console:audience-policy-list", "icon": "policy", "areas": ("console",), "staff": True, "group": "audience"},
    {"label": _("Simulador de audiência"), "url": "console:audience-simulation", "icon": "search", "areas": ("console",), "staff": True, "group": "audience"},
    {"label": _("Impacto da audiência"), "url": "console:audience-impact", "icon": "feed", "areas": ("console",), "staff": True, "group": "audience"},
    {"label": _("Tipos de público e vínculo"), "url": "console:person_type_list", "icon": "profile", "areas": ("console",), "staff": True, "group": "audience"},
    {"label": _("Usuários"), "url": "console:user-list", "icon": "profile", "areas": ("console",), "staff": True, "group": "access"},
    {"label": _("Solicitações de cadastro"), "url": "console:registration-requests", "icon": "profile", "areas": ("console",), "staff": True, "group": "access"},
    {"label": _("Atribuir usuários"), "url": "console:assignment", "icon": "profile", "areas": ("console",), "staff": True, "group": "access"},
    # Organização e estrutura são um único núcleo: a organização define o
    # contexto; empresa, unidade, área, função e canal formam sua estrutura.
    {"label": _("Visão geral da organização"), "url": "console:organization-home", "icon": "home", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Criar organização"), "url": "console:organization-onboarding", "icon": "plus", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Marca e white-label"), "url": "console:organization-brand", "icon": "policy", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Integrações da organização"), "url": "console:integration-connections", "icon": "api", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Estrutura da organização"), "url": "console:organization-settings", "icon": "policy", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Serviços contratados"), "url": "console:organization-services", "icon": "policy", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Empresas"), "url": "console:company_list", "icon": "profile", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Unidades de negócio"), "url": "console:business_unit_list", "icon": "profile", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Unidades operacionais"), "url": "console:operational_unit_list", "icon": "profile", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Cargos da estrutura"), "url": "console:job_function_list", "icon": "profile", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Canais de negócio"), "url": "console:business_channel_list", "icon": "profile", "areas": ("console",), "staff": True, "group": "structure"},
    {"label": _("Papéis de gestão"), "url": "console:management-assignments", "icon": "policy", "areas": ("console",), "staff": True, "group": "access"},
    {"label": _("Hierarquias de grupos"), "url": "console:group-hierarchy-list", "icon": "profile", "areas": ("console",), "staff": True, "group": "access"},
    {"label": _("Auditoria da estrutura"), "url": "console:hierarchy_audit_log", "icon": "feed", "areas": ("console",), "staff": True, "group": "access"},
    {"label": _("Relatórios subordinados"), "url": "console:management-reports", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence"},
    {"label": _("Visitas de demonstração"), "url": "console:demo-visits", "icon": "feed", "areas": ("console",), "staff": True, "group": "matchco_ops"},
    {"label": _("Conformidade"), "url": "console:compliance-dashboard", "icon": "feed", "areas": ("console",), "staff": True, "group": "access"},
    # Recrutamento — necessidades Match de alto giro.
    {"label": _("Templates de perguntas"), "url": "console:questionnaire-templates", "icon": "wiki", "areas": ("console",), "staff": True, "group": "recruitment", "service": "recruitment"},

    # Conta do usuário — disponível no Console sem depender de superusuário.
    {"label": _("Meu perfil"), "url": "user_management_profile:user_profile_detail", "icon": "profile", "areas": ("console",), "auth": True, "group": "account"},
    {"label": _("Configurações da conta"), "url": "user_management_profile:user_profile_settings_menu", "icon": "policy", "areas": ("console",), "auth": True, "group": "account"},

    # MatchCo — oportunidades, recrutamento e portas de entrada no mesmo grupo.
    {"label": _("Necessidades de alto giro"), "url": "recruitment:matchco_opportunity_list", "icon": "feed", "areas": ("console",), "staff": True, "group": "recruitment", "service": "recruitment"},
    {"label": _("Portas de entrada e QR Codes"), "url": "recruitment:entry_point_list", "icon": "feed", "areas": ("console",), "staff": True, "group": "recruitment", "service": "recruitment"},
    {"label": _("Abrir experiência pública"), "url": "recruitment_public:matchco_access", "icon": "feed", "areas": ("console",), "staff": True, "group": "recruitment", "service": "recruitment"},

    # Ops (só superuser)
    {"label": _("Seed MatchCo Demo"), "url": "console:matchco-demo-seed", "icon": "feed", "areas": ("console",), "superuser": True, "group": "matchco_ops"},
    {"label": _("Ledger de auditoria"), "url": "recruitment:ops_ledger", "icon": "feed", "areas": ("console",), "superuser": True, "group": "matchco_ops"},

    # LGPD público
    {"label": _("Política de privacidade"), "url": "recruitment_public:privacy_policy", "icon": "feed", "areas": ("console",), "staff": True, "group": "lgpd"},
    {"label": _("Direitos do titular"), "url": "recruitment_public:privacy_rights", "icon": "feed", "areas": ("console",), "staff": True, "group": "lgpd"},
    {"label": _("Registro de processadores"), "url": "recruitment_public:privacy_processors", "icon": "feed", "areas": ("console",), "staff": True, "group": "lgpd"},
)


def get_menu_items(request, area):
    """Return only resolvable, authorized links for the requested shell."""
    from configuration.organization_context import selected_organization

    items = []
    can_manage_console = (
        request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.groups.filter(name__in=("content_manager", "audience_manager")).exists()
        )
    )

    # Get terminology if in console area
    terminology = None
    active_services = None
    if area == "console":
        org = selected_organization(request)
        if org and hasattr(org, 'terminology') and org.terminology:
            terminology = org.terminology
        if org:
            from configuration.models import OrganizationServiceSubscription
            from configuration.services import service_enabled
            active_company = None
            active_company_id = getattr(request, 'active_company_id', None) or request.session.get('active_company_id')
            if active_company_id:
                active_company = org.companies.filter(pk=active_company_id, active=True).first()
            configured_services = OrganizationServiceSubscription.objects.filter(
                organization=org,
            ).values_list('service_code', flat=True)
            # Sem nenhuma configuração ainda, preserve o menu para o onboarding.
            # Depois que o administrador define o padrão, cada item de serviço
            # passa a obedecer ao catálogo ativo da organização.
            if configured_services.exists():
                active_services = {
                    code for code, _label in OrganizationServiceSubscription.SERVICE_CHOICES
                    if service_enabled(org, code, company=active_company)
                }

    for item in MENU_ITEMS:
        if area not in item["areas"]:
            continue
        # Service filtering: skip if not enabled, UNLESS user is staff/superuser
        if active_services is not None and item.get("service") and item["service"] not in active_services:
            if not (request.user.is_staff or request.user.is_superuser):
                continue
        if item.get("auth") and not request.user.is_authenticated:
            continue
        if item.get("staff") and not can_manage_console:
            continue
        if item.get("superuser") and not request.user.is_superuser:
            continue

        # Create a copy to avoid modifying the original
        item = {**item}

        # Replace hierarchy labels with dynamic terminology
        if terminology and item.get("group") in ("hierarchy", "structure"):
            if item["url"] == "console:company_list":
                item["label"] = terminology.level_1_label
            elif item["url"] == "console:business_unit_list":
                item["label"] = terminology.level_2_label
            elif item["url"] == "console:operational_unit_list":
                item["label"] = terminology.level_3_label

        try:
            kwargs = {"pk": request.user.pk} if item["url"].endswith(("user_profile_detail", "user_gamification_points")) else {}
            href = reverse(item["url"], kwargs=kwargs)
            if item.get("query"):
                href = f"{href}?{item['query']}"
            item = {**item, "href": href}
            if item["url"].startswith("recruitment_public:"):
                item["target"] = "_blank"
                item["rel"] = "noopener noreferrer"
            path_matches = request.path == item["href"].split("?", 1)[0]
            expected_query = dict(parse_qsl(item.get("query", ""), keep_blank_values=True))
            current_query = {key: value for key, value in request.GET.items()}
            item["active"] = path_matches and expected_query == current_query
        except NoReverseMatch:
            continue
        items.append(item)
    return items


GROUPS = {
    "start": _("Início"),
    "content": _("Conteúdo"),
    "intelligence": _("Análises e auditoria"),
    "audience": _("Audiência"),
    "structure": _("Organização e estrutura"),
    "access": _("Gestão de pessoas e acessos"),
    "account": _("Conta"),
    "recruitment": _("MatchCo — Recrutamento"),
    "matchco_ops": _("Operação técnica"),
    "lgpd": _("LGPD"),
}

# Ordem top-down: primeiro a organização e sua hierarquia; depois os acessos;
# só então conteúdo, análises e operações técnicas.
GROUP_ORDER = (
    "structure", "access", "audience", "content",
    "recruitment", "intelligence", "lgpd", "matchco_ops", "account", "start",
)


def get_menu_groups(request, area):
    return group_menu_items(get_menu_items(request, area))


def group_menu_items(items):
    groups = []
    by_key = {}
    for item in items:
        key = item.get("group", "content")
        if key not in by_key:
            by_key[key] = {"key": key, "label": GROUPS.get(key, key), "items": []}
            groups.append(by_key[key])
        by_key[key]["items"].append(item)
        by_key[key]["active"] = by_key[key].get("active", False) or item.get("active", False)
    order = {key: index for index, key in enumerate(GROUP_ORDER)}
    return sorted(groups, key=lambda group: (order.get(group["key"], len(order)), str(group["label"])))
