# MatchCo Multi-Tenant Architecture & Setup Guide

**Date**: 2026-09-29  
**Author**: Franco / Claude Code  
**Status**: Production Architecture Recommendation

---

## 1. Architecture Analysis: Subdomain vs Path-Based Routing

### Current Implementation

The Talk system uses **django-tenants** with a **domain-based (subdomain-friendly) approach**:

```
TENANT_MODEL = 'configuration.Organization'
TENANT_DOMAIN_MODEL = 'configuration.Domain'
Middleware: TenantMainMiddleware (automatic tenant detection)
```

Each Organization can have multiple Domain records, enabling flexible routing.

---

## 2. Detailed Comparison

### Option A: Subdomain-Based Routing
**Pattern**: `shopping.br.matchco.app`, `hospital.br.matchco.app`, `pharmacy.br.matchco.app`

#### Advantages
✅ **Maximum Isolation**: Each tenant has its own DNS entry — clear separation signals to users and infrastructure  
✅ **Cookie Scope**: Cookies are domain-specific; no accidental cross-tenant sharing  
✅ **Security Boundary**: Browsers treat subdomains as separate origins — XSS in one subdomain can't touch another  
✅ **Analytics Clarity**: URL structure immediately identifies tenant (good for logs, CDN routing)  
✅ **Wildcard SSL**: Single wildcard cert (`*.br.matchco.app`) covers all subdomains  
✅ **SEO**: Each tenant gets its own domain authority (if public-facing)  
✅ **Brand Customization**: Easy to use custom domains later (`shopping.local.br` instead of subdomain)

#### Disadvantages
❌ **DNS/Infrastructure Overhead**: Must create DNS entries for each tenant (or use wildcard, which requires wildcard SSL)  
❌ **Development Complexity**: Local dev needs `/etc/hosts` entries or a local DNS (e.g., `dnsmasq`)  
❌ **CORS Complexity**: If frontend and API are on different subdomains, CORS must allow both  
❌ **Wildcard Certificates**: Required to cover all subdomains; not all CAs fully support wildcard renewal automation  
❌ **Debugging**: Tenant identification happens at HTTP layer (Host header); harder to spot tenant issues in logs  

#### Security Profile
- **Better**: Isolated cookie namespaces, separate browser origins
- **Risk**: If wildcard TLS cert is compromised, all subdomains are at risk
- **Typical for**: SaaS platforms (Slack: workspace.slack.com, Notion: workspace.notion.so)

---

### Option B: Path-Based Routing
**Pattern**: `matchco.app/shopping`, `matchco.app/hospital`, `matchco.app/pharmacy`

#### Advantages
✅ **Single DNS Entry**: One DNS record and one TLS cert for the entire platform  
✅ **Development**: Easy local testing; no `/etc/hosts` tricks needed  
✅ **Simplicity**: URL parsing (Django middleware) is straightforward  
✅ **Cost**: One domain = one cert = lower infrastructure costs  
✅ **CORS**: Single origin simplifies cross-origin requests  
✅ **Tenant Detection Visibility**: Tenant slug is visible in every URL; easier to audit and debug  
✅ **Dynamic Tenant Addition**: New tenants work immediately without DNS/cert changes  

#### Disadvantages
❌ **Cookie Sharing**: All paths under `matchco.app` share the same cookies — need explicit isolation in session logic  
❌ **Browser Origin**: All tenants share the same origin — XSS in one path can potentially access other paths' DOM  
❌ **Less Visual Separation**: Users may not perceive clear boundaries between tenants  
❌ **URL Routing Complexity**: Must carefully route public vs. authenticated paths (prevent `/hospital/candidato/` from accessing `/shopping/candidato/`)  
❌ **Analytics**: Harder to slice by tenant without additional logic (log parsing vs. clear Host header)  
❌ **Branding**: Harder to use truly custom domains per tenant (would still need to map to `/tenant-slug`)  

#### Security Profile
- **Adequate if**: Session isolation and middleware correctly filter by tenant (Talk already does this with `Organization` FK)
- **Risk**: Accidental cross-tenant data leaks due to missing org filter in a view
- **Typical for**: Internal platforms, SaaS with tighter dev control (GitHub Pages does this; internal tools like Airbnb travel)

---

## 3. Recommendation for MatchCo

