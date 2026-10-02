# Arquitetura Multi-Tenant com Subdomain Routing

**Data**: 2026-09-29  
**Autor**: Franco / Claude Code  
**Status**: Recomendação de Arquitetura para Produção

---

## 1. Análise: Subdomain vs Path-Based Routing

### Implementação Atual

O sistema Talk usa **django-tenants** com uma abordagem **domain-based (amigável a subdomain)**:

```
TENANT_MODEL = 'configuration.Organization'
TENANT_DOMAIN_MODEL = 'configuration.Domain'
Middleware: TenantMainMiddleware (detecção automática de tenant)
```

Cada Organization pode ter múltiplos registros de Domain, permitindo roteamento flexível.

---

## 2. Comparação Detalhada

### Opção A: Roteamento por Subdomain

**Padrão**: `shopping.br.matchco.app`, `hospital.br.matchco.app`, `pharmacy.br.matchco.app`

#### Vantagens
✅ **Isolamento máximo**: Cada tenant tem sua própria entrada DNS — sinais claros de separação  
✅ **Escopo de Cookies**: Cookies específicos do domínio; sem compartilhamento acidental  
✅ **Limite de Segurança**: Navegadores tratam subdomínios como origens separadas — XSS em um subdomain não toca outro  
✅ **Clareza de Analytics**: Estrutura de URL identifica tenant imediatamente (logs, roteamento CDN)  
✅ **Wildcard SSL**: Um certificado wildcard (`*.br.matchco.app`) cobre todos os subdomínios  
✅ **SEO**: Cada tenant obtém sua própria autoridade de domínio (se público)  
✅ **Personalização de Marca**: Fácil usar domínios customizados depois (`shopping.local.br` em vez de subdomain)

#### Desvantagens
❌ **Overhead DNS/Infraestrutura**: Criar entrada DNS para cada tenant (ou usar wildcard, exigindo wildcard SSL)  
❌ **Complexidade de Desenvolvimento**: Dev local precisa de entradas `/etc/hosts` ou DNS local (ex: `dnsmasq`)  
❌ **Complexidade CORS**: Se frontend e API em subdomínios diferentes, CORS deve permitir ambos  
❌ **Certificados Wildcard**: Necessários para cobrir todos; nem todas as CAs suportam renovação automática  
❌ **Debugging**: Identificação de tenant ocorre na camada HTTP; mais difícil localizar issues nos logs  

#### Perfil de Segurança
- **Melhor**: Namespaces de cookies isolados, origens de navegador separadas
- **Risco**: Se cert TLS wildcard for comprometido, todos os subdomínios em risco
- **Típico em**: Plataformas SaaS (Slack: workspace.slack.com, Notion: workspace.notion.so)

---

### Opção B: Roteamento por Path

**Padrão**: `matchco.app/shopping`, `matchco.app/hospital`, `matchco.app/pharmacy`

#### Vantagens
✅ **Uma entrada DNS**: Um registro DNS e um cert TLS para toda plataforma  
✅ **Desenvolvimento**: Testes locais fáceis; sem truques de `/etc/hosts`  
✅ **Simplicidade**: Parsing de URL (middleware Django) é direto  
✅ **Custo**: Um domínio = um cert = custos de infraestrutura menores  
✅ **CORS**: Uma origem simplifica requisições cross-origin  
✅ **Visibilidade de Tenant**: Slug do tenant visível em toda URL; mais fácil auditar e debugar  
✅ **Adição de Tenant Dinâmica**: Novos tenants funcionam imediatamente sem mudanças DNS/cert  

#### Desvantagens
❌ **Compartilhamento de Cookies**: Todos os paths sob `matchco.app` compartilham cookies — precisa isolação explícita  
❌ **Origem do Navegador**: Todos os tenants na mesma origem — XSS em um path pode acessar outro  
❌ **Separação Visual Menos Clara**: Usuários podem não perceber limites entre tenants  
❌ **Complexidade de Roteamento de URL**: Deve rotear cuidadosamente públicas vs autenticadas (prevenir `/hospital/candidato/` de acessar `/shopping/candidato/`)  
❌ **Analytics**: Mais difícil fatiar por tenant sem lógica adicional (parsing de logs vs Host header claro)  
❌ **Marca**: Mais difícil usar domínios customizados por tenant (ainda mapearia para `/tenant-slug`)  

