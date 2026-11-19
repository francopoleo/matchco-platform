# Decisão Profissional: Arquitetura Híbrida em 1 Servidor

**Contexto:** Você desenvolve em DigitalOcean ou Contabo (1 servidor). Qual é a MELHOR PRÁTICA?

**Resposta:** Opção 3 Híbrida, mas implementada em 1 servidor com separação lógica.

---

## 🎯 A Decisão Profissional

### Por Que NÃO Opção 1 (Um Banco)?

```
❌ "Mas eu só tenho 1 servidor, vou usar um banco único"

Problema:
- Você desenvolve hábitos ruins (sem isolamento)
- Quando vender para cliente 1, estrutura é fraca
- Cliente questiona: "Meus dados estão seguros?"
- Refatorar depois é 10x mais caro (data migration)
- LGPD: Cliente não aprova (auditoria falha)

Resultado: Você vende, ganha R$2k/cliente/mês, mas:
- 3 clientes = 3 reclamações de segurança
- Refatora tudo = 3 meses perdidos
- Perde clientes = R$2k × 36 meses = R$72k perdido
```

### Por Que SIM Opção 3 (Híbrida, em 1 Servidor)?

```
✅ "Vou implementar Opção 3 mesmo com 1 servidor"

Vantagem:
- Você aprende a fazer certo desde o início
- Quando vender, estrutura já é profissional
- Cliente quer segurança? Você tem
- LGPD auditável? Está pronto
- Migrar para múltiplos servidores é 1 linha de config
- Quando crescer: zero refatoração

Resultado: Você vende profissionalmente
- 1º cliente: "Dados isolados? ✅ LGPD ready? ✅"
- 3º cliente: Mesma arquitetura, sem mudança de código
- Escala: ARR cresce, estrutura já suporta 100 clientes
```

---

## 🏗️ Implementação Profissional em 1 Servidor

### Estrutura Física: 1 PostgreSQL com N Schemas

```
CONTABO / DigitalOcean (1 servidor)
└─ PostgreSQL 14
   ├─ Schema: public (candidatos compartilhados)
   │  ├─ Table: public.users
   │  ├─ Table: public.applications
   │  └─ Table: public.organizations
   │
   └─ Schema: shopping_xyz (isolado logicamente)
      ├─ Table: shopping_xyz.organization_users
      ├─ Table: shopping_xyz.job_offers
      └─ Table: shopping_xyz.audit_logs
   
   └─ Schema: hospital_def (isolado logicamente)
      ├─ Table: hospital_def.organization_users
      ├─ Table: hospital_def.job_offers
      └─ Table: hospital_def.audit_logs
   
   └─ Schema: rede_abc (isolado logicamente)
      └─ ...
```

### Implementação Django

```python
# settings.py - Roteamento por Schema

DATABASES = {
    'public': {
        'ENGINE': 'django_multitenant',  # Plugin para multi-schema
        'NAME': 'matchco_production',  # DB única
        'USER': 'postgres',
        'HOST': '123.456.789.0',  # DigitalOcean/Contabo IP
        'SCHEMA': 'public',  # Schema para candidatos
    },
    'default': {  # Roteado dinamicamente
        'ENGINE': 'django_multitenant',
        'NAME': 'matchco_production',  # Mesma DB!
        'SCHEMA': 'default',  # Placeholder
    }
}

# middleware.py - Roteamento por Request

class MultiSchemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Detecta qual cliente (schema) usar
        organization_id = self.get_organization_id(request)
        
        if organization_id:
            schema_name = self.get_schema_for_organization(organization_id)
            request.schema_name = schema_name
            
            # Django-multitenant usa esse info
            request.tenant = Organization.objects.get(id=organization_id)
        else:
            request.schema_name = 'public'
        
        response = self.get_response(request)
        return response
    
    def get_schema_for_organization(self, org_id):
        """Retorna schema name para esta org"""
        mapping = {
            1: 'shopping_xyz',
            2: 'hospital_def',
            3: 'rede_abc',
        }
        return mapping.get(org_id, 'public')
```

### Instalação do Plugin

```bash
pip install django-multitenant
# Ou alternativa: django-tenants, django-organizations
```

---

## 💾 Migração Profissional

### Passo 1: Criar Schemas