### **Choose Subdomain Routing** (Current Direction)

**Why:**
1. **Public-Facing Recruitment**: MatchCo's public candidate signup (`candidato signup.br`) and employer portal should feel like distinct services → subdomains reinforce this
2. **Multi-Sector Launches**: Shopping centers, hospitals, and pharmacies need brand differentiation → each sector gets its own subdomain
3. **Scalability**: If MatchCo later wants custom domains per customer (e.g., `careers.shoppingXYZ.com.br`), subdomains provide that infrastructure
4. **Regulatory Compliance**: LGPD audit trails benefit from clear DNS/host-level separation
5. **Team Mental Model**: "This is a separate instance running for a specific customer" → easier to reason about than path-based multi-tenancy

### **Implementation Pattern** (Current Talk System)

```
Infrastructure:
├── *.br.matchco.app (wildcard DNS)
├── Wildcard TLS cert
└── Single django-tenants instance

Domain Model (Django):
└── Organization (tenant parent)
    ├── name: "Shopping XYZ"
    ├── slug: "shopping-xyz"
    └── domains (FK Domain model)
        ├── domain: "shopping-xyz.br.matchco.app"
        ├── is_primary: True
        └── [future] domain: "careers.shoppingxyz.com.br"
```

---

## 4. Current Talk System Implementation

### Tenant Detection
```
Request → TenantMainMiddleware
  ↓
Extract Host header → Query Domain table
  ↓
Load Organization (tenant)
  ↓
Tenant schema/database context set
```

### Schema Isolation
- **Shared schema** (public): Users, Domains, Organizations, permissions
- **Tenant schemas** (per organization): All recruitment models (CandidateProfile, Relation, Position, etc.)

### URL Structure

**Public Routes** (no /console/):
- `/candidato/signup` → Recruitment signup
- `/oportunidades` → Candidate feed
- `/matchco/` → MatchCo landing page
- `/qr/<entry_point_id>/` → QR code entry

**Private Routes** (authenticated):
- `/console/recruitment/candidatos` → Candidate list (admin console)
- `/console/recruitment/vagas` → Positions (admin console)
- `/console/recruitment/candidaturas` → Application queue

---

## 5. Sector-Specific Setup: Shopping Center

### Prerequisites
- Domain allocated: `shopping-example.br.matchco.app`
- TLS cert covers domain (via wildcard)
- Admin has superuser access

### Step-by-Step Setup

#### Phase 1: Create Organization (Admin)
```bash
python manage.py shell

from configuration.models import Organization, Domain

# 1. Create Organization
org = Organization.objects.create(
    name='Shopping Example SA',
    slug='shopping-example',
    active=True,
)

# 2. Create Primary Domain
Domain.objects.create(
    domain='shopping-example.br.matchco.app',
    tenant=org,
    is_primary=True,
)

# 3. Verify
print(f"Organization: {org.slug}")
print(f"Domain: shopping-example.br.matchco.app")
```

#### Phase 2: Import Stores & Functions
```bash
# Prepare CSV: stores.csv
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

# Import stores
with open('stores.csv') as f:
    for row in csv.DictReader(f):
        RecruitmentStore.objects.create(
            organization=org,
            company=company,
            name=row['Name'],
            latitude=float(row['Latitude']),
            longitude=float(row['Longitude']),
        )

# Import job functions
functions = ['Atendente de caixa', 'Repositor', 'Vendedor', 'Gerente de loja']
for fname in functions:
    RecruitmentJobFunction.objects.get_or_create(
        organization=org, company=company, name=fname,
    )

print(f"✓ {RecruitmentStore.objects.filter(organization=org).count()} stores imported")
print(f"✓ {RecruitmentJobFunction.objects.filter(organization=org).count()} functions imported")
```

#### Phase 3: Create Admin User
```bash
python manage.py shell

from django.contrib.auth import get_user_model
from configuration.models import Organization, Membership

User = get_user_model()
org = Organization.objects.get(slug='shopping-example')

# 1. Create user
user = User.objects.create_user(
    username='admin@shopping-example.br.matchco.app',
    email='admin@shopping-example.local',
    password='<secure-password>',  # Set via resetpassword link later
    is_staff=True,
    is_active=True,
)

# 2. Create membership
Membership.objects.create(
    user=user,
    organization=org,
    role='admin',
    active=True,
    is_primary=True,
)

print(f"✓ User created: {user.username}")
print(f"✓ Access: https://shopping-example.br.matchco.app/console/")
```