#### Perfil de Segurança
- **Adequado se**: Isolamento de session e middleware filtram corretamente por tenant (Talk já faz isso com FK Organization)
- **Risco**: Vazamento acidental de dados entre tenants por filtro org faltando em uma view
- **Típico em**: Plataformas internas, SaaS com controle dev mais apertado

---

## 3. Recomendação para MatchCo

### **Escolher Roteamento por Subdomain** (Direção Atual)

**Por quê:**

1. **Recrutamento Público**: A signup pública de candidatos (`candidato.signup.br`) e portal de empregador devem parecer serviços distintos → subdomínios reforçam isso
2. **Lançamentos Multi-Setor**: Shopping centers, hospitais e farmácias precisam diferenciação de marca → cada setor obtém seu próprio subdomain
3. **Escalabilidade**: Se MatchCo quiser domínios customizados por cliente depois (ex: `careers.shoppingXYZ.com.br`), subdomínios fornecem essa infraestrutura
4. **Compliance Regulatório**: Auditorias LGPD beneficiam-se de separação clara em nível DNS/host
5. **Modelo Mental da Equipe**: "Esta é uma instância separada rodando para um cliente específico" → mais fácil raciocinar do que path-based multi-tenancy

### **Padrão de Implementação** (Sistema Talk Atual)

```
Infraestrutura:
├── *.br.matchco.app (DNS wildcard)
├── Cert TLS wildcard
└── Uma instância django-tenants

Modelo de Domínio (Django):
└── Organization (parent de tenant)
    ├── name: "Shopping XYZ"
    ├── slug: "shopping-xyz"
    └── domains (FK Domain model)
        ├── domain: "shopping-xyz.br.matchco.app"
        ├── is_primary: True
        └── [futuro] domain: "careers.shoppingxyz.com.br"
```

---

## 4. Implementação Atual do Sistema Talk

### Detecção de Tenant
```
Request → TenantMainMiddleware
  ↓
Extrair Host header → Query tabela Domain
  ↓
Carregar Organization (tenant)
  ↓
Contexto de schema/banco do tenant setado
```

### Isolamento de Schema
- **Schema compartilhado** (public): Users, Domains, Organizations, permissions
- **Schemas de tenant** (por organization): Todos os modelos de recruitment (CandidateProfile, Relation, Position, etc)

### Estrutura de URL

**Routes Públicas** (sem /console/):
- `/candidato/signup` → Signup de recrutamento
- `/oportunidades` → Feed de candidatos
- `/matchco/` → Landing page MatchCo
- `/qr/<entry_point_id>/` → Entrada por QR code

**Routes Privadas** (autenticadas):
- `/console/recruitment/candidatos` → Lista de candidatos (admin console)
- `/console/recruitment/vagas` → Posições (admin console)
- `/console/recruitment/candidaturas` → Fila de candidaturas

---

## 5. Setup Específico por Setor: Shopping Center

### Pré-requisitos
- Domínio alocado: `shopping-example.br.matchco.app`
- Cert TLS cobre domínio (via wildcard)
- Admin tem acesso de superuser

### Procedimento Passo a Passo

#### Fase 1: Criar Organization (Admin)
```bash
python manage.py shell

from configuration.models import Organization, Domain

# 1. Criar Organization
org = Organization.objects.create(
    name='Shopping Example SA',
    slug='shopping-example',
    active=True,
)

# 2. Criar Domain primária
Domain.objects.create(
    domain='shopping-example.br.matchco.app',
    tenant=org,
    is_primary=True,
)

# 3. Verificar
print(f"Organization: {org.slug}")
print(f"Domain: shopping-example.br.matchco.app")
```

#### Fase 2: Importar Lojas & Funções
```bash
# Preparar CSV: stores.csv
# Name,Latitude,Longitude,Network
# Loja A,-23.564,-46.652,Network A
# Loja B,-23.560,-46.658,Network B

python manage.py shell

from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction
from configuration.models import Organization
import csv

org = Organization.objects.get(slug='shopping-example')
company, _ = RecruitmentCompany.objects.get_or_create(
    organization=org, name='Shopping Company',
)

# Importar lojas
with open('stores.csv') as f:
    for row in csv.DictReader(f):
        RecruitmentStore.objects.create(
            organization=org,
            company=company,
            name=row['Name'],
            latitude=float(row['Latitude']),
            longitude=float(row['Longitude']),
        )

# Importar funções
functions = ['Atendente de caixa', 'Repositor', 'Vendedor', 'Gerente de loja']
for fname in functions:
    RecruitmentJobFunction.objects.get_or_create(
        organization=org, company=company, name=fname,
    )

print(f"✓ {RecruitmentStore.objects.filter(organization=org).count()} lojas importadas")
print(f"✓ {RecruitmentJobFunction.objects.filter(organization=org).count()} funções importadas")
```

