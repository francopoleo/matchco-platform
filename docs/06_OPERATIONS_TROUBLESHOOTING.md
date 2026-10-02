# Troubleshooting & Problemas Comuns - Operações

**Público**: Admins de plataforma, DevOps, suporte técnico  
**Última atualização**: 2026-10-02

---

## Problemas de Detecção de Tenant

### Domínio não resolve

**Sintomas**: 
- `curl: (6) Could not resolve host`
- 404 em todo subdomain

**Verificação**:
```bash
nslookup shopping-xyz.br.matchco.app
dig shopping-xyz.br.matchco.app

# Verificar wildcard
nslookup any-subdomain.br.matchco.app
```

**Soluções**:
1. **DNS wildcard não configurado**: Criar entrada wildcard no DNS
   ```bash
   # Exemplo (zona DNS):
   *.br.matchco.app  IN  A  <IP_DO_SERVIDOR>
   ```

2. **TTL expirado**: Aguardar propagação de DNS (até 48h)
   ```bash
   # Forçar refresh no /etc/hosts para testes locais:
   echo "127.0.0.1 shopping-xyz.br.matchco.app" >> /etc/hosts
   ```

3. **Certificado TLS incompatível**: Verificar wildcard cert
   ```bash
   # Testar SSL:
   openssl s_client -connect shopping-xyz.br.matchco.app:443 -showcerts
   ```

---

### 404 em `/candidato/signup`

**Sintomas**:
- URL resolve mas recebe 404
- Outras URLs também não funcionam

**Verificação**:
```bash
# 1. Verificar se TenantMainMiddleware está ativo
python manage.py shell
from django.conf import settings
print([m for m in settings.MIDDLEWARE if 'Tenant' in m])

# 2. Verificar se Domain existe
from configuration.models import Domain, Organization
d = Domain.objects.filter(domain='shopping-xyz.br.matchco.app')
print(d.exists())

# 3. Verificar Organization
if d.exists():
    org = d.first().tenant
    print(f"Org: {org.name}, slug: {org.slug}, active: {org.active}")
```

**Soluções**:
1. **TenantMainMiddleware não ativo**: Adicionar a `settings.py`
   ```python
   MIDDLEWARE = [
       # ...
       'django_tenants.middleware.main.TenantMainMiddleware',
       # ...
   ]
   ```

2. **Domain não existe**: Criar Domain via shell
   ```python
   from configuration.models import Organization, Domain
   org = Organization.objects.get(slug='shopping-xyz')
   Domain.objects.create(
       domain='shopping-xyz.br.matchco.app',
       tenant=org,
       is_primary=True,
   )
   ```

3. **Organization inativa**: Ativar organization
   ```python
   org.active = True
   org.save()
   ```

---

### Console mostra "No organizations"

**Sintomas**:
- Login bem-sucedido mas console vazio
- Não aparecem lojas nem vagas

**Verificação**:
```bash
# 1. Verificar Membership do usuário
python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin@shopping-xyz.local')

from configuration.models import Membership
ms = Membership.objects.filter(user=user)
print(f"Memberships: {ms.count()}")
for m in ms:
    print(f"  - {m.organization.name} ({m.role})")

# 2. Verificar se user.is_active e membership.active
print(f"User active: {user.is_active}")
for m in ms:
    print(f"Membership {m.organization.slug} active: {m.active}")
```

**Soluções**:
1. **Membership não existe**: Criar membership
   ```python
   from configuration.models import Organization, Membership
   org = Organization.objects.get(slug='shopping-xyz')
   Membership.objects.create(
       user=user,
       organization=org,
       role='admin',
       active=True,
       is_primary=True,
   )
   ```

2. **Membership inativa**: Ativar
   ```python
   m = Membership.objects.get(user=user, organization=org)
   m.active = True
   m.save()
   ```

3. **Usuário inativo**: Ativar usuário
   ```python
   user.is_active = True
   user.save()
   ```

---

## Problemas de Lojas e Dados

### Lojas não aparecem em list view

**Sintomas**:
- Console carrega mas lista de lojas vazia
- Outras organizações têm lojas

