# Mapa Detalhado de Dependências: TENANT_APPS → SHARED_APPS

**Data**: 27 Jul 2026  
**Status**: 📊 Análise Completa  
**Total de Dependências Identificadas**: 18  
**Apps Afetados**: 6 (gamification, courses, students, audience, library, documents)  
**Apps Limpos**: 2 (chat, console)

---

## 📋 Resumo Executivo

```
DEPENDÊNCIAS POR TIPO:

User (user_management.User) → 11 dependências
├─ GamificationReport.user (NOT NULL)
├─ GamificationPostView.user (NOT NULL)
├─ Course.author (nullable)
├─ Course.owner (NOT NULL)
├─ CourseEnroll.student_id (NOT NULL)
├─ ContentItem.owner (NOT NULL)
├─ ContentItemProgress.user (NOT NULL)
├─ Document.owner (NOT NULL)
├─ DocumentPermission.user (NOT NULL)
├─ DocumentPermission.granted_by (nullable)
├─ DocumentVersion.created_by (NOT NULL)
├─ DocumentView.user (NOT NULL)
└─ DocumentLink.created_by (NOT NULL)

Organization (configuration.Organization) → 4 dependências
├─ Course.organization (nullable)
├─ AudiencePolicy.organization (nullable)
├─ Document.organization (nullable)
└─ Document.company (nullable)

Publication (publishing.Publication) → 1 dependência
└─ GamificationPostView.feed_post (NOT NULL)

Company (configuration.Company) → 1 dependência
└─ Course.company (nullable)
```

---

## 🔧 Estratégia de Refatoração por Tipo

### TIPO 1: User References (11 Total)

**Status**: ⚠️ Crítico (necessário em CADA tenant)

#### 1. GamificationReport.user
```python
# ANTES (SHARED_APPS)
class GamificationReport(models.Model):
    user = ForeignKey(User)  # ← Problema: User está em SHARED

# DEPOIS (TENANT_APPS)
class TenantUser(models.Model):
    """Espelho de User no schema tenant"""
    user_id = IntegerField(primary_key=True)
    username = CharField(max_length=150)
    email = EmailField()

class GamificationReport(models.Model):
    user = ForeignKey(TenantUser, primary_key=user_id)  # ✓ Seguro
    
    def get_real_user(self):
        """Helper para acessar usuário real em schema público"""
        from user_management.models import User
        return User.objects.get(id=self.user_id)
```

#### 2. GamificationPostView.user
```python
# Mesmo padrão que GamificationReport.user
# SOLUÇÃO: Copiar para TenantUser (já criado)
```

#### 3. Course.author, Course.owner
```python
# ANTES
class Course(models.Model):
    author = ForeignKey(User, null=True)  # nullable ✓ (mais fácil)
    owner = ForeignKey(User)  # NOT NULL ✗ (problema)

# DEPOIS
class Course(models.Model):
    author = ForeignKey(TenantUser, null=True)
    owner = ForeignKey(TenantUser)
    
    def get_real_author(self):
        from user_management.models import User
        return User.objects.get(id=self.author_id) if self.author_id else None
    
    def get_real_owner(self):
        from user_management.models import User
        return User.objects.get(id=self.owner_id)
```

#### 4. CourseEnroll.student_id
```python
# ANTES
class CourseEnroll(models.Model):
    student_id = ForeignKey(User)

# DEPOIS
class CourseEnroll(models.Model):
    student_id = ForeignKey(TenantUser)
```

#### 5. ContentItem.owner, ContentItemProgress.user
```python
# Mesmo padrão
# SOLUÇÃO: ForeignKey para TenantUser
```

#### 6. Document.owner, DocumentPermission.user, etc.
```python
# 7 modelos em documents/ com FKs para User
# SOLUÇÃO: Usar TenantUser para todos
```

---

### TIPO 2: Organization References (4 Total)

**Status**: ⚠️ Crítico (necessário em CADA tenant)

#### 1. Course.organization
```python
# ANTES (SHARED_APPS)
class Course(models.Model):
    organization = ForeignKey(Organization, null=True)

# DEPOIS (TENANT_APPS)
class TenantOrganization(models.Model):
    """Espelho de Organization no schema tenant"""
    organization_id = IntegerField(primary_key=True)
    name = CharField(max_length=160)
    slug = SlugField()

class Course(models.Model):
    organization = ForeignKey(TenantOrganization, null=True)
    
    def get_real_organization(self):
        from configuration.models import Organization
        return Organization.objects.get(id=self.organization_id) if self.organization_id else None
```