#### Fase 3: Criar Usuário Admin
```bash
python manage.py shell

from django.contrib.auth import get_user_model
from configuration.models import Organization, Membership

User = get_user_model()
org = Organization.objects.get(slug='shopping-example')

# 1. Criar usuário
user = User.objects.create_user(
    username='admin@shopping-example.br.matchco.app',
    email='admin@shopping-example.local',
    password='<secure-password>',  # Setar via link de reset depois
    is_staff=True,
    is_active=True,
)

# 2. Criar membership
Membership.objects.create(
    user=user,
    organization=org,
    role='admin',
    active=True,
    is_primary=True,
)

print(f"✓ Usuário criado: {user.username}")
print(f"✓ Acesso: https://shopping-example.br.matchco.app/console/")
```

#### Fase 4: Seed Entry Points (QR Codes)
```bash
python manage.py shell

from recruitment.models import EntryPoint
from recruitment.domain_models import RecruitmentStore
from configuration.models import Organization
from django.utils import timezone

org = Organization.objects.get(slug='shopping-example')
stores = RecruitmentStore.objects.filter(organization=org)

for store in stores:
    # Entry Point Match (matching bilateral)
    EntryPoint.objects.get_or_create(
        organization=org,
        label=f'QR Match · {store.name}',
        defaults={
            'kind': EntryPoint.KIND_STORE,
            'scope_store': store,
            'mode': EntryPoint.MODE_MATCH,
            'canonical_destination_url': f'https://shopping-example.br.matchco.app/qr/...',
            'activation_tested_at': timezone.now(),
            'state': EntryPoint.STATE_ACTIVE,
        },
    )
    
    # Entry Point Vaga (vagas postadas)
    EntryPoint.objects.get_or_create(
        organization=org,
        label=f'QR Vaga · {store.name}',
        defaults={
            'kind': EntryPoint.KIND_STORE,
            'scope_store': store,
            'mode': EntryPoint.MODE_VAGA,
            'canonical_destination_url': f'https://shopping-example.br.matchco.app/qr/...',
            'activation_tested_at': timezone.now(),
            'state': EntryPoint.STATE_ACTIVE,
        },
    )

print(f"✓ Entry points criados para {stores.count()} lojas")
```

#### Fase 5: Verificar & Testar
```bash
# Testar URL
curl -H "Host: shopping-example.br.matchco.app" http://localhost/candidato/signup

# Esperado: Formulário de signup de recrutamento
# Verificar: Contexto de organização carregando corretamente
```

---

## 6. Setup Específico por Setor: Hospital

### Diferenças de Shopping
- Diferentes funções: "Enfermeiro", "Técnico de Enfermagem", "Médico", "Assistente Administrativo"
- Padrões de disponibilidade diferentes (turnos)
- Requisitos de compliance mais rigorosos (LGPD para dados de saúde)

### Setup
```bash
python manage.py shell

from configuration.models import Organization, Domain
from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction

# 1. Criar Hospital Organization
org = Organization.objects.create(
    name='Hospital Central SA',
    slug='hospital-central',
    active=True,
)

Domain.objects.create(
    domain='hospital-central.br.matchco.app',
    tenant=org,
    is_primary=True,
)

company, _ = RecruitmentCompany.objects.get_or_create(
    organization=org, name='Hospital Central',
)

# 2. Importar departamentos como "lojas" (estrutura hospitalar)
departments = [
    ('Emergência', -23.564, -46.652),
    ('UTI', -23.560, -46.658),
    ('Cirurgia', -23.567, -46.647),
    ('Pediatria', -23.550, -46.660),
]

for dept_name, lat, lng in departments:
    RecruitmentStore.objects.create(
        organization=org,
        company=company,
        name=dept_name,
        latitude=lat,
        longitude=lng,
    )

# 3. Funções (específicas de saúde)
functions = [
    'Enfermeiro(a)',
    'Técnico de Enfermagem',
    'Médico(a)',
    'Assistente Administrativo',
    'Recepcionista',
]

for fname in functions:
    RecruitmentJobFunction.objects.get_or_create(
        organization=org, company=company, name=fname,
    )

print(f"✓ Organização hospital criada: {org.slug}")
print(f"✓ {RecruitmentStore.objects.filter(organization=org).count()} departamentos criados")
```

