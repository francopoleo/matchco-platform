# Implementação Completa: TENANT_APPS Isolados (Schema Separado)

**Estratégia**: Como não temos legado, refatoramos de uma vez!  
**Prazo**: 1-2 sprints (3-4 semanas)  
**Risco**: Médio (bem planejado)  
**Ganho**: LGPD-ready, Enterprise-ready, Zero débito técnico

---

## 🎯 Visão Final (Fase 3 Completa)

```
Schema public (Shared - 30 tabelas)
├─ configuration_organization ← Qual empresa
├─ configuration_domain ← Domínios de acesso
├─ auth_user ← Login global
├─ user_management_* ← Perfil do usuário
├─ accounts_* ← Signup/login
├─ configuration_membership ← User → Organization mapping
└─ learning_publiccandidate ← Candidatos compartilhados

Schema shopping-xyz (50 tabelas)
├─ courses_course ← Cursos da Shop
├─ courses_module ← Módulos da Shop
├─ students_courseenroll ← Alunos da Shop
├─ gamification_* ← Pontos da Shop
├─ console_* ← Permissões da Shop
├─ chat_* ← Chat da Shop
└─ documents_* ← Documentos da Shop

Schema hospital-def (50 tabelas)
├─ courses_course ← Cursos do Hospital
├─ ... [ISOLADO]
└─ ... [SEM acesso aos dados da Shop]
```

---

## 🔧 Estratégia de Refatoração

### Problema 1: FKs Cross-Schema (SHARED → TENANT)

**Problema:**
```python
# Em TENANT_APPS
class Course(models.Model):
    organization = ForeignKey(Organization)  # ← SHARED_APPS!
    owner = ForeignKey(User)  # ← SHARED_APPS!
```

**Solução: Copiar dados de referência para cada schema**

```python
# Novo modelo em TENANT_APPS
class TenantOrganization(models.Model):
    """Espelho de Organization no schema tenant"""
    organization_id = IntegerField(primary_key=True)  # Same ID como public
    name = CharField()
    slug = SlugField()
    # Só dados necessários (sem FKs)

class TenantUser(models.Model):
    """Espelho de User no schema tenant"""
    user_id = IntegerField(primary_key=True)  # Same ID como public
    username = CharField()
    email = EmailField()
    # Só dados necessários

# Agora Course pode ter FK segura
class Course(models.Model):
    organization = ForeignKey(TenantOrganization, primary_key=organization_id)
    owner = ForeignKey(TenantUser, primary_key=user_id)
    name = CharField()
    # ...
```

### Problema 2: Sincronizar Dados entre Schemas

**Solução: Signals + Management Command**

```python
# models.py (organization em SHARED_APPS)
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Organization)
def sync_organization_to_tenant(sender, instance, created, **kwargs):
    """Quando organization muda em public, atualiza em todos os tenants"""
    from django_tenants.utils import get_tenant_model
    
    # Para cada tenant schema
    for tenant in get_tenant_model().objects.all():
        # Conecta ao schema do tenant
        tenant.activate()
        
        # Espelha dados
        TenantOrganization.objects.update_or_create(
            organization_id=instance.id,
            defaults={
                'name': instance.name,
                'slug': instance.slug,
            }
        )
```

### Problema 3: Compartilhar Candidatos entre Tenants

**Solução: Bridge Table no Schema Public**

```python
# learning/models.py (SHARED_APPS)
class PublicCandidate(models.Model):
    """Candidato compartilhado entre todos os tenants"""
    name = CharField()
    email = EmailField(unique=True)
    # ... dados públicos

class CandidateAccess(models.Model):
    """Qual tenant pode ver qual candidato"""
    candidate = ForeignKey(PublicCandidate)
    organization = ForeignKey(Organization)
    # Se job.organization == access.organization → pode ver!

# courses/models.py (TENANT_APPS)
class JobOffer(models.Model):
    """Oferta específica de uma empresa"""
    organization = ForeignKey(TenantOrganization)
    candidate_id = IntegerField()  # ID do PublicCandidate (não FK!)
    salary = DecimalField()
    
    def get_candidate(self):
        """Busca candidato do schema público"""
        from learning.models import PublicCandidate
        # Conecta ao schema público
        public_schema_connection = get_public_connection()
        return PublicCandidate.objects.using(public_schema_connection).get(id=self.candidate_id)
```