**Verificação**:
```bash
python manage.py shell
from configuration.models import Organization
from recruitment.domain_models import RecruitmentStore

org = Organization.objects.get(slug='shopping-xyz')
stores = RecruitmentStore.objects.filter(organization=org)
print(f"Stores for {org.slug}: {stores.count()}")
```

**Soluções**:
1. **Stores não foram criadas**: Executar import
   ```python
   from recruitment.domain_models import RecruitmentStore, RecruitmentCompany
   
   company, _ = RecruitmentCompany.objects.get_or_create(
       organization=org, name='Shopping Company'
   )
   
   RecruitmentStore.objects.create(
       organization=org,
       company=company,
       name='Loja Test',
       latitude=-23.564,
       longitude=-46.652,
   )
   ```

2. **View não filtra por organization**: Verificar `views.py`
   ```python
   # Em recruitment/views.py, garantir que queryset filtra:
   qs = RecruitmentStore.objects.filter(organization=self.request.organization)
   ```

3. **Organization não setada no request**: Verificar middleware
   ```bash
   # Testar:
   python manage.py shell
   from django.test import RequestFactory, Client
   client = Client()
   response = client.get('/console/recruitment/stores/',
       HTTP_HOST='shopping-xyz.br.matchco.app')
   print(response.status_code)
   ```

---

### QR codes não geram

**Sintomas**:
- Página de QR code está vazia ou erro
- EntryPoint existe mas QR não aparece

**Verificação**:
```bash
python manage.py shell
from recruitment.models import EntryPoint

ep = EntryPoint.objects.filter(organization__slug='shopping-xyz')
print(f"Entry Points: {ep.count()}")
for e in ep:
    print(f"  - {e.label}: state={e.state}, kind={e.kind}")
```

**Soluções**:
1. **EntryPoint state não é ACTIVE**: Ativar
   ```python
   ep = EntryPoint.objects.get(id=<id>)
   ep.state = EntryPoint.STATE_ACTIVE
   ep.save()
   ```

2. **EntryPoint não existe**: Criar
   ```python
   from django.utils import timezone
   from recruitment.models import EntryPoint
   from recruitment.domain_models import RecruitmentStore
   
   store = RecruitmentStore.objects.get(id=<store_id>)
   EntryPoint.objects.create(
       organization=store.organization,
       label=f'QR · {store.name}',
       kind=EntryPoint.KIND_STORE,
       scope_store=store,
       mode=EntryPoint.MODE_MATCH,
       state=EntryPoint.STATE_ACTIVE,
       activation_tested_at=timezone.now(),
   )
   ```

3. **Biblioteca QR code não instalada**: Instalar
   ```bash
   pip install qrcode[pil]
   ```

---

## Problemas de Isolamento de Tenant

### Tenant A vendo dados de Tenant B

**Sintomas**:
- Lojas de outro shopping aparecem
- Candidatos de outro tenant acessíveis
- Relatórios com dados misturados

**Verificação**:
```bash
# 1. Verificar que middleware está filtrando schema:
python manage.py shell
from django.test import Client

client = Client(HTTP_HOST='shopping-xyz.br.matchco.app')
response = client.get('/console/')
# Verificar se organization está no request

# 2. Verificar queries estão filtrando:
from recruitment.domain_models import RecruitmentStore
from configuration.models import Organization

org_a = Organization.objects.get(slug='shopping-a')
org_b = Organization.objects.get(slug='shopping-b')

# Sem filtro - ERRADO:
all_stores = RecruitmentStore.objects.all()
print(f"All stores: {all_stores.count()}")

# Com filtro - CERTO:
stores_a = RecruitmentStore.objects.filter(organization=org_a)
stores_b = RecruitmentStore.objects.filter(organization=org_b)
print(f"Stores A: {stores_a.count()}, Stores B: {stores_b.count()}")
```

**Soluções**:
1. **View não filtra por organization**: Adicionar filtro
   ```python
   # Em views.py:
   class StoreListView(ListView):
       def get_queryset(self):
           return RecruitmentStore.objects.filter(
               organization=self.request.organization
           )
   ```

2. **Middleware TenantMainMiddleware não ativo**: Ativar (veja seção anterior)

3. **Raw SQL queries**: Revisar e adicionar comentário `TENANT SAFE`
   ```python
   # ERRADO:
   stores = RecruitmentStore.objects.raw(
       'SELECT * FROM recruitment_store WHERE 1=1'
   )
   
   # CORRETO:
   stores = RecruitmentStore.objects.filter(
       organization=self.request.organization
   )
   ```