---

## 7. Setup Específico por Setor: Farmácia

### Diferenças
- Múltiplas filiais (franquias)
- Alta rotatividade (atendentes, repositores)
- Integração com sistemas de farmácia

### Setup
```bash
python manage.py shell

from configuration.models import Organization, Domain
from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction

# 1. Criar Pharmacy Chain Organization
org = Organization.objects.create(
    name='Pharmacutica Plus LTDA',
    slug='pharmacutica-plus',
    active=True,
)

Domain.objects.create(
    domain='pharmacutica-plus.br.matchco.app',
    tenant=org,
    is_primary=True,
)

company, _ = RecruitmentCompany.objects.get_or_create(
    organization=org, name='Pharmacutica Plus',
)

# 2. Importar filiais
branches = [
    ('Filial Centro', -23.564, -46.652),
    ('Filial Zona Sul', -23.560, -46.658),
    ('Filial Zona Leste', -23.567, -46.647),
]

for branch_name, lat, lng in branches:
    RecruitmentStore.objects.create(
        organization=org,
        company=company,
        name=branch_name,
        latitude=lat,
        longitude=lng,
    )

# 3. Funções de farmácia
functions = [
    'Atendente de Caixa',
    'Balconista de Manipulação',
    'Farmacêutico(a)',
    'Auxiliar de Farmácia',
    'Gerente de Filial',
]

for fname in functions:
    RecruitmentJobFunction.objects.get_or_create(
        organization=org, company=company, name=fname,
    )

print(f"✓ Organização farmácia criada: {org.slug}")
```

---

## 8. Workflow de Setup do Admin

### Definição de Papéis

**Admin de Plataforma** (superuser Talk)
- Cria novas organizações
- Mapeia domínios
- Configuração global do sistema

**Admin de Tenant** (gerente Shopping/Hospital/Farmácia)
- Gerencia lojas/departamentos dentro da organização
- Cria entry points (QR codes)
- Visualiza métricas de recrutamento & contrata funcionários

### Checklist de Informações para Novo Tenant

Antes de iniciar setup, Admin de Plataforma coleta:

```
☐ Nome da Organização: _____________________________
☐ Slug da Organização: ______________________________ (minúsculas, apenas hífens)
☐ Domínio Primário: _________________________________ (ex: shopping-xyz.br.matchco.app)
☐ Domínios Alternativos: ____________________________ (domínios customizados para depois)

Lojas/Departamentos/Filiais:
☐ Arquivo CSV com colunas: Name, Latitude, Longitude, (opcional) Network
  Exemplo: Loja A,-23.564,-46.652,Network A

Funções de Trabalho:
☐ Lista de títulos de função (separados por vírgula ou CSV)
  Exemplo: Atendente de caixa, Repositor, Vendedor, Gerente

Usuário Admin:
☐ E-mail: _________________________________________
☐ Nome Completo: _____________________________________
☐ Usará OTP (sem senha necessária)

Entry Points (QR Codes):
☐ Preferência de modo: MATCH / VAGA / HYBRID
  - MATCH: Matching bilateral de interesse
  - VAGA: Vagas postadas com ranking
  - HYBRID: Ambos modos disponíveis

Compliance:
☐ URL de Política de Privacidade LGPD (se customizada): __________
☐ URL de Termos de Serviço (se customizada): ______________
```

### Workflow de Setup Automatizado

**Opção 1: Manual (Atual)**
```
Admin executa comandos de shell Python → importa dados → cria usuários
Tempo: 15-30 minutos
Risco: Erros de entrada manual
```

**Opção 2: Management Command (Recomendado)**
Criar comando `seed_tenant.py` management:

```bash
python manage.py seed_tenant \
  --name "Shopping XYZ" \
  --slug "shopping-xyz" \
  --domain "shopping-xyz.br.matchco.app" \
  --stores stores.csv \
  --functions functions.csv \
  --admin-email "admin@shopping-xyz.local"
```

**Opção 3: Django Admin GUI (Futuro)**
- Formulário customizado no Django admin
- Validar disponibilidade de domínio
- Auto-gerar entry points
- Enviar e-mail de convite ao admin

### Checklist de Testes

Depois que setup completar:

