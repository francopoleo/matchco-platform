# Progressive Growth Implementation Guide

**Versão**: 1.0  
**Data**: 2026-07-24  
**Objetivo**: Como implementar o sistema de "feature unlocking" automático no Talk

---

## 📖 VISÃO GERAL

### O Problema

Plataformas de Learning tradicionales (Docebo, SAP, Moodle) fracassam porque:
1. Dia 1: Sistema VAZIO ou POLUÍDO (pick one horror)
2. Admin é forçado a criar conteúdo enquanto usuários abandonam
3. Ciclo de implementação: 6+ meses
4. Adoption: 40-50% (resto desiste)

### A Solução

**Talk cresce conforme o cliente usa, não conforme você design.**

```
✅ Dia 1: Sistema funcional, limpo, útil (não vazio)
✅ Semana 2-3: Features despertam quando relevantes
✅ Mês 2: Sistema customizado pro cliente real
✅ Adoption: 85%+, ROI visível, cliente quer MAIS
```

---

## 🏗️ ARQUITETURA TÉCNICA

### Layer 1: Metrics Collection (Sempre Rodando)

```python
# talk/analytics/metrics_collector.py

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q
from datetime import timedelta
from django.utils import timezone

class MetricsCollector:
    """
    Coleta métricas de uso do cliente em tempo real.
    Essas métricas alimentam o sistema de feature unlocking.
    """
    
    def collect_organization_metrics(self, organization):
        """Coleta todas as métricas de uma organização"""
        
        now = timezone.now()
        one_week_ago = now - timedelta(days=7)
        
        metrics = {
            'organization_id': organization.id,
            'collection_date': now,
            
            # === DOCUMENTO METRICS ===
            'total_documents': organization.document_set.count(),
            'documents_uploaded_this_week': organization.document_set.filter(
                created_at__gte=one_week_ago
            ).count(),
            
            'total_document_views': organization.analytics_events.filter(
                event_type='document_viewed'
            ).count(),
            'document_views_this_week': organization.analytics_events.filter(
                event_type='document_viewed',
                timestamp__gte=one_week_ago
            ).count(),
            
            'total_document_downloads': organization.analytics_events.filter(
                event_type='document_downloaded'
            ).count(),
            'document_downloads_this_week': organization.analytics_events.filter(
                event_type='document_downloaded',
                timestamp__gte=one_week_ago
            ).count(),
            
            'doc_view_rate': self._calculate_doc_view_rate(organization),
            'doc_views_unique_users': self._calculate_unique_users(
                organization, 'document_viewed', one_week_ago
            ),
            
            # === SEARCH METRICS ===
            'search_queries_total': organization.analytics_events.filter(
                event_type='search_query'
            ).count(),
            'search_queries_this_week': organization.analytics_events.filter(
                event_type='search_query',
                timestamp__gte=one_week_ago
            ).count(),
            
            # === ENGAGEMENT METRICS ===
            'total_users': organization.user_set.count(),
            'active_users_this_week': organization.analytics_events.filter(
                timestamp__gte=one_week_ago
            ).values('user').distinct().count(),
            'active_users_this_month': organization.analytics_events.filter(
                timestamp__gte=now - timedelta(days=30)
            ).values('user').distinct().count(),
            
            'user_login_count_this_week': organization.analytics_events.filter(
                event_type='user_login',
                timestamp__gte=one_week_ago
            ).count(),
            
            'engagement_score': self._calculate_engagement_score(organization),
            
            # === DEVICE METRICS ===
            'mobile_traffic_ratio': self._calculate_mobile_ratio(organization),
            
            # === FEEDBACK/COMMUNICATION ===
            'feedback_messages_this_week': organization.notification_set.filter(
                created_at__gte=one_week_ago
            ).count(),
            'support_tickets_this_week': organization.support_ticket_set.filter(
                created_at__gte=one_week_ago
            ).count(),
            
            # === COMPLIANCE ===
            'has_compliance_tracking_requests': self._has_compliance_requests(organization),
            'compliance_check_count': organization.compliance_check_set.count(),
            
            # === INTEGRATION ===
            'integration_requests_count': organization.integration_request_set.filter(
                status='pending'
            ).count(),
            
            # === COURSE METRICS (se temos learning) ===
            'courses_assigned': organization.course_set.count(),
            'courses_completed_this_week': organization.analytics_events.filter(
                event_type='course_completed',
                timestamp__gte=one_week_ago
            ).count(),
            
            # === DAYS ACTIVE ===
            'days_since_activation': (now - organization.created_at).days,
        }
        
        return metrics
    
    def _calculate_doc_view_rate(self, org):
        """
        Porcentagem de documentos que foram visualizados pelo menos 1x
        Se 80% dos docs foram vistos, = 0.8
        """
        total_docs = org.document_set.count()
        if total_docs == 0:
            return 0.0
        
        viewed_docs = org.document_set.filter(
            document_view__isnull=False
        ).distinct().count()
        
        return viewed_docs / total_docs
    
    def _calculate_engagement_score(self, org):
        """
        Score de 0-1 baseado em vários fatores:
        - Frequência de login
        - Documentos visualizados
        - Tempo gasto
        - Participação (feedback, comments)
        """
        logins = org.analytics_events.filter(
            event_type='user_login',
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        views = org.analytics_events.filter(
            event_type='document_viewed',
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        feedback = org.notification_set.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Score: (logins + views + feedback*2) / max_score
        score = min((logins + views + feedback*2) / 100, 1.0)
        return score
    
    def _calculate_mobile_ratio(self, org):
        """Porcentagem de traffic que vem de mobile"""
        total_requests = org.analytics_events.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if total_requests == 0:
            return 0.0
        
        mobile_requests = org.analytics_events.filter(
            timestamp__gte=timezone.now() - timedelta(days=7),
            properties__device_type='mobile'  # Assume isso no event
        ).count()
        
        return mobile_requests / total_requests
    
    def _calculate_unique_users(self, org, event_type, since):
        """Quantos usuários diferentes fizeram uma ação"""
        return org.analytics_events.filter(
            event_type=event_type,
            timestamp__gte=since
        ).values('user_id').distinct().count()
    
    def _has_compliance_requests(self, org):
        """Check se o cliente mencionou compliance em algum lugar"""
        # Opção 1: Marcado explicitamente no org
        if org.compliance_required:
            return True
        
        # Opção 2: Palavra "compliance" em feedbacks/suporte
        from django.db.models import Q
        has_mention = org.support_ticket_set.filter(
            Q(description__icontains='compliance') |
            Q(description__icontains='auditoria') |
            Q(description__icontains='conformidade')
        ).exists()
        
        return has_mention
```

