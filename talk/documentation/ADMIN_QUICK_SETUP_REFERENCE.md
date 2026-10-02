# MatchCo Tenant Setup — Quick Reference Card

**For**: Platform Admins creating new tenant organizations  
**Time**: ~20 minutes per tenant  
**Prerequisites**: Python shell access, superuser account

---

## Quick Checklist

```
☐ Collect information (see checklist below)
☐ Create Organization & Domain (Phase 1)
☐ Import stores/departments & functions (Phase 2)
☐ Create admin user (Phase 3)
☐ Create entry points / QR codes (Phase 4)
☐ Test & verify (Phase 5)
☐ Document in shared tracking sheet
```

---

## Information Intake Form

Get these details from the new tenant:

| Item | Value | Example |
|------|-------|---------|
| **Organization Name** | | Shopping XYZ |
| **Organization Slug** | | `shopping-xyz` (lowercase, hyphens) |
| **Primary Domain** | | `shopping-xyz.br.matchco.app` |
| **Sector** | Shopping / Hospital / Pharmacy | Shopping |
| **Number of Stores** | | 5 |
| **Admin Email** | | admin@shopping-xyz.local |
| **Stores CSV** | File path | `/tmp/stores.csv` |
| **Functions List** | Comma-separated or CSV | "Caixa, Repositor, Gerente" |

---

## Phase 1: Organization & Domain (5 min)

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

print(f"✓ {org.name} created ({org.slug})")
```

---

## Phase 2: Stores & Functions (5 min)

### Prepare CSV: `stores.csv`
```
Name,Latitude,Longitude
Loja Centro,-23.564,-46.652
Loja Zona Sul,-23.560,-46.658
Loja Zona Leste,-23.567,-46.647
```

### Run import:
```python
from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction
from configuration.models import Organization
import csv

org = Organization.objects.get(slug='shopping-xyz')
company, _ = RecruitmentCompany.objects.get_or_create(
    organization=org, name='Shopping Company'
)

# Import stores
with open('/tmp/stores.csv') as f:
    for row in csv.DictReader(f):
        RecruitmentStore.objects.create(
            organization=org, company=company,
            name=row['Name'],
            latitude=float(row['Latitude']),
            longitude=float(row['Longitude']),
        )

# Import functions
functions = ['Atendente de caixa', 'Repositor', 'Vendedor', 'Gerente']
for fname in functions:
    RecruitmentJobFunction.objects.get_or_create(
        organization=org, company=company, name=fname,
    )

print(f"✓ {RecruitmentStore.objects.filter(organization=org).count()} stores")
print(f"✓ {RecruitmentJobFunction.objects.filter(organization=org).count()} functions")
```

---

## Phase 3: Admin User (3 min)

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
# No password — they'll use OTP

Membership.objects.create(
    user=user, organization=org,
    role='admin', active=True, is_primary=True,
)

print(f"✓ Admin user: {user.username}")
print(f"✓ Console: https://shopping-xyz.br.matchco.app/console/")
```

---

## Phase 4: Entry Points (3 min)

```python
from recruitment.models import EntryPoint
from recruitment.domain_models import RecruitmentStore
from django.utils import timezone

org = Organization.objects.get(slug='shopping-xyz')

for store in RecruitmentStore.objects.filter(organization=org):
    # Match mode
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

print(f"✓ Entry points created")
```

---

## Phase 5: Verify (4 min)

### Test via Django shell:
```bash
# Check organization exists
python manage.py shell
from configuration.models import Organization
org = Organization.objects.get(slug='shopping-xyz')
print(f"Org: {org.name}")

# Check domain
from configuration.models import Domain
print(f"Domain: {org.domains.filter(is_primary=True).first().domain}")

# Check stores
from recruitment.domain_models import RecruitmentStore
print(f"Stores: {RecruitmentStore.objects.filter(organization=org).count()}")

# Check entry points
from recruitment.models import EntryPoint
print(f"Entry points: {EntryPoint.objects.filter(organization=org).count()}")
```

### Test via browser (if running locally with host entry):
```
Edit /etc/hosts:
127.0.0.1 shopping-xyz.br.matchco.app

Test:
- https://shopping-xyz.br.matchco.app/candidato/signup
  Expected: Signup form loads, organization context correct
- https://shopping-xyz.br.matchco.app/console/
  Expected: Login, then console shows this org's stores/positions
```

---

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| Domain not resolving | DNS wildcard configured | `nslookup shopping-xyz.br.matchco.app` |
| 404 on `/candidato/signup` | TenantMainMiddleware active | Check MIDDLEWARE in settings.py |
| Console shows "No organizations" | User membership exists | Verify Membership FK to org |
| Stores not appearing in list view | Organization filter in view | Check recruitment/views.py filters |
| QR codes not generating | EntryPoint.state = ACTIVE | Set state = 'ACTIVE' |

---

## Automation (Future)

Replace manual steps with:
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

## Documentation

Full details: `/docs/MATCHCO_MULTITENANT_ARCHITECTURE.md`  
Architecture decision: See project memory (`multitenant_architecture_decision.md`)