```sql
-- Conecta ao DigitalOcean/Contabo PostgreSQL

-- Schema público (candidatos compartilhados)
CREATE SCHEMA IF NOT EXISTS public;

-- Schemas privados (dados por cliente)
CREATE SCHEMA IF NOT EXISTS shopping_xyz;
CREATE SCHEMA IF NOT EXISTS hospital_def;
CREATE SCHEMA IF NOT EXISTS rede_abc;

-- Role para isolamento (opcional, mas profissional)
CREATE ROLE shopping_admin LOGIN PASSWORD 'password';
GRANT USAGE ON SCHEMA shopping_xyz TO shopping_admin;
GRANT CREATE ON SCHEMA shopping_xyz TO shopping_admin;

CREATE ROLE hospital_admin LOGIN PASSWORD 'password';
GRANT USAGE ON SCHEMA hospital_def TO hospital_admin;
```

### Passo 2: Django Migrations por Schema

```bash
# Migra schema público
python manage.py migrate --database=public

# Migra schema shopping_xyz
python manage.py migrate_schema shopping_xyz

# Migra schema hospital_def
python manage.py migrate_schema hospital_def
```

### Passo 3: Isolamento de Queries

```python
# models.py

class PublicUser(models.Model):
    """Candidato compartilhado (schema public)"""
    email = EmailField(unique=True)
    first_name = CharField()
    
    class Meta:
        app_label = 'public'
        # Sempre usa schema 'public'

class OrganizationUser(models.Model):
    """Usuário por organização (schema isolado)"""
    public_user_id = IntegerField()  # Referência FK
    organization_id = IntegerField()
    
    class Meta:
        app_label = 'organizations'
        # Usa schema específico da org

# views.py

def get_candidates(request, org_id):
    # Detecta schema automaticamente
    request.schema_name = get_schema_for_org(org_id)
    
    # Query usa schema correto
    candidates = OrganizationUser.objects.filter(
        organization_id=org_id
    )
    # Django: usa schema_name do request
    
    return JsonResponse(candidates)
```

---

## 🔐 LGPD em 1 Servidor

### Backup Granular (Profissional)

```bash
#!/bin/bash
# backup_professional.sh

# Backup schema público (candidatos)
pg_dump -h 123.456.789.0 \
  -U postgres \
  -n public \
  matchco_production > backup_public_$(date +%Y%m%d).sql

# Backup schema shopping_xyz isolado
pg_dump -h 123.456.789.0 \
  -U postgres \
  -n shopping_xyz \
  matchco_production > backup_shopping_$(date +%Y%m%d).sql

# Backup schema hospital_def isolado
pg_dump -h 123.456.789.0 \
  -U postgres \
  -n hospital_def \
  matchco_production > backup_hospital_$(date +%Y%m%d).sql

# Criptografa backups
gpg --symmetric backup_public_*.sql
gpg --symmetric backup_shopping_*.sql
gpg --symmetric backup_hospital_*.sql

# Envia para storage (AWS S3, Google Cloud)
aws s3 cp backup_*.sql.gpg s3://matchco-backups/
```

### Direito ao Esquecimento (LGPD)

```python
def delete_candidate(email):
    """
    Apaga candidato de TODOS os schemas
    - Remove de matchco_public (soft delete)
    - Remove de todos os schemas privados
    """
    
    # 1. Encontra candidato no schema público
    public_user = PublicUser.objects.using('public').get(email=email)
    
    # 2. Soft delete (LGPD auditoria)
    public_user.deleted_at = now()
    public_user.email = f'deleted_{uuid.uuid4()}@deleted.local'
    public_user.save()
    
    # 3. Apaga de todos os schemas privados
    for org in Organization.objects.using('public').all():
        schema_name = get_schema_for_organization(org.id)
        
        OrganizationUser.objects.using(schema_name).filter(
            public_user_id=public_user.id
        ).update(deleted_at=now())
    
    # 4. Log auditoria
    AuditLog.objects.using('public').create(
        action='DELETE_USER',
        user_email=email,
        reason='LGPD Art. 17',
        timestamp=now()
    )
    
    return True
```

### Auditoria (Profissional)

```python
# models.py

class AuditLog(models.Model):
    """Log de quem acessou o quê (LGPD compliance)"""
    organization_id = IntegerField()
    admin_email = EmailField()
    action = CharField(
        choices=[
            ('VIEW_CANDIDATES', 'Viu lista de candidatos'),
            ('SENT_OFFER', 'Enviou oferta'),
            ('HIRED', 'Contratou candidato'),
            ('DELETED_DATA', 'Deletou dados'),
        ]
    )
    candidate_email = EmailField(null=True)
    timestamp = DateTimeField(auto_now_add=True)
    ip_address = GenericIPAddressField()
    
    class Meta:
        app_label = 'public'
        # Auditoria em schema público (compartilhado)
        # Protege contra: admin do Hospital se dizendo que foi Shopping

# views.py - Log automático

def send_job_offer(request, candidate_id):
    # ... lógica de oferta
    
    # Log: Quem enviou oferta para quem?
    AuditLog.objects.using('public').create(
        organization_id=request.organization_id,
        admin_email=request.user.email,
        action='SENT_OFFER',
        candidate_email=candidate.email,
        ip_address=get_client_ip(request)
    )
    
    return JsonResponse({'status': 'sent'})
```