### Layer 2: Feature Unlock Rules Engine

```python
# talk/features/unlock_rules.py

from enum import Enum
from dataclasses import dataclass
from typing import Callable, List

class FeatureTier(Enum):
    BASIC = 'basic'           # Sempre incluído
    GROWTH = 'growth'         # Desbloqueia conforme uso
    ENTERPRISE = 'enterprise' # Premium features

@dataclass
class UnlockRule:
    feature_name: str
    tier: FeatureTier
    trigger: Callable  # lambda que toma 'metrics' e retorna bool
    unlock_message: str
    additional_monthly_cost: int  # Em cents
    deploy_sprint: int  # Quando fica pronto pra desbloquear
    
    def should_unlock(self, metrics: dict) -> bool:
        """Checa se trigger é ativado"""
        try:
            return self.trigger(metrics)
        except Exception as e:
            print(f"Error evaluating trigger for {self.feature_name}: {e}")
            return False

# Registry de todas as features que podem ser desbloqueadas
FEATURE_UNLOCK_REGISTRY = [
    UnlockRule(
        feature_name='analytics_dashboard',
        tier=FeatureTier.GROWTH,
        trigger=lambda m: m['doc_view_rate'] > 0.5,
        unlock_message='Analytics dashboard disponível - seus documentos estão sendo lidos!',
        additional_monthly_cost=30000,  # $300
        deploy_sprint=3
    ),
    
    UnlockRule(
        feature_name='advanced_search',
        tier=FeatureTier.GROWTH,
        trigger=lambda m: m['search_queries_this_week'] > 20,
        unlock_message='Pesquisa avançada em PDFs agora disponível!',
        additional_monthly_cost=0,  # Grátis
        deploy_sprint=3
    ),
    
    UnlockRule(
        feature_name='compliance_dashboard',
        tier=FeatureTier.ENTERPRISE,
        trigger=lambda m: m['has_compliance_tracking_requests'],
        unlock_message='Dashboard de compliance & auditoria disponível!',
        additional_monthly_cost=50000,  # $500
        deploy_sprint=4
    ),
    
    UnlockRule(
        feature_name='gamification',
        tier=FeatureTier.GROWTH,
        trigger=lambda m: m['engagement_score'] > 0.6 and m['days_since_activation'] > 14,
        unlock_message='Badges & leaderboards disponíveis para motivar sua equipe!',
        additional_monthly_cost=20000,  # $200
        deploy_sprint=6
    ),
    
    UnlockRule(
        feature_name='community_forums',
        tier=FeatureTier.GROWTH,
        trigger=lambda m: m['feedback_messages_this_week'] > 5,
        unlock_message='Comunidade & fóruns abertos para peer support!',
        additional_monthly_cost=20000,  # $200
        deploy_sprint=6
    ),
    
    UnlockRule(
        feature_name='mobile_app',
        tier=FeatureTier.ENTERPRISE,
        trigger=lambda m: m['mobile_traffic_ratio'] > 0.4,
        unlock_message='App mobile disponível para iOS/Android!',
        additional_monthly_cost=100000,  # $1000
        deploy_sprint=8
    ),
    
    UnlockRule(
        feature_name='api_access',
        tier=FeatureTier.ENTERPRISE,
        trigger=lambda m: m['integration_requests_count'] > 0,
        unlock_message='API REST & webhooks disponíveis!',
        additional_monthly_cost=50000,  # $500
        deploy_sprint=9
    ),
]

class FeatureUnlockEngine:
    """Engine que decide quais features desbloquear"""
    
    def __init__(self):
        self.registry = FEATURE_UNLOCK_REGISTRY
    
    def evaluate_organization(self, organization, metrics: dict) -> List[UnlockRule]:
        """
        Retorna lista de features que DEVERIAM ser desbloqueadas
        mas ainda não foram
        """
        unlockable = []
        
        for rule in self.registry:
            # Só considera features do Deploy Sprint atual+
            if rule.deploy_sprint > organization.current_sprint:
                continue
            
            # Se já tem a feature, skip
            if organization.has_feature(rule.feature_name):
                continue
            
            # Se trigger é ativado, pode desbloquear
            if rule.should_unlock(metrics):
                unlockable.append(rule)
        
        return unlockable
    
    def unlock_features(self, organization, unlockable_rules: List[UnlockRule]):
        """Aplica os unlocks"""
        for rule in unlockable_rules:
            # 1. Enable feature
            organization.add_feature(rule.feature_name)
            
            # 2. Notify admin
            self._notify_admin(organization, rule)
            
            # 3. Update billing
            self._update_billing(organization, rule)
            
            # 4. Log adoption journey
            self._log_milestone(organization, rule)
    
    def _notify_admin(self, org, rule: UnlockRule):
        """Enviar email ao admin sobre novo feature"""
        from django.core.mail import send_mail
        
        admin_email = org.admin_users.first().email
        
        email_html = f"""
        <h2>New feature available: {rule.feature_name}</h2>
        <p>{rule.unlock_message}</p>
        <p>Cost: ${rule.additional_monthly_cost / 100:.2f}/month</p>
        <a href="https://talk.app/console/features/{rule.feature_name}">View Feature</a>
        """
        
        send_mail(
            subject=f'New feature: {rule.feature_name}',
            message='',
            from_email='noreply@talk.app',
            recipient_list=[admin_email],
            html_message=email_html,
        )
    
    def _update_billing(self, org, rule: UnlockRule):
        """Adicionar custo mensal à subscription"""
        subscription = org.subscription
        subscription.add_feature_cost(
            feature=rule.feature_name,
            cost_cents=rule.additional_monthly_cost
        )
        subscription.save()
    
    def _log_milestone(self, org, rule: UnlockRule):
        """Log no adoption journey"""
        from talk.analytics.models import AdoptionMilestone
        
        AdoptionMilestone.objects.create(
            organization=org,
            milestone=f'feature_unlocked_{rule.feature_name}',
            reached_at=timezone.now(),
            details={
                'trigger_name': rule.feature_name,
                'cost': rule.additional_monthly_cost
            }
        )
```