#### 2. AudiencePolicy.organization
```python
# Mesmo padrão
class AudiencePolicy(models.Model):
    organization = ForeignKey(TenantOrganization, null=True)
```

#### 3. Document.organization
```python
# Mesmo padrão
class Document(models.Model):
    organization = ForeignKey(TenantOrganization, null=True)
```

#### 4. Course.company
```python
# ANTES
class Course(models.Model):
    company = ForeignKey(Company, null=True)  # Company está em SHARED

# DEPOIS
class TenantCompany(models.Model):
    """Espelho de Company"""
    company_id = IntegerField(primary_key=True)
    name = CharField(max_length=160)

class Course(models.Model):
    company = ForeignKey(TenantCompany, null=True)
```

---

### TIPO 3: Publication References (1 Total)

**Status**: ⚠️ Crítico

#### GamificationPostView.feed_post
```python
# PROBLEMA: Publication está em SHARED_APPS
# SOLUÇÃO: Remover essa relação! (não faz sentido em tenant schema)

# ANTES
class GamificationPostView(models.Model):
    feed_post = ForeignKey(Publication)  # ← Cross-schema!

# DEPOIS
class GamificationPostView(models.Model):
    # Remover FK!
    feed_post_id = IntegerField()  # Apenas ID, sem FK
    
    def get_feed_post(self):
        """Busca em schema público"""
        from django.db import connections
        from publishing.models import Publication
        
        # Usar schema público
        return Publication.objects.get(id=self.feed_post_id)
```

---

## 📊 Tabela de Solução

| # | Model | Field | Target | Tipo | Nullable | Solução |
|---|-------|-------|--------|------|----------|---------|
| 1 | GamificationReport | user | User | FK | ❌ | TenantUser |
| 2 | GamificationPostView | user | User | FK | ❌ | TenantUser |
| 3 | GamificationPostView | feed_post | Publication | FK | ❌ | IntegerField |
| 4 | Course | author | User | FK | ✅ | TenantUser |
| 5 | Course | owner | User | FK | ❌ | TenantUser |
| 6 | Course | organization | Organization | FK | ✅ | TenantOrganization |
| 7 | Course | company | Company | FK | ✅ | TenantCompany |
| 8 | CourseEnroll | student_id | User | FK | ❌ | TenantUser |
| 9 | AudiencePolicy | organization | Organization | FK | ✅ | TenantOrganization |
| 10 | ContentItem | owner | User | FK | ❌ | TenantUser |
| 11 | ContentItemProgress | user | User | FK | ❌ | TenantUser |
| 12 | Document | organization | Organization | FK | ✅ | TenantOrganization |
| 13 | Document | owner | User | FK | ❌ | TenantUser |
| 14 | DocumentPermission | user | User | FK | ❌ | TenantUser |
| 15 | DocumentPermission | granted_by | User | FK | ✅ | TenantUser |
| 16 | DocumentVersion | created_by | User | FK | ❌ | TenantUser |
| 17 | DocumentView | user | User | FK | ❌ | TenantUser |
| 18 | DocumentLink | created_by | User | FK | ❌ | TenantUser |

---

## 🛠️ Plano de Implementação Detalhado

### PASSO 1: Criar Modelos Espelho (1 dia)

**Arquivo**: `tenants_core/models.py`

```python
from django.db import models

class TenantUser(models.Model):
    """Espelho de User no schema tenant"""
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150)
    email = models.EmailField()
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        managed = True
        db_table = 'tenants_core_tenantuser'

class TenantOrganization(models.Model):
    """Espelho de Organization no schema tenant"""
    organization_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    
    class Meta:
        managed = True
        db_table = 'tenants_core_tenantorganization'

class TenantCompany(models.Model):
    """Espelho de Company no schema tenant"""
    company_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=160)
    
    class Meta:
        managed = True
        db_table = 'tenants_core_tenantcompany'
```

### PASSO 2: Refatorar Models (2 dias)

**Arquivos a modificar:**
- `gamification/models.py` (2 modelos)
- `courses/models.py` (1 modelo)
- `students/models.py` (1 modelo)
- `audience/models.py` (1 modelo)
- `library/models.py` (2 modelos)
- `documents/models.py` (4 modelos)

