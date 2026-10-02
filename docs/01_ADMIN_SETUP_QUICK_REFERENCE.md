# Setup Rápido para Novos Tenants - Cartão de Referência

**Público**: Admins de Plataforma criando novos tenants  
**Tempo**: ~20 minutos por tenant  
**Pré-requisitos**: Acesso ao shell Python, conta de superuser

---

## Checklist Rápido

```
☐ Coletar informações (veja formulário abaixo)
☐ Criar Organization & Domain (Fase 1)
☐ Importar lojas/departamentos & funções (Fase 2)
☐ Criar usuário admin (Fase 3)
☐ Criar entry points / QR codes (Fase 4)
☐ Testar & verificar (Fase 5)
☐ Documentar em planilha de rastreamento
```

---

## Formulário de Coleta de Informações

Obtenha estes detalhes do novo tenant:

| Item | Valor | Exemplo |
|------|-------|---------|
| **Nome da Organização** | | Shopping XYZ |
| **Slug da Organização** | | `shopping-xyz` (minúsculas, hífens) |
| **Domínio Primário** | | `shopping-xyz.br.matchco.app` |
| **Setor** | Shopping / Hospital / Farmácia | Shopping |
| **Número de Lojas** | | 5 |
| **E-mail do Admin** | | admin@shopping-xyz.local |
| **CSV de Lojas** | Caminho do arquivo | `/tmp/stores.csv` |
| **Lista de Funções** | Separadas por vírgula ou CSV | "Caixa, Repositor, Gerente" |

---

## Fase 1: Organization & Domain (5 min)

```bash
python manage.py shell
```

```python
from configuration.models import Organization, Domain

org = Organization.objects.create(
    name='Shopping XYZ SA',
    slug='shopping-xyz',
    active=True,
)

Domain.objects.create(
    domain='shopping-xyz.br.matchco.app',
    tenant=org,
    is_primary=True,
)

print(f"✓ {org.name} criada ({org.slug})")
```

---

## Fase 2: Lojas & Funções (5 min)

### Preparar CSV: `stores.csv`
```
Name,Latitude,Longitude
Loja Centro,-23.564,-46.652
Loja Zona Sul,-23.560,-46.658
Loja Zona Leste,-23.567,-46.647
```

### Executar importação:
```python
from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction
from configuration.models import Organization
import csv

org = Organization.objects.get(slug='shopping-xyz')
company, _ = RecruitmentCompany.objects.get_or_create(
    organization=org, name='Shopping Company'
)

# Importar lojas
with open('/tmp/stores.csv') as f:
    for row in csv.DictReader(f):
        RecruitmentStore.objects.create(
            organization=org, company=company,
            name=row['Name'],
            latitude=float(row['Latitude']),
            longitude=float(row['Longitude']),
        )

# Importar funções
functions = ['Atendente de caixa', 'Repositor', 'Vendedor', 'Gerente']
for fname in functions:
    RecruitmentJobFunction.objects.get_or_create(
        organization=org, company=company, name=fname,
    )

print(f"✓ {RecruitmentStore.objects.filter(organization=org).count()} lojas")
print(f"✓ {RecruitmentJobFunction.objects.filter(organization=org).count()} funções")
```

---

## Fase 3: Usuário Admin (3 min)

```python
from django.contrib.auth import get_user_model
from configuration.models import Organization, Membership

User = get_user_model()
org = Organization.objects.get(slug='shopping-xyz')

user = User.objects.create_user(
    username='admin@shopping-xyz.br.matchco.app',
    email='admin@shopping-xyz.local',
    is_staff=True, is_active=True,
)
# Sem senha — usará OTP

Membership.objects.create(
    user=user, organization=org,
    role='admin', active=True, is_primary=True,
)

print(f"✓ Usuário admin: {user.username}")
print(f"✓ Console: https://shopping-xyz.br.matchco.app/console/")
```

---

## Fase 4: Entry Points (3 min)

```python
from recruitment.models import EntryPoint
from recruitment.domain_models import RecruitmentStore
from django.utils import timezone

org = Organization.objects.get(slug='shopping-xyz')

for store in RecruitmentStore.objects.filter(organization=org):
    # Modo Match
    EntryPoint.objects.get_or_create(
        organization=org,
        label=f'QR Match · {store.name}',
        defaults={
            'kind': EntryPoint.KIND_STORE,
            'scope_store': store,
            'mode': EntryPoint.MODE_MATCH,
            'activation_tested_at': timezone.now(),
            'state': EntryPoint.STATE_ACTIVE,
        },
    )

print(f"✓ Entry points criados")
```

---

## Fase 5: Verificar (4 min)

### Testar via Django shell:
```bash
# Verificar organização
python manage.py shell
from configuration.models import Organization
org = Organization.objects.get(slug='shopping-xyz')
print(f"Org: {org.name}")

# Verificar domínio
from configuration.models import Domain
print(f"Domain: {org.domains.filter(is_primary=True).first().domain}")

# Verificar lojas
from recruitment.domain_models import RecruitmentStore
print(f"Lojas: {RecruitmentStore.objects.filter(organization=org).count()}")

# Verificar entry points
from recruitment.models import EntryPoint
print(f"Entry points: {EntryPoint.objects.filter(organization=org).count()}")
```

### Testar via navegador (rodando localmente):
```
Editar /etc/hosts:
127.0.0.1 shopping-xyz.br.matchco.app

Testar:
- https://shopping-xyz.br.matchco.app/candidato/signup
  Esperado: Formulário de signup carrega, contexto da organização correto
- https://shopping-xyz.br.matchco.app/console/
  Esperado: Login, depois console mostra lojas/posições desta org
```

---

## Troubleshooting

| Problema | Verificar | Solução |
|----------|-----------|---------|
| Domínio não resolve | DNS wildcard configurado | `nslookup shopping-xyz.br.matchco.app` |
| 404 em `/candidato/signup` | TenantMainMiddleware ativo | Verificar MIDDLEWARE em settings.py |
| Console mostra "No organizations" | Membership do usuário existe | Verificar Membership FK para org |
| Lojas não aparecem em list view | Filtro de organização na view | Verificar recruitment/views.py filters |
| QR codes não gerados | EntryPoint.state = ACTIVE | Setar state = 'ACTIVE' |

---

## Automação (Futuro)

Substituir passos manuais com:
```bash
python manage.py seed_tenant \
  --name "Shopping XYZ" \
  --slug "shopping-xyz" \
  --domain "shopping-xyz.br.matchco.app" \
  --stores stores.csv \
  --functions functions.csv \
  --admin-email admin@shopping-xyz.local
```

---

## Documentação Completa

Detalhes completos: [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md)  
Decisão de arquitetura: Ver [02_ARCHITECTURE_DECISIONS.md](02_ARCHITECTURE_DECISIONS.md)