### Layer 3: Scheduled Task (Roda Weekly)

```python
# talk/features/tasks.py

from celery import shared_task
from django.core.management.base import BaseCommand
from talk.features.unlock_rules import FeatureUnlockEngine
from talk.analytics.metrics_collector import MetricsCollector
from talk.organizations.models import Organization
from django.utils import timezone

@shared_task
def evaluate_and_unlock_features():
    """
    Roda toda semana (ou todo dia) para:
    1. Coletar métricas de cada org
    2. Checar quais features deveriam desbloquear
    3. Desbloquear automatically se trigger ativado
    """
    
    engine = FeatureUnlockEngine()
    collector = MetricsCollector()
    
    for org in Organization.objects.filter(is_active=True):
        try:
            # Collect metrics
            metrics = collector.collect_organization_metrics(org)
            
            # Evaluate which features should unlock
            unlockable = engine.evaluate_organization(org, metrics)
            
            # Unlock them
            if unlockable:
                engine.unlock_features(org, unlockable)
                print(f"[{org.name}] Unlocked {len(unlockable)} features")
            
            # Save metrics pra analytics
            org.save_metrics_snapshot(metrics)
            
        except Exception as e:
            print(f"Error processing org {org.id}: {e}")
            # Log to Sentry/monitoring
            raise

# Management command para rodar manual
class Command(BaseCommand):
    help = 'Evaluate and unlock features based on metrics'
    
    def handle(self, *args, **options):
        evaluate_and_unlock_features()
        self.stdout.write("Done!")

# Setup no settings.py:
# CELERY_BEAT_SCHEDULE = {
#     'evaluate-feature-unlocks': {
#         'task': 'talk.features.tasks.evaluate_and_unlock_features',
#         'schedule': crontab(minute=0, hour=0),  # Daily at midnight
#     },
# }
```