**Exemplo de refatoração**:
```python
# gamification/models.py
from tenants_core.models import TenantUser, TenantOrganization
from django.contrib.auth import get_user_model

class GamificationReport(models.Model):
    # NOVO: usar TenantUser
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE)
    points = models.IntegerField()
    
    def get_real_user(self):
        """Busca usuário real em schema público"""
        User = get_user_model()
        return User.objects.get(id=self.user_id)
```

### PASSO 3: Criar Migrations (1 dia)

```bash
python manage.py makemigrations tenants_core
python manage.py makemigrations gamification
python manage.py makemigrations courses
python manage.py makemigrations students
python manage.py makemigrations audience
python manage.py makemigrations library
python manage.py makemigrations documents
```

### PASSO 4: Implementar Signals (1 dia)

**Arquivo**: `configuration/signals.py`

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from configuration.models import Organization, Company

User = get_user_model()

@receiver(post_save, sender=User)
def sync_user_to_tenants(sender, instance, created, **kwargs):
    """Quando usuário muda em schema público, sincroniza em todos os tenants"""
    from django_tenants.utils import get_tenant_model
    from tenants_core.models import TenantUser
    
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        tenant.activate()
        TenantUser.objects.update_or_create(
            user_id=instance.id,
            defaults={
                'username': instance.username,
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'is_active': instance.is_active,
            }
        )

@receiver(post_save, sender=Organization)
def sync_organization_to_tenants(sender, instance, **kwargs):
    """Sincroniza Organization para todos os tenants"""
    from django_tenants.utils import get_tenant_model
    from tenants_core.models import TenantOrganization
    
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        tenant.activate()
        TenantOrganization.objects.update_or_create(
            organization_id=instance.id,
            defaults={
                'name': instance.name,
                'slug': instance.slug,
            }
        )

@receiver(post_save, sender=Company)
def sync_company_to_tenants(sender, instance, **kwargs):
    """Sincroniza Company para todos os tenants"""
    from django_tenants.utils import get_tenant_model
    from tenants_core.models import TenantCompany
    
    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        tenant.activate()
        TenantCompany.objects.update_or_create(
            company_id=instance.id,
            defaults={
                'name': instance.name,
            }
        )
```

### PASSO 5: Data Migration Script (1 dia)

**Arquivo**: `management/commands/migrate_to_tenant_schemas.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from configuration.models import Organization, Company
from django_tenants.utils import get_tenant_model
from tenants_core.models import TenantUser, TenantOrganization, TenantCompany

User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **options):
        Tenant = get_tenant_model()
        
        # Para cada tenant
        for tenant in Tenant.objects.exclude(schema_name='public'):
            self.stdout.write(f"Processando tenant: {tenant.name}")
            tenant.activate()
            
            # 1. Sincronizar usuários
            for user in User.objects.all():
                TenantUser.objects.update_or_create(
                    user_id=user.id,
                    defaults={...}
                )
            
            # 2. Sincronizar organizações
            for org in Organization.objects.all():
                TenantOrganization.objects.update_or_create(...)
            
            # 3. Sincronizar companies
            for company in Company.objects.all():
                TenantCompany.objects.update_or_create(...)
            
            self.stdout.write(f"✓ {tenant.name} sincronizado")
```

---

## ✅ Checklist de Implementação

### Semana 1
- [ ] Criar modelos espelho em `tenants_core/models.py`
- [ ] Refatorar `gamification/models.py` (2 modelos)
- [ ] Refatorar `courses/models.py` (1 modelo)
- [ ] Refatorar `students/models.py` (1 modelo)
- [ ] Refatorar `audience/models.py` (1 modelo)
- [ ] Refatorar `library/models.py` (2 modelos)
- [ ] Refatorar `documents/models.py` (4 modelos)
- [ ] Testar cada refatoração

### Semana 2
- [ ] Criar migrations
- [ ] Implementar signals em `configuration/signals.py`
- [ ] Criar data migration script
- [ ] Testar sincronização

### Semana 3
- [ ] Aplicar migrations (--shared)
- [ ] Aplicar migrations (--tenant)
- [ ] Rodar data migration script
- [ ] Validar isolamento

### Semana 4
- [ ] Testes de segurança
- [ ] Bug fixes
- [ ] Documentação

---

## 🎯 Próximo Passo

Pronto para começar com **Passo 1: Criar Modelos Espelho**?

Quer que eu crie os arquivos agora?