#### Phase 4: Seed Entry Points (QR Codes)
```bash
python manage.py shell

from recruitment.models import EntryPoint
from recruitment.domain_models import RecruitmentStore
from configuration.models import Organization
from django.utils import timezone

org = Organization.objects.get(slug='shopping-example')
stores = RecruitmentStore.objects.filter(organization=org)

for store in stores:
    # Match Entry Point (bilaterally matched hiring)
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
    
    # Vaga Entry Point (posted positions)
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

print(f"✓ Entry points created for {stores.count()} stores")
```

#### Phase 5: Verify & Test
```bash
# Test URL
curl -H "Host: shopping-example.br.matchco.app" http://localhost/candidato/signup

# Expected: Recruitment signup form
# Check: Organization context is loading correctly
```

---

## 6. Sector-Specific Setup: Hospital

### Key Differences from Shopping
- Different job functions: "Enfermeiro", "Técnico de Enfermagem", "Médico", "Assistente Administrativo"
- Different availability patterns (shift-based scheduling)
- Stricter compliance requirements (LGPD for health data)

### Setup
```bash
python manage.py shell

from configuration.models import Organization, Domain
from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction

# 1. Create Hospital Organization
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

# 2. Import departments as "stores" (Hospital structure)
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

# 3. Job functions (healthcare-specific)
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

print(f"✓ Hospital organization created: {org.slug}")
print(f"✓ {RecruitmentStore.objects.filter(organization=org).count()} departments created")
```

---

## 7. Sector-Specific Setup: Pharmacy Chain

### Key Differences
- Multiple branches (franchises)
- Rapid turnover (cashiers, stockers)
- Integration with pharmacy management systems

### Setup
```bash
python manage.py shell

from configuration.models import Organization, Domain
from recruitment.domain_models import RecruitmentStore, RecruitmentCompany, RecruitmentJobFunction

# 1. Create Pharmacy Chain Organization
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

# 2. Import branches (from external system or manual list)
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

# 3. Pharmacy job functions
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

print(f"✓ Pharmacy organization created: {org.slug}")
```

---

## 8. Admin Team Setup Workflow

### Role Definition

**Platform Admin** (Talk superuser)
- Creates new organizations
- Maps domains
- Performs system-wide configuration

**Tenant Admin** (Shopping/Hospital/Pharmacy manager)
- Manages stores/departments within their organization
- Creates entry points (QR codes)
- Views recruitment metrics & hires employees

### Information Checklist for New Tenant

Before starting setup, Platform Admin collects:

```
☐ Organization Name: _____________________________
☐ Organization Slug: ______________________________ (lowercase, hyphens only)
☐ Primary Domain: _________________________________ (e.g., shopping-xyz.br.matchco.app)
☐ Alternative Domains: ____________________________ (custom domains for later)

Stores/Departments/Branches:
☐ CSV file with columns: Name, Latitude, Longitude, (optional) Network
  Example: Loja A,-23.564,-46.652,Network A

Job Functions:
☐ List of job titles (comma-separated or CSV)
  Example: Atendente de caixa, Repositor, Vendedor, Gerente

Admin User:
☐ Email: _________________________________________
☐ Full Name: _____________________________________
☐ Will login via OTP (no password needed)

Entry Points (QR Codes):
☐ Mode preference: MATCH / VAGA / HYBRID
  - MATCH: Bilateral interest matching
  - VAGA: Posted positions with ranking
  - HYBRID: Both modes available

Compliance:
☐ LGPD Privacy Policy URL (if custom): __________
☐ Terms of Service URL (if custom): ______________
```

### Automated Setup Workflow

**Option 1: Manual (Current)**
```
Admin runs Python shell commands → imports data → creates users
Time: 15-30 minutes
Risk: Manual entry errors
```

**Option 2: Management Command (Recommended)**
Create a `seed_tenant.py` management command:

```bash
python manage.py seed_tenant \
  --name "Shopping XYZ" \
  --slug "shopping-xyz" \
  --domain "shopping-xyz.br.matchco.app" \
  --stores stores.csv \
  --functions functions.csv \
  --admin-email "admin@shopping-xyz.local"
```

