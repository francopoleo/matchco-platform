# Strategy: Separação de Apps em SHARED_APPS vs TENANT_APPS

**Data**: 27 Jul 2026  
**Status**: 🟡 Phase 1B (Documented, Staged Implementation)

---

## ⚠️ O Desafio Real

### Descoberta: Não é Simples Separar!

Tentei separar `gamification`, `courses`, `students` para TENANT_APPS, mas encontrei:

```
❌ Problema: Dependências Circulares
courses_course
  ├─ FK: organization (configuration.Organization) ← SHARED_APPS
  ├─ FK: owner (auth.User) ← SHARED_APPS
  └─ FK: content_category (courses.ContentCategory) ← TENANT_APPS

students_courseenroll
  ├─ FK: course (courses.Course) ← TENANT_APPS
  └─ FK: user (auth.User) ← SHARED_APPS

gamification_report
  ├─ FK: user (auth.User) ← SHARED_APPS
  └─ FK: organization (configuration.Organization) ← SHARED_APPS
```

**Resultado:**
- Apps em TENANT_APPS precisam de tabelas em SHARED_APPS
- Django-tenants não consegue criar tabelas automaticamente
- Precisa de refatoração de models ANTES de separar

---

## 🎯 Solução: 3 Fases Progressivas

### Fase 1B (Atual - Estável ✅)
**Tudo em SHARED_APPS (schema public)**

```
Schema public: 100+ tabelas (tudo)
├─ SHARED: configuration, accounts, user_management
├─ TENANT: gamification, courses, students (mas no schema público)
└─ Resultado: Funciona, mas SEM isolamento

Schema tenant (shopping-xyz, hospital-def, rede-abc):
└─ django_migrations (vazio)
```

**Vantagem:** Sistema funcional, sem refatoração

**Desvantagem:** Sem isolamento (pode ver dados de outras empresas via queries)

---

### Fase 2 (Next Sprint - Isolamento via Middleware)
**Tudo em SHARED_APPS + Isolamento via Middleware**

Mesmo banco/schema, mas:
1. Middleware detecta `request.tenant`
2. Queries automáticas filtram por `organization=request.organization`
3. Usuário da Shop só vê dados da Shop

```python
# models.py
class Course(models.Model):
    organization = ForeignKey(Organization)
    name = CharField()
    
    def __manager__(self):
        # Middleware injeta: get_queryset().filter(organization=request.organization)
        pass

# views.py
def course_list(request):
    # Sem filtro explícito, middleware cuida!
    courses = Course.objects.all()  # ← Automático: filtra por tenant
    return render(request, 'courses.html', {'courses': courses})
```

**Vantagem:**
- Isolamento automático
- SEM refatoração de models
- Funciona para LGPD (dados não "vazam")

**Desvantagem:**
- Tecnicamente tudo em mesmo schema
- Mais lento que schema isolado
- Requer middleware bem testado

---

### Fase 3 (Production - Schema Isolado)
**SHARED_APPS em schema public, TENANT_APPS em schema tenant**

```
Schema public (30 tabelas):
├─ configuration_organization
├─ auth_user
├─ user_management_*
├─ accounts_*
└─ learning_publiccandidate

Schema shopping-xyz (40 tabelas):
├─ courses_course (SÓ da Shop)
├─ students_courseenroll (SÓ da Shop)
├─ gamification_* (SÓ da Shop)
├─ console_* (SÓ da Shop)
└─ chat_* (SÓ da Shop)

Schema hospital-def (40 tabelas):
├─ courses_course (SÓ do Hospital)
├─ ... [isolado]
```

**Vantagem:**
- Máximo isolamento
- LGPD completo (dados fisicamente separados)
- Melhor performance (menos dados por query)
- Pode deletar tenant inteiro (schema drop)

**Desvantagem:**
- Refatoração significativa
- Models com FK entre SHARED ↔ TENANT precisam ser cuidadosos
- Mais complexo de desenvolver

---

## 📋 Roadmap Detalhado

### Fase 1B (Agora ✅)
```
✅ Setup local com django-tenants
✅ Multi-domain routing (colabore.ddns.net)
✅ Superadmin com múltiplas memberships
✅ Landing pages funcionando
✅ Documentação arquitetura
```