### Layer 4: Feature Flag Frontend

```python
# talk/features/middleware.py

class FeatureFlagMiddleware:
    """
    Adiciona organization.features_available no context de cada request
    pra templates saber quais features mostrar
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            org = request.user.organization
            
            # Cacheado por 5 min pra performance
            cache_key = f"features_{org.id}"
            features = cache.get(cache_key)
            
            if features is None:
                features = {
                    f.feature_name: True
                    for f in org.organizationfeature_set.filter(enabled=True)
                }
                cache.set(cache_key, features, 300)
            
            request.features_available = features
        
        response = self.get_response(request)
        return response

# Template tag
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def has_feature(context, feature_name):
    """
    Em template: {% if "analytics"|has_feature %}
    """
    request = context['request']
    return request.features_available.get(feature_name, False)
```

---

## 📱 UI ADAPTATION BASED ON ADOPTION SCORE

```python
# talk/ui/adoption_levels.py

from enum import Enum

class AdoptionLevel(Enum):
    ONBOARDING = (0, 0.2)      # Dia 1-3
    DISCOVERY = (0.2, 0.6)     # Semana 1-2
    PRODUCTIVE = (0.6, 0.85)   # Semana 3-4
    POWER_USER = (0.85, 1.0)   # Mês 2+

def get_adoption_level(organization) -> AdoptionLevel:
    """Calcula nível de adoção da org"""
    score = organization.adoption_score
    
    for level in AdoptionLevel:
        min_score, max_score = level.value
        if min_score <= score < max_score:
            return level
    
    return AdoptionLevel.POWER_USER

# Template context
class DashboardView(TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        
        adoption_level = get_adoption_level(org)
        
        context['adoption_level'] = adoption_level.name
        context['show_sidebar'] = adoption_level.value[0] >= 0.2
        context['show_advanced_analytics'] = adoption_level.value[0] >= 0.6
        context['show_community'] = adoption_level.value[0] >= 0.85
        
        return context
```