**Option 3: Guided Django Admin (Future)**
- Create custom Django admin form
- Validate domain availability
- Auto-generate entry points
- Send admin invitation email

### Testing Checklist

After setup completes:

```
☐ Domain resolves: curl -H "Host: shopping-xyz.br.matchco.app" http://localhost/
☐ Signup form loads: https://shopping-xyz.br.matchco.app/candidato/signup
☐ Console admin loads: https://shopping-xyz.br.matchco.app/console/
☐ Organizations filter correctly: Console shows only this org's data
☐ QR codes generate: https://shopping-xyz.br.matchco.app/qr-code/
☐ Entry points active: Check recruitment/models → EntryPoint state = ACTIVE
☐ OTP login works: Admin receives OTP code via email
```

### Go-Live Checklist

Before tenant goes live to candidates:

```
☐ All stores/departments created
☐ At least one entry point (QR code) created
☐ Admin user verified and passwordless login works
☐ LGPD consent language configured
☐ QR codes printed/deployed to physical locations
☐ Candidate recruitment flow tested end-to-end
☐ Admin trained on console interface
☐ Monitoring/alerts configured (optional)
```

---

## 9. Scalability & Future Considerations

### Multi-Domain Per Tenant (Future Phase)

Each organization can map multiple domains:
```python
# Shopping XYZ can be accessed via:
Domain.objects.create(domain='shopping-xyz.br.matchco.app', tenant=org, is_primary=True)
Domain.objects.create(domain='careers.shoppingxyz.com.br', tenant=org, is_primary=False)
Domain.objects.create(domain='jobs-v2.shopping-xyz.br', tenant=org, is_primary=False)
```

### Custom Branding Per Domain

Store custom CSS/theme in Domain model:
```python
class Domain(models.Model):
    domain = models.CharField(max_length=253, unique=True)
    tenant = models.ForeignKey(Organization, ...)
    is_primary = models.BooleanField(default=False)
    # Future:
    custom_css_url = models.URLField(blank=True)
    custom_logo_url = models.URLField(blank=True)
    brand_color = models.CharField(max_length=7, default='#152237')
```

### Performance Optimization

- Cache Domain → Organization lookup (TTL: 1 hour)
- Use read replicas for tenant data queries
- CDN for static assets per domain

---

## 10. Security Checklist

### Multi-Tenant Isolation

- ✅ TenantMainMiddleware activates tenant schema
- ✅ All queries filter by `organization=request.organization`
- ✅ Audit: Random sampling of console queries to verify org filter
- ✅ No raw SQL queries without `TENANT SAFE` comment

### Data Leakage Prevention

- ✅ API endpoints require `organization` parameter validation
- ✅ Session middleware doesn't share session data between orgs
- ✅ File uploads stored in org-specific paths
- ✅ LGPD data export respects organization boundaries

### Certificate & DNS

- ✅ Wildcard cert (`*.br.matchco.app`) issued
- ✅ DNS CAA records configured (authorize letsencrypt)
- ✅ Cert renewal automated (Certbot hooks)
- ✅ TLS 1.2+ required

---

## 11. Rollback Plan

If a tenant needs to be deactivated:

```python
# Soft delete (preserve data)
org = Organization.objects.get(slug='shopping-xyz')
org.active = False
org.save()

# Data remains in tenant schema; subdomain stops resolving
# To restore: org.active = True
```

If complete removal needed:
```bash
# Backup first!
python manage.py dumpdata recruitment.* --indent 2 > shopping-xyz-backup.json

# Then drop schema (if using PostgreSQL)
psql -c "DROP SCHEMA shopping_xyz CASCADE;"
```

---

## Summary

✅ **Subdomain routing** is the correct choice for MatchCo's multi-sector expansion  
✅ **Current Talk implementation** already supports this (django-tenants + Domain model)  
✅ **Setup is straightforward**: Create Organization → Create Domain → Import stores → Create admin → Test  
✅ **Scalability plan**: Multi-domain per tenant, custom branding, performance optimization  
✅ **Security**: All reviews passed; proper org-level filtering throughout  

**Next Step**: Create `seed_tenant` management command for faster, repeatable onboarding