---

## Problemas de Login & Autenticação

### OTP não chega

**Sintomas**:
- Usuário clica "Send OTP" mas não recebe e-mail
- Campo de código fica vazio

**Verificação**:
```bash
# 1. Verificar que sistema de e-mail está configurado
python manage.py shell
from django.conf import settings
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")

# 2. Testar envio:
from django.core.mail import send_mail
send_mail('Test', 'Message', 'noreply@example.com', ['admin@example.local'])

# 3. Verificar que usuário tem e-mail
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin@shopping.local')
print(f"Email: {user.email}")
```

**Soluções**:
1. **E-mail não configurado**: Adicionar a `settings.py`
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.example.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'your-email@example.com'
   EMAIL_HOST_PASSWORD = 'password'
   ```

2. **Usuário sem e-mail**: Adicionar e-mail
   ```python
   user.email = 'admin@shopping.local'
   user.save()
   ```

3. **E-mail de OTP indo para spam**: Adicionar domain a whitelist do servidor

---

## Problemas de Performance

### Console lento ao listar candidatos

**Sintomas**:
- Página demora muito para carregar
- Muitos candidatos (>1000)

**Verificação**:
```bash
# 1. Usar Django debug toolbar:
# Adicionar a INSTALLED_APPS:
# 'debug_toolbar',

# 2. Verificar queries:
python manage.py shell
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True

# Executar operação...
print(f"Queries: {len(connection.queries)}")
for q in connection.queries:
    print(f"  {q['time']:.2f}s: {q['sql'][:100]}")
```

**Soluções**:
1. **Falta de índices**: Adicionar índices em `models.py`
   ```python
   class CandidateProfile(models.Model):
       # ...
       class Meta:
           indexes = [
               models.Index(fields=['organization', 'created_at']),
               models.Index(fields=['organization', 'name']),
           ]
   ```

2. **N+1 queries**: Usar `select_related` e `prefetch_related`
   ```python
   # ERRADO:
   candidates = CandidateProfile.objects.filter(organization=org)
   for c in candidates:
       print(c.application_set.count())  # Query por cada candidato!
   
   # CORRETO:
   candidates = CandidateProfile.objects.filter(
       organization=org
   ).prefetch_related('application_set')
   ```

3. **Paginação**: Implementar paginação
   ```python
   # Em views.py:
   paginate_by = 50
   ```

---

## Problemas de Reset/Seed

### Reset falha com erro

**Sintomas**:
- `python manage.py reset_demo_system` com erro
- Dados não resetam corretamente

**Verificação**:
```bash
# 1. Verificar que comando existe:
python manage.py reset_demo_system --help

# 2. Verificar que banco é acessível:
python manage.py dbshell

# 3. Testar migrações:
python manage.py migrate --plan
```

**Soluções**:
1. **Permissões de banco insuficientes**: Garantir acesso DROP/CREATE
   ```bash
   # PostgreSQL:
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
   ```

2. **Comando não existe**: Criar management command `reset_demo_system.py`
   ```bash
   touch talk/management/commands/reset_demo_system.py
   ```

3. **Erro de integridade**: Limpar dados antes de reset
   ```bash
   python manage.py flush --no-input
   python manage.py migrate
   ```

---

## Checklist de Diagnóstico

Ao encontrar um problema:

```
☐ Verificar domínio resolve (nslookup)
☐ Verificar TenantMainMiddleware ativo
☐ Verificar Domain e Organization existem
☐ Verificar Membership do usuário ativo
☐ Verificar queries filtram por organization
☐ Verificar estado de dados (state=ACTIVE)
☐ Verificar e-mail configurado
☐ Revisar logs de erro do servidor
☐ Testar em shell Django
☐ Executar manage.py check
```

---

## Contato e Escalação

- **Problemas de DNS**: Contatar DevOps / Provider de DNS
- **Problemas de e-mail**: Contatar SMTP provider
- **Problemas de dados**: Criar issue com query que reproduz
- **Problemas de performance**: Criar profiling de queries

---

**Última Atualização**: 2026-10-02  
**Mantido por**: Franco
