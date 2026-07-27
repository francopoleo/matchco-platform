# Plano de Desenvolvimento: Multi-Tenancy com Django-Tenants

**Status**: ✅ Fase 1 Concluída (Setup Local) | ⏳ Fase 2 Em Planejamento

---

## 📊 Estado Atual da Arquitetura

### Problema Identificado
```
Schema public (104 tabelas) ← TUDO aqui
├─ Organizations (todas as empresas)
├─ Users (todos os usuários)
├─ Courses, Students, JobOffers, etc
└─ Dados da empresa XXX, YYY, ZZZ misturados

Schema shopping-xyz ← VAZIO
Schema hospital-def ← VAZIO
Schema rede-abc ← VAZIO
  (Só têm django_migrations)
```

**Consequências:**
- ❌ SEM isolamento de dados entre tenants
- ❌ SEM compliance LGPD (não há segmentação)
- ❌ Usuários podem ver dados de outras empresas
- ✓ Funciona, mas não é production-ready

---

## ✅ Fase 1: Implementado (Local Dev)

```
✓ PostgreSQL com 4 schemas (public + 3 tenants)
✓ django-tenants middleware ativo
✓ Domain routing funcional
✓ Superadmin criado e com memberships
✓ Landing pages (/recrutamento/) funcionais
✓ Multi-tenant detection automático
```

---

## 📋 Fase 2: Isolamento de Dados (PRÓXIMA)

### 2.1 Separar Apps em SHARED_APPS e TENANT_APPS

**SHARED_APPS (Schema Public - Shared):**
```python
SHARED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    
    # Multi-tenancy
    'django_tenants',
    'configuration',  # Organizations, Domains, Memberships
    
    # Global/Shared
    'accounts',  # Login, signup (compartilhado)
    'user_management',  # Users (compartilhado)
    'latest_changes',  # Auditoria global
    
    # Public data (compartilhado entre tenants)
    'learning',  # PublicCandidates, shared trails
    'publishing',  # Public content
]
```

**TENANT_APPS (Schema tenant - Isolado):**
```python
TENANT_APPS = [
    # Dados isolados por empresa
    'courses',  # Cursos da empresa XXX
    'students',  # Alunos inscritos na empresa XXX
    'gamification',  # Pontos por empresa
    'console',  # Admin console por empresa
    'documents',  # Documentos da empresa
    'audience',  # Audiências por empresa
    'library',  # Biblioteca da empresa
    'chat',  # Chat da empresa
]
```

### 2.2 Criar Migrations para TENANT_APPS

```bash
# Após separar os apps:
python manage.py makemigrations
python manage.py migrate_schemas --shared  # Atualiza schema public
python manage.py migrate_schemas --tenant  # Cria tabelas em cada tenant
```

### 2.3 Dados Resultantes

```
Schema public (30 tabelas)
├─ auth_user (global)
├─ configuration_organization (todas as empresas)
├─ configuration_membership (user ↔ org)
├─ accounts_* (login/signup global)
├─ user_management_* (perfil de usuário global)
└─ learning_publiccandidate (candidatos compartilhados)

Schema shopping-xyz (40 tabelas)
├─ courses_course (cursos da Shopping XYZ)
├─ courses_module, courses_quiz
├─ students_courseenroll
├─ gamification_* (pontos da Shopping XYZ)
├─ console_* (permissões da Shopping XYZ)
└─ documents_* (documentos da Shopping XYZ)

Schema hospital-def (40 tabelas)
├─ courses_course (cursos do Hospital Def)
├─ ... [similar]
└─ ... [dados isolados]

Schema rede-abc (40 tabelas)
└─ [dados isolados]
```

---

## 👥 Administração de Usuários (Fase 2)

### Modelo de Acesso