---

## 📋 Passo a Passo de Implementação (4 Semanas)

### **Semana 1: Preparação & Refatoração de Models**

**Dia 1-2: Análise de Dependências**
```bash
# Identificar todos os FKs entre SHARED ↔ TENANT
grep -r "ForeignKey.*Organization" courses/
grep -r "ForeignKey.*User" courses/
# Documentar em DEPENDENCY_MAP.md
```

**Dia 2-3: Criar Modelos Espelho**
```python
# Em cada TENANT_APP que precisa
class TenantOrganization(models.Model):
    organization_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=160)
    slug = models.SlugField()

class TenantUser(models.Model):
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150)
    email = models.EmailField()
```

**Dia 3-5: Refatorar Models**
```python
# Antes
class Course(models.Model):
    organization = ForeignKey(Organization)  # SHARED_APPS
    owner = ForeignKey(User)  # SHARED_APPS

# Depois
class Course(models.Model):
    organization = ForeignKey(TenantOrganization)  # TENANT_APPS
    owner = ForeignKey(TenantUser)  # TENANT_APPS
    # Adicionar métodos helper
    def get_real_organization(self):
        return Organization.objects.get(id=self.organization_id)
    def get_real_owner(self):
        return User.objects.get(id=self.owner_id)
```

### **Semana 2: Migrations & Data Sync**

**Dia 1: Criar Migrations**
```bash
python manage.py makemigrations courses students gamification console
# Vai criar migrations para criar os modelos espelho
```

**Dia 2: Implementar Signals**
```python
# configuration/signals.py
@receiver(post_save, sender=Organization)
def sync_org_to_tenants(sender, instance, **kwargs):
    for tenant in Organization.objects.exclude(schema_name='public'):
        tenant.activate()
        TenantOrganization.objects.update_or_create(
            organization_id=instance.id,
            defaults={'name': instance.name, 'slug': instance.slug}
        )

@receiver(post_save, sender=User)
def sync_user_to_tenants(sender, instance, **kwargs):
    # Similar para users
    pass
```

**Dia 3-4: Data Migration Script**
```python
# management/commands/migrate_to_tenant_schemas.py

def handle(self, *args, **options):
    # 1. Copiar dados de courses para schema tenant
    # 2. Copiar dados de students para schema tenant
    # 3. Validar integridade
    # 4. Deletar originals (opcional, ou manter ambos)
```

**Dia 5: Testar Isolamento**
```bash
# Script de teste
python manage.py test_tenant_isolation

# Verificar:
# - Shop não vê cursos do Hospital
# - Hospital não vê alunos da Shop
# - Dados sincronizam corretamente
```

### **Semana 3: Migrations Django-Tenants**

**Dia 1: Aplicar Migrations**
```bash
# Schema public
python manage.py migrate_schemas --shared

# Cada schema tenant
python manage.py migrate_schemas --tenant --schema=shopping-xyz
python manage.py migrate_schemas --tenant --schema=hospital-def
python manage.py migrate_schemas --tenant --schema=rede-abc
```

**Dia 2-3: Criar/Atualizar Views**
```python
# courses/views.py
def course_list(request):
    # Middleware já setou request.tenant
    tenant = request.tenant
    
    # Conecta ao schema do tenant automaticamente
    courses = Course.objects.filter(organization=tenant)
    return render(request, 'courses.html', {'courses': courses})
```