### Fase 2 (1-2 Semanas)
```
1. Criar TenantMiddleware que:
   - Detecta request.tenant
   - Filtra automáticamente por organization
   
2. Adicionar a models.py:
   class TenantManager(models.Manager):
       def get_queryset(self):
           return super().get_queryset().filter(
               organization=get_current_tenant()
           )
   
3. Testar isolamento:
   - Shop vê só suas courses
   - Hospital não vê Shop's students
   
4. Criar management command:
   python manage.py create_tenant \
     --name "Nova Shop" \
     --slug "nova-shop" \
     --domain "nova-shop.localhost"
```

### Fase 3 (3+ Semanas)
```
1. Identificar models que podem ser TENANT:
   ✓ courses (empresa específica)
   ✓ students (empresa específica)
   ✓ gamification (empresa específica)
   
2. Refatorar models para remover FKs perigosas:
   - Ao invés de: course.organization_id
   - Usar: course.get_organization() via middleware
   
3. Criar migrations tenant-specific
4. Migrar dados: public → tenant schemas
5. Validar isolamento
```

---

## 🔧 Como Funciona Hoje (Fase 1B)

### Sem Isolamento (PROBLEMA)
```python
# Shop Admin acessa /console/
courses = Course.objects.all()  # ← VÊ TUDO (Shop + Hospital + Rede)
```

### Com TenantMiddleware (Fase 2)
```python
# Shop Admin acessa /console/
courses = Course.objects.all()  # ← TenantMiddleware filtra
# Internamente: Course.objects.filter(organization=shopping_xyz)

# Resultado: VÊ APENAS Shop
```

### Com Schema Isolado (Fase 3)
```python
# Shop Admin acessa /console/
# Middleware: routing automático para schema shopping-xyz
courses = Course.objects.all()  # ← Schema shopping-xyz (só 50 courses da Shop)

# Hospital Admin acessa /console/
# Middleware: routing automático para schema hospital-def
courses = Course.objects.all()  # ← Schema hospital-def (só 100 courses do Hospital)
```

---

## ✅ Checklist Implementação

### Fase 1B (FEITO)
- [x] PostgreSQL multi-schema setup
- [x] django-tenants middleware
- [x] Domain routing
- [x] Superadmin
- [x] Local dev funcional

### Fase 2 (PRÓXIMO)
- [ ] TenantMiddleware for auto-filtering
- [ ] management command create_tenant
- [ ] Test isolamento (Shop ≠ Hospital)
- [ ] Console UI

### Fase 3 (FUTURO)
- [ ] Refatorar models
- [ ] Separar SHARED_APPS ↔ TENANT_APPS
- [ ] Migrar dados
- [ ] Schema isolado validado

---

## 🚨 Configuração Atual (Fase 1B)

```python
# cep/settings/base.py

SHARED_APPS = [
    'django_tenants',
    'configuration',       # Organizations (global)
    'accounts',            # Login (global)
    'user_management',     # Users (global)
    'courses',             # Atualmente compartilhado
    'students',            # Atualmente compartilhado
    'gamification',        # Atualmente compartilhado
    'chat',                # Atualmente compartilhado
    'console',             # Atualmente compartilhado
    # ...
]

TENANT_APPS = [
    'tenants_core',  # Placeholder apenas
]

# TODO Fase 2:
# Mover para TENANT_APPS: courses, students, gamification, console, chat
# Criar TenantManager que filtra por organization automaticamente

# TODO Fase 3:
# Refatorar models para remover FKs entre SHARED ↔ TENANT
```

---

## 📚 Referências

- Django-Tenants Docs: https://django-tenants.readthedocs.io/
- Multi-Tenant Architecture: https://en.wikipedia.org/wiki/Multitenancy
- LGPD Compliance: Isolamento + Auditoria + Backup por tenant

---

## 💬 Recomendação

**Para v1.0 (Now):** Ficar em Fase 1B
- ✅ Simples, funcional, low risk
- ✅ Permite onboarding de clientes
- ✅ Pode evoluir para Fase 2/3

**Para v1.1 (2 semanas):** Implementar Fase 2
- TenantMiddleware for auto-filtering
- Management command for new tenants
- Isolamento via middleware (suficiente para MVP)

**Para v2.0 (Futuro):** Migrar para Fase 3
- Verdadeiro isolamento de schema
- LGPD fully compliant
- Pronto para enterprise customers