```
┌─ Superadmin Global
│  ├─ User: superadmin (em schema public)
│  ├─ Memberships: Public, Shopping, Hospital, Rede
│  └─ Permissão: Tudo em todos os tenants
│
├─ Admin por Tenant (Shopping XYZ)
│  ├─ User: admin_shopping (em schema public)
│  ├─ Membership: shopping-xyz (is_primary=True)
│  └─ Permissão: Tudo na Shopping XYZ
│
├─ Usuário Normal (Gerente Loja)
│  ├─ User: gerente_loja_1 (em schema public)
│  ├─ Membership: shopping-xyz (role=manager)
│  └─ Permissão: Console + Relatórios da Shop
│
└─ Candidato/Aluno (Público)
   ├─ User: candidato_123 (em schema public, is_public=True)
   ├─ Membership: NENHUMA (não precisa)
   └─ Permissão: Signup, Landing pages, Cursos públicos
```

---

## 🏗️ Fase 3: Criação de Novas Empresas (PLANEJAMENTO)

### Donde fazer isso? Opções:

**OPÇÃO 1: Admin Panel (/admin/) - Recomendado para v1**
```
✅ Vantagens:
  - Implementação rápida (Django admin built-in)
  - Seguro (apenas superadmin)
  - Sem UI customizada necessária
  
❌ Desvantagens:
  - Interface não é user-friendly
  - Não automático
  - Requer conhecimento técnico
```

**Fluxo:**
```
1. Superadmin acessa /admin/
2. Configuration > Organization > Adicionar nova
3. Preenche: name, slug, is_public
4. Salva (cria schema automaticamente)
5. Volta para Organization > Domains
6. Adiciona domain: shopping-xyz.localhost
7. Cria Membership: superadmin → shopping-xyz
```

**OPÇÃO 2: Console de Admin (/console/admin-settings/) - Recomendado para v2**
```
✅ Vantagens:
  - Interface customizada e user-friendly
  - Automático (cria schema + domain + superadmin)
  - Pode oferecer para SaaS customers

❌ Desvantagens:
  - Desenvolvimento inicial maior
  - Mais complexo de manter
```

**Fluxo:**
```
1. Superadmin acessa /console/admin-settings/companies/
2. Clica "Criar Nova Empresa"
3. Preenche formulário (nome, slug, website, etc)
4. Sistema automático:
   a. Cria Organization
   b. Cria Schema no PostgreSQL
   c. Roda migrations no schema novo
   d. Cria Domain
   e. Cria primeiro Admin User
   f. Envia email com credenciais
```

**OPÇÃO 3: API para Onboarding - Recomendado para v3 (SaaS)**
```
POST /api/v1/organizations/create/
{
  "name": "Nova Empresa LTDA",
  "slug": "nova-empresa",
  "website": "https://nova-empresa.com",
  "admin_email": "admin@nova-empresa.com",
  "plan": "professional"
}

Response:
{
  "organization_id": 123,
  "schema_name": "nova-empresa",
  "admin_username": "admin_novo_empresa",
  "admin_password": "ABC123xyz",
  "setup_complete": true
}
```

---

## 👤 Atribuição de Superuser por Tenant

### Problema Atual
```
Só existe 1 superuser global: superadmin
Memberships são criadas manualmente

Como fica?
├─ superadmin (global) - acessa tudo
├─ admin_shopping (admin da Shop) - acessa só Shop
└─ admin_hospital (admin do Hospital) - acessa só Hospital
```

### Solução: Django Admin Groups + Permissions por Tenant

```python
# models.py
class TenantAdminGroup(models.Model):
    """Define quem é admin de qual tenant"""
    organization = ForeignKey(Organization)
    user = ForeignKey(User)
    role = CharField(choices=[
        ('owner', 'Owner - Acesso total'),
        ('admin', 'Admin - Gerenciar usuários'),
        ('manager', 'Manager - Relatórios'),
    ])

# Criar no admin
admin_shopping = User.objects.create_user(
    username='admin_shopping',
    email='admin@shopping-xyz.com',
    password='Admin@Shop123!'
)

TenantAdminGroup.objects.create(
    organization=shopping_xyz_org,
    user=admin_shopping,
    role='owner'  # Pode fazer tudo na Shopping
)
```