**Dia 4-5: Testes de Segurança**
```python
# Tentar acessar dados de outro tenant
# Deve falhar (404 ou 403)
```

### **Semana 4: Polish & Documentação**

**Dia 1-2: Bug Fixes**
- Queries cruzadas entre schemas
- Permissões por tenant
- Admin console por tenant

**Dia 3: Management Commands**
```bash
python manage.py create_tenant \
  --name "Nova Empresa" \
  --slug "nova-empresa" \
  --domain "nova-empresa.localhost"
```

**Dia 4-5: Documentação**
- Como criar novo tenant
- Como adicionar novo app isolado
- LGPD compliance checklist

---

## 🔐 Checklist de Segurança

```
Isolamento:
- [ ] Shop não consegue fazer query em Hospital
- [ ] Middleware força tenant correction
- [ ] Foreign keys seguros entre schemas

Dados Compartilhados:
- [ ] Candidatos públicos acessíveis
- [ ] JobOffers isoladas por empresa
- [ ] Permissions respeitadas

LGPD:
- [ ] Backup separado por tenant
- [ ] Direito ao esquecimento (delete schema)
- [ ] Auditoria de acessos
- [ ] Consentimento por empresa
```

---

## 📊 Comparação: Antes vs Depois

### ANTES (Fase 1B - Tudo em public)
```
Schema public:
├─ courses_course (Shop XXX, Hospital YYY, Rede ZZZ - MISTURADO!)
├─ students_courseenroll (dados misturados)
└─ gamification_report (sem isolamento)

Risk: SELECT * FROM courses_course ← VÊ TUDO
```

### DEPOIS (Fase 3 - Isolado)
```
Schema public:
├─ configuration_organization
├─ auth_user
└─ learning_publiccandidate

Schema shopping-xyz:
└─ courses_course (SÓ Shop) + students + gamification

Schema hospital-def:
└─ courses_course (SÓ Hospital) + students + gamification

Risk: SELECT * FROM courses_course ← VÊ APENAS Hospital
```

---

## 💰 Estimativa de Esforço

| Atividade | Horas | Pessoas |
|-----------|-------|---------|
| Análise Dependências | 8 | 1 |
| Refatorar Models | 16 | 1 |
| Criar Migrations | 8 | 1 |
| Implementar Signals | 12 | 1 |
| Data Migration | 16 | 1 |
| Testes Isolamento | 16 | 1-2 |
| Bugs/Polish | 12 | 1 |
| Documentação | 8 | 1 |
| **TOTAL** | **96h** | **1 dev** |

**Timeline:** 3-4 semanas (1 dev, 24h/semana)

---

## ✅ Decision: GO or NO GO?

### OPÇÃO A: Refatorar Completo Agora (Recomendado)
```
✅ Zero débito técnico
✅ Enterprise-ready desde dia 1
✅ LGPD-compliant
✅ Escalável para N tenants
✅ Sem refatoração futura

❌ Esforço inicial: 3-4 semanas
❌ Risco médio (mas bem controlado)
```

### OPÇÃO B: Fase 2 com Middleware Depois
```
✅ Rápido (1-2 semanas)
✅ Funcional para MVP

❌ Débito técnico acumula
❌ Refatoração futura será 2x mais cara
❌ Não é LGPD-ready
```

---

## 🎯 RECOMENDAÇÃO FINAL

**👍 OPÇÃO A - Refatorar Completo AGORA!**

**Porque:**
1. Não temos legado (advantage!)
2. Esforço é 3-4 semanas (não é tanto)
3. Futuro: zero débito técnico
4. LGPD-ready desde dia 1
5. Enterprise customers vão exigir isso

**Plano de Execução:**
```
Semana 1: Refatorar Models
Semana 2: Criar Signals + Data Migration
Semana 3: Migrations Django-Tenants + Testes
Semana 4: Polish + Go-Live
```

Quer que eu comece com a análise de dependências?