---

## 📈 Escalabilidade: Do 1 Servidor para Múltiplos

### Fase 1: 1 Servidor (Hoje)
```
DigitalOcean/Contabo
└─ PostgreSQL (schemas: public, shopping_xyz, hospital_def)
└─ Django App
└─ Custo: ~R$50-100/mês
```

### Fase 2: 2 Servidores (Quando tiver 10+ clientes)
```
Servidor 1: PostgreSQL (AWS RDS)
└─ Schema: public (candidatos compartilhados)

Servidor 2: PostgreSQL (CloudSQL)
└─ Schema: shopping_xyz (isolado)

Mudar uma linha em settings.py:
  'shopping': {
    'HOST': 'shopping-private-db.cloudsql.io',  # ← Muda URL
  }

Código Django: ZERO mudança
```

### Fase 3: N Servidores (Quando tiver 100+ clientes)
```
Servidor Public: AWS RDS
└─ Schema: public

Servidor Shopping: CloudSQL
└─ Schema: shopping_xyz

Servidor Hospital: CloudSQL
└─ Schema: hospital_def

Servidor Rede: CloudSQL
└─ Schema: rede_abc

Cada cliente em seu próprio servidor (LGPD perfeito)
Código Django: ZERO mudança (router detecta automaticamente)
```

---

## ✅ Implementação Profissional em 1 Servidor

### Checklist

```
SEMANA 1: Setup Básico
[ ] Provisionar Contabo/DigitalOcean (512MB RAM mín, 20GB SSD)
[ ] Instalar PostgreSQL 14
[ ] Criar 3 schemas (public, shopping_xyz, hospital_def)
[ ] Instalar Django + django-multitenant
[ ] Testar roteamento (request → schema correto)

SEMANA 2: Models & Migrations
[ ] Criar PublicUser (schema public)
[ ] Criar OrganizationUser (schema privado)
[ ] Criar JobOffer (schema privado)
[ ] Criar AuditLog (schema public)
[ ] Migrations por schema funcionando

SEMANA 3: Queries & Views
[ ] View: listar candidatos (de 1 schema)
[ ] View: enviar oferta (isolado)
[ ] View: auditoria (completa)
[ ] Testar isolamento (Shop não vê Hospital)

SEMANA 4: LGPD & Segurança
[ ] Backup por schema (granular)
[ ] Direito ao esquecimento (soft delete)
[ ] Portabilidade (export JSON)
[ ] Consent management (qual org pode acessar)
[ ] Documentação LGPD pronta
```

---

## 💼 Resultado: Profissionalismo

Quando você vender para um cliente:

```
Cliente: "Vocês têm conformidade LGPD?"
Você: "Sim. Dados de cada cliente em schema isolado.
       Backup granular. Auditoria. Direito ao esquecimento.
       DPO pode auditar dados."

Cliente: "Quanto custa?"
Você: "R$2.000/mês"

Cliente: "OK, contrata!"
```

Se você tivesse feito Opção 1 (um banco):

```
Cliente: "Vocês têm conformidade LGPD?"
Você: "Uh... tecnicamente... há row-level security..."
Cliente: "Muito obrigado, vou com concorrente que tem..."
```

---

## 🎯 Comparação: Profissionalismo vs Atalho

| Decisão | Hoje | Depois (3 clientes) | Depois (100 clientes) |
|---------|------|---------------------|----------------------|
| **Opção 1** (1 banco) | Mais rápido | Refatora (3 meses) | Impossível |
| **Opção 3** (Híbrida) | 1 semana extra | ZERO refatoração | Escala naturalmente |

**Tempo extra hoje:** 1 semana  
**Tempo economizado depois:** 3 meses × 2 = 6 meses  
**Clientes perdidos evitados:** 3 × R$2k/mês × 12 meses = R$72k  

**ROI:** Fazer certo agora economiza R$72k depois.

---

## 🚀 Próximos Passos (Recomendação)

1. **Confirmação:** Opção 3 Híbrida em 1 servidor (Contabo/DigitalOcean)?
2. **Setup:** Provisionar servidor + PostgreSQL + schemas
3. **Django:** Instalar django-multitenant + configurar
4. **Testes:** Testar isolamento (Shop não vê Hospital)
5. **Go-Live:** Com estrutura profissional desde dia 1

**Resultado:** Quando você vender, é profissional. Sem refatoração.