---

## 🔄 METRICS DATABASE SCHEMA

```sql
-- Armazenar métricas coletadas periodicamente
CREATE TABLE organization_metrics_snapshot (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    snapshot_date DATE NOT NULL,
    
    -- Document metrics
    total_documents INT,
    documents_uploaded_this_week INT,
    total_document_views INT,
    document_views_this_week INT,
    total_document_downloads INT,
    document_downloads_this_week INT,
    doc_view_rate DECIMAL(3, 2),  -- 0.00 to 1.00
    doc_views_unique_users INT,
    
    -- Search metrics
    search_queries_total INT,
    search_queries_this_week INT,
    
    -- Engagement metrics
    total_users INT,
    active_users_this_week INT,
    active_users_this_month INT,
    user_login_count_this_week INT,
    engagement_score DECIMAL(3, 2),
    
    -- Device metrics
    mobile_traffic_ratio DECIMAL(3, 2),
    
    -- Feedback metrics
    feedback_messages_this_week INT,
    support_tickets_this_week INT,
    
    -- Compliance
    has_compliance_tracking_requests BOOLEAN,
    compliance_check_count INT,
    
    -- Integration
    integration_requests_count INT,
    
    -- Course metrics
    courses_assigned INT,
    courses_completed_this_week INT,
    
    -- Lifecycle
    days_since_activation INT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, snapshot_date)
);

-- Feature unlock history
CREATE TABLE feature_unlock_history (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    feature_name VARCHAR(100) NOT NULL,
    
    trigger_metric VARCHAR(100),  -- "doc_view_rate > 0.5"
    unlocked_at TIMESTAMP DEFAULT NOW(),
    
    unlock_reason VARCHAR(200),
    additional_cost_cents INT,
    
    INDEX idx_org_date (organization_id, unlocked_at)
);

-- Adoption journey milestones
CREATE TABLE adoption_milestones (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    milestone VARCHAR(100),  -- "first_login", "first_document_view", "feature_unlocked_analytics"
    reached_at TIMESTAMP,
    days_to_milestone INT,  -- Dias até atingir esse milestone
    
    details JSONB,  -- Extra context
    
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_org_milestone (organization_id, milestone)
);
```

---

## 🎯 TESTING PROGRESSIVE GROWTH