---

## 📋 Roadmap Detalhado (Recomendado)

### Semana 1: Separar Apps
- [ ] Mover `courses`, `students`, `gamification` para `TENANT_APPS`
- [ ] Mover `accounts`, `user_management` para `SHARED_APPS`
- [ ] Criar migrations
- [ ] Testar isolamento (Shop não vê Hospital)

### Semana 2: Admin por Tenant
- [ ] Criar modelo `TenantAdminGroup`
- [ ] Adicionar middleware de permissão por tenant
- [ ] Testar console.views com isolamento
- [ ] Criar first admin quando organização é criada

### Semana 3: Criação de Empresas (v1 - Manual)
- [ ] Criar management command: `python manage.py create_tenant`
  ```bash
  python manage.py create_tenant \
    --name "Shopping XYZ" \
    --slug "shopping-xyz" \
    --domain "shopping-xyz.localhost" \
    --admin-email "admin@shopping.com"
  ```

### Semana 4: Console Admin (v1)
- [ ] Criar /console/organizations/create/
- [ ] Validar slug único
- [ ] Validar domain único
- [ ] Criar schema + migrations automático
- [ ] Enviar email com credenciais

### Semana 5: Testes & Documentação
- [ ] Testes de isolamento (segurança)
- [ ] Testes de permissões por tenant
- [ ] Documentação para ops (criar nova empresa)
- [ ] Runbook para troubleshooting

---

## 🔒 Checklist de Segurança (LGPD)

```
Isolamento de Dados:
- [ ] Dados da Shop nunca são vistos por Hospital
- [ ] Queries automáticas filtram por tenant
- [ ] Backups separados por tenant

Auditoria:
- [ ] Log de quem acessou o quê
- [ ] Log de criação/exclusão de organizações
- [ ] Log de atribuição de permissions

LGPD:
- [ ] Direito ao esquecimento (delete user across all tenants)
- [ ] Portabilidade (export data de 1 tenant)
- [ ] Consentimento (track consent per tenant)
```

---

## 📊 Comparação: Onde Fazer Onboarding?

| Aspecto | Admin Panel | Console Admin | API SaaS |
|---------|-----------|---------------|----------|
| **Tempo Dev** | 1 dia | 1 semana | 2 semanas |
| **User-Friendly** | ❌ | ✅ | ✅ |
| **Automático** | ❌ Manual | ✅ Semi | ✅ Total |
| **Para Quem** | Superadmin | Superadmin | Customers |
| **v1 Recomendado** | ✅ Sim | Não | Não |
| **v2 Recomendado** | Opcional | ✅ Sim | Não |
| **v3+ Recomendado** | Não | Opcional | ✅ Sim |

---

## 🎯 Recomendação Final

**Para v1.0 (Agora - Local Dev):**
1. ✅ Implementar Separação de Apps (SHARED vs TENANT)
2. ✅ Criar management command `create_tenant`
3. ✅ Criar migrations e testar isolamento
4. ✅ Documentar processo de onboarding manual

**Para v1.1 (2 semanas):**
5. Criar Console Admin UI simples (/console/organizations/create/)
6. Automático: Schema + Domain + First Admin

**Para v2.0 (Futuro - SaaS):**
7. API de onboarding
8. Self-service signup (Customers criam suas próprias organizações)

---

## 📝 Próximos Passos

**Imediato (hoje):**
```bash
# 1. Fazer commit do multi-tenant setup
git add .
git commit -m "feat: multi-tenant setup com django-tenants (local dev)"

# 2. Criar branch para Phase 2
git checkout -b feature/tenant-data-isolation
```

**Próxima Sprint:**
1. Separar Apps em SHARED_APPS / TENANT_APPS
2. Criar management command create_tenant
3. Testar isolamento de dados

Quer que eu comece com a Fase 2 agora?