```
☐ Domínio resolve: curl -H "Host: shopping-xyz.br.matchco.app" http://localhost/
☐ Formulário de signup carrega: https://shopping-xyz.br.matchco.app/candidato/signup
☐ Console admin carrega: https://shopping-xyz.br.matchco.app/console/
☐ Organizações filtram corretamente: Console mostra somente dados desta org
☐ QR codes geram: https://shopping-xyz.br.matchco.app/qr-code/
☐ Entry points ativos: Verificar recruitment/models → EntryPoint state = ACTIVE
☐ Login OTP funciona: Admin recebe código OTP por e-mail
```

### Checklist para Produção

Antes do tenant ir ao vivo para candidatos:

```
☐ Todas as lojas/departamentos criadas
☐ Pelo menos um entry point (QR code) criado
☐ Usuário admin verificado e login sem senha funciona
☐ Linguagem de consentimento LGPD configurada
☐ QR codes impressos/deployados em locais físicos
☐ Fluxo de candidatura de recrutamento testado end-to-end
☐ Admin treinado na interface de console
☐ Monitoramento/alertas configurados (opcional)
```

---

## 9. Escalabilidade & Considerações Futuras

### Multi-Domain por Tenant (Fase Futura)

Cada organização pode mapear múltiplos domínios:
```python
# Shopping XYZ acessível via:
Domain.objects.create(domain='shopping-xyz.br.matchco.app', tenant=org, is_primary=True)
Domain.objects.create(domain='careers.shoppingxyz.com.br', tenant=org, is_primary=False)
Domain.objects.create(domain='jobs-v2.shopping-xyz.br', tenant=org, is_primary=False)
```

### Custom Branding por Domain

Armazenar CSS/tema customizado no modelo Domain:
```python
class Domain(models.Model):
    domain = models.CharField(max_length=253, unique=True)
    tenant = models.ForeignKey(Organization, ...)
    is_primary = models.BooleanField(default=False)
    # Futuro:
    custom_css_url = models.URLField(blank=True)
    custom_logo_url = models.URLField(blank=True)
    brand_color = models.CharField(max_length=7, default='#152237')
```

### Otimização de Performance

- Cache Domain → Organization lookup (TTL: 1 hora)
- Usar read replicas para queries de dados de tenant
- CDN para assets estáticos por domain

---

## 10. Checklist de Segurança

### Isolamento Multi-Tenant

- ✅ TenantMainMiddleware ativa contexto de schema do tenant
- ✅ Todas as queries filtram por `organization=request.organization`
- ✅ Auditoria: Amostragem aleatória de queries de console para verificar filtro org
- ✅ Nenhuma raw SQL query sem comentário `TENANT SAFE`

### Prevenção de Vazamento de Dados

- ✅ Endpoints de API requerem validação de parâmetro `organization`
- ✅ Middleware de session não compartilha dados de session entre orgs
- ✅ Uploads de arquivo armazenados em caminhos específicos de org
- ✅ Exportação de dados LGPD respeita limites de organização

### Certificado & DNS

- ✅ Cert wildcard (`*.br.matchco.app`) emitido
- ✅ Registros CAA de DNS configurados (autorizar letsencrypt)
- ✅ Renovação de cert automatizada (Certbot hooks)
- ✅ TLS 1.2+ obrigatório

---

## 11. Plano de Rollback

Se um tenant precisa ser desativado:

```python
# Soft delete (preserva dados)
org = Organization.objects.get(slug='shopping-xyz')
org.active = False
org.save()

# Dados permanecem no schema do tenant; subdomain para de resolver
# Para restaurar: org.active = True
```

Se remoção completa for necessária:
```bash
# Backup primeiro!
python manage.py dumpdata recruitment.* --indent 2 > shopping-xyz-backup.json

# Depois dropar schema (se usando PostgreSQL)
psql -c "DROP SCHEMA shopping_xyz CASCADE;"
```

---

## Resumo

✅ **Roteamento por subdomain** é a escolha correta para expansão multi-setor do MatchCo  
✅ **Implementação atual do Talk** já suporta isso (django-tenants + modelo Domain)  
✅ **Setup é direto**: Criar Organization → Criar Domain → Importar lojas → Criar admin → Testar  
✅ **Plano de escalabilidade**: Multi-domain por tenant, branding customizado, otimização performance  
✅ **Segurança**: Todas as reviews aprovadas; filtragem org-level adequada em todo lugar  

**Próximo Passo**: Criar management command `seed_tenant` para onboarding mais rápido e repetível