```python
# tests/test_feature_unlocks.py

from django.test import TestCase
from talk.features.unlock_rules import FeatureUnlockEngine, FEATURE_UNLOCK_REGISTRY
from talk.analytics.metrics_collector import MetricsCollector

class ProgressiveGrowthTestCase(TestCase):
    
    def setUp(self):
        self.org = OrganizationFactory()
        self.engine = FeatureUnlockEngine()
        self.collector = MetricsCollector()
    
    def test_analytics_unlocks_when_doc_view_rate_high(self):
        """Analytics desbloqueia quando >50% dos docs foram vistos"""
        
        # Setup: 10 docs, 6 foram vistos
        DocumentFactory.create_batch(10, organization=self.org)
        viewed_docs = self.org.document_set.all()[:6]
        
        for doc in viewed_docs:
            AnalyticsEventFactory(
                organization=self.org,
                event_type='document_viewed',
                object=doc
            )
        
        # Collect metrics
        metrics = self.collector.collect_organization_metrics(self.org)
        self.assertGreater(metrics['doc_view_rate'], 0.5)
        
        # Check unlock
        unlockable = self.engine.evaluate_organization(self.org, metrics)
        analytics_rule = [r for r in unlockable if r.feature_name == 'analytics_dashboard']
        self.assertTrue(analytics_rule)
    
    def test_advanced_search_unlocks_when_search_queries_high(self):
        """Advanced search desbloqueia quando >20 buscas por semana"""
        
        # Setup: 25 search events
        for i in range(25):
            AnalyticsEventFactory(
                organization=self.org,
                event_type='search_query'
            )
        
        metrics = self.collector.collect_organization_metrics(self.org)
        self.assertGreater(metrics['search_queries_this_week'], 20)
        
        unlockable = self.engine.evaluate_organization(self.org, metrics)
        search_rule = [r for r in unlockable if r.feature_name == 'advanced_search']
        self.assertTrue(search_rule)
    
    def test_mobile_app_unlocks_when_mobile_traffic_high(self):
        """Mobile app desbloqueia quando >40% traffic é mobile"""
        
        # Setup: 60 mobile, 40 desktop
        for i in range(60):
            AnalyticsEventFactory(
                organization=self.org,
                event_type='document_viewed',
                properties={'device_type': 'mobile'}
            )
        
        for i in range(40):
            AnalyticsEventFactory(
                organization=self.org,
                event_type='document_viewed',
                properties={'device_type': 'desktop'}
            )
        
        metrics = self.collector.collect_organization_metrics(self.org)
        self.assertGreater(metrics['mobile_traffic_ratio'], 0.4)
        
        unlockable = self.engine.evaluate_organization(self.org, metrics)
        mobile_rule = [r for r in unlockable if r.feature_name == 'mobile_app']
        self.assertTrue(mobile_rule)
    
    def test_no_double_unlock(self):
        """Feature não desbloqueia duas vezes"""
        
        # Primeiro unlock
        self.org.add_feature('analytics_dashboard')
        
        # Setup metrics pra trigger
        AnalyticsEventFactory.create_batch(10, organization=self.org, event_type='document_viewed')
        metrics = self.collector.collect_organization_metrics(self.org)
        
        # Checar que não é retornado como desbloqueável
        unlockable = self.engine.evaluate_organization(self.org, metrics)
        analytics_rules = [r for r in unlockable if r.feature_name == 'analytics_dashboard']
        self.assertEqual(len(analytics_rules), 0)
```

---

## 📊 MONITORING & OBSERVABILITY

```python
# talk/monitoring/progressive_growth_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Métricas Prometheus pra observar Progressive Growth

features_unlocked_total = Counter(
    'features_unlocked_total',
    'Total features unlocked',
    ['feature_name', 'organization_id']
)

feature_unlock_latency = Histogram(
    'feature_unlock_latency_seconds',
    'Time from trigger condition to unlock',
    ['feature_name']
)

adoption_score = Gauge(
    'adoption_score',
    'Current adoption score',
    ['organization_id']
)

engagement_score = Gauge(
    'engagement_score',
    'Current engagement score',
    ['organization_id']
)

def log_unlock_event(rule, org):
    """Log quando feature é desbloqueada"""
    features_unlocked_total.labels(
        feature_name=rule.feature_name,
        organization_id=org.id
    ).inc()
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Metrics collector funcionando (daily/hourly)
- [ ] Feature unlock rules estão definidas
- [ ] Celery task agendado pra rodar weekly
- [ ] Email notifications configuradas
- [ ] Billing automático testado
- [ ] Feature flags no frontend testadas
- [ ] Database migrations executadas
- [ ] Adoption score calculation validado
- [ ] Monitoring/alerting ativo
- [ ] Testes unitários passando (>90% coverage)

---

**Progressive Growth torna Talk diferente. Não é complexo, é elegante.**
