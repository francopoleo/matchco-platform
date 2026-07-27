# Talk Recruitment: Estratégia de Infraestrutura & Arquitetura Multi-Tenant

**Data:** 2026-07-27  
**Escopo:** Decisão arquitetural para suportar múltiplos clientes (Shopping, Rede Varejo, Hospital, etc)  
**Questão Central:** Um banco de dados vs múltiplos bancos? Como permitir candidato "roaming" sem complexidade?

---

## 📊 Parte 1: Entendendo o Seu Negócio

### Modelo de Negócio Atual

```
Você vende a PLATAFORMA TALK RECRUITMENT para diferentes clientes:

CLIENTE 1: Shopping XYZ
├─ Organização: Shopping XYZ
├─ Hierarquia:
│  ├─ Loja 1 (Unidade: Feminino)
│  ├─ Loja 2 (Unidade: Esporte)
│  └─ Loja 3 (Unidade: Eletrônicos)
├─ Funções: Vendedor, Gerente, Operacional, Caixa
└─ Candidatos: ~200 (vagas mensais)

CLIENTE 2: Rede de Varejo ABC
├─ Organização: Rede ABC
├─ Hierarquia:
│  ├─ Loja São Paulo (Unidade distribuída)
│  ├─ Loja Rio (Unidade distribuída)
│  └─ Loja Brasília (Unidade distribuída)
├─ Funções: Vendedor, Supervisor, Gerente (mesmas para todas)
└─ Candidatos: ~500 (vagas mensais)

CLIENTE 3: Hospital DEF
├─ Organização: Hospital DEF
├─ Hierarquia:
│  ├─ Departamento: Enfermagem
│  ├─ Departamento: Médicos
│  └─ Departamento: Administrativo
├─ Unidades: Hospital Central, Unidade Satélite, Lab
├─ Funções: Médico, Enfermeiro, Técnico, Admin
└─ Candidatos: ~100 (vagas mensais)
```

### O Problema

```
Hoje: Tudo em UM BANCO DE DADOS (multi-tenant)

Questão 1: Candidato Compartilhado
├─ João se cadastra via QR Code do Shopping XYZ
├─ Depois quer se aplicar no Hospital DEF
├─ Precisa de novo cadastro? Ou reutiliza João do Shopping?
│
└─ Desejável: João existe UMA VEZ, visível para ambos

Questão 2: Isolamento de Dados (LGPD)
├─ Dados de João no Shopping estão na mesma tabela de Hospital
├─ O que impede Admin do Hospital ver dados do Shopping?
├─ LGPD: Cliente Hospital precisa garantir que dados de Hospital estão segregados
│
└─ Risco: Um erro de query (WHERE organization_id missing) vaza dados

Questão 3: Flexibilidade vs Complexidade
├─ Opção A: Um banco (mais simples, mas risco LGPD)
├─ Opção B: Múltiplos bancos (LGPD OK, mas candidatos não compartilham)
├─ Opção C: Híbrido (candidatos compartilham, dados isolados)
│
└─ Qual escolher?
```

---

## 🏗️ Parte 2: Três Opções de Arquitetura

### Opção 1: Um Banco de Dados (Multi-Tenant Clássico)

```
├─ Banco: talk_production
│  ├─ Table: organizations (Shopping XYZ, Rede ABC, Hospital DEF)
│  ├─ Table: users (João, Maria, Pedro)
│  ├─ Table: candidate_profiles (João → score 78, Maria → score 65)
│  ├─ Table: job_offers (João contratado no Shopping, depois no Hospital)
│  └─ Table: audit_logs (quem acessou o quê)

Isolamento: Row-Level Security (organization_id)
```

#### Implementação

```python
class User(models.Model):
    first_name = CharField()
    last_name = CharField()
    email = EmailField(unique=True)  # ← Chave global
    
    organizations = ManyToManyField(Organization)  
    # João aparece em {Shopping, Hospital}

class CandidateProfile(models.Model):
    user = ForeignKey(User)
    organization = ForeignKey(Organization)  # ← Isolamento
    score = IntegerField()
    
    class Meta:
        unique_together = ['user', 'organization']
        # João pode ter scores diferentes em cada org
```

#### Fluxo: João em Múltiplos Clientes

```
1. João cadastra no Shopping XYZ (via QR)
   └─ User.email = "joao@email.com"
   └─ User.organizations = [Shopping XYZ]
   └─ CandidateProfile(João, Shopping XYZ, score=78)

2. João escaneia QR do Hospital DEF
   └─ Sistema reconhece email
   └─ User.organizations.add(Hospital DEF)
   └─ CandidateProfile(João, Hospital DEF, score=???)

3. João faz entrevista do Hospital
   └─ Score diferente por org: Hospital score=82, Shopping score=78

4. HR do Shopping busca: "Vendedores score 70+, CEP 01310"
   └─ Query: SELECT * FROM candidate_profile 
       WHERE organization_id=Shopping AND score >= 70
   └─ Resultado: João

5. HR do Hospital busca: "Enfermeiros score 75+, CEP 01310"
   └─ Query: SELECT * FROM candidate_profile 
       WHERE organization_id=Hospital AND score >= 75
   └─ Resultado: João
```

#### Análise LGPD

```
✅ Bom:
  - Row-Level Security garante isolamento de dados
  - Auditoria: Qual admin acessou qual organização
  
❌ Ruim:
  - Um erro de query (WHERE organization_id missing) afeta todas as orgs
  - Backup único: se disaster recovery, recupera tudo junto
  - Admin central tem acesso a tudo (confiança necessária)
  - Conformidade: Cliente Hospital precisa confiar em você 100%
  - Limite de espaço: 3 clientes = OK, 100 clientes = risco
```

#### Prós & Contras

| Aspecto | Pro | Con |
|---------|-----|-----|
| Candidato Compartilhado | ✅ João UMA VEZ | N/A |
| Infraestrutura | ✅ Simples | N/A |
| LGPD | ✅ Básico | ❌ Risco de leak |
| Escalabilidade | ✅ Começo fácil | ❌ Limite ~50 clientes |
| Segurança | ⚠️ Depende de código | ❌ Ponto único falha |
| Conformidade | ⚠️ Cliente deve confiar | ❌ Auditoria complexa |

---

### Opção 2: Múltiplos Bancos de Dados (Instância por Cliente)

```
├─ Banco: talk_shopping_xyz
│  ├─ users (João, Maria)
│  ├─ candidate_profiles (apenas do Shopping)
│  └─ audit_logs
│
├─ Banco: talk_rede_abc
│  ├─ users (Pedro, Ana)
│  ├─ candidate_profiles (apenas da Rede)
│  └─ audit_logs
│
└─ Banco: talk_hospital_def
   ├─ users (Carlos, Paula)
   ├─ candidate_profiles (apenas do Hospital)
   └─ audit_logs

+ Banco Central: talk_shared
  ├─ organizations (metadados)
  ├─ connection_strings (qual banco pra qual cliente)
  └─ subscriptions (cobrança)
```

#### Implementação

```python
# settings.py
DATABASES = {
    'default': {  # Central
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talk_shared',
        'HOST': 'localhost',
    },
    'shopping': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talk_shopping_xyz',
        'HOST': 'localhost',
    },
    'hospital': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talk_hospital_def',
        'HOST': 'localhost',
    },
}

# views.py
def get_database_for_organization(org_slug):
    """Retorna qual banco usar para esta organização"""
    mapping = {
        'shopping-xyz': 'shopping',
        'hospital-def': 'hospital',
    }
    return mapping.get(org_slug, 'default')

class CandidateListView(View):
    def get(self, request, org_slug):
        db = get_database_for_organization(org_slug)
        
        candidates = CandidateProfile.objects.using(db).filter(score__gte=70)
        return JsonResponse(candidates)
```

#### Fluxo: João em Múltiplos Clientes

```
1. João cadastra no Shopping XYZ
   └─ Banco: talk_shopping_xyz
   └─ User(João) criado
   └─ CandidateProfile(João, score=78) criado

2. João escaneia QR do Hospital DEF
   └─ Sistema detecta email "joao@email.com"
   └─ Mas João não existe em talk_hospital_def
   └─ Opções:
      a) Criar novo usuário (João_H) no banco Hospital
      b) Replicar João do Shopping para Hospital (sync)
      c) Rejeitar (João só do Shopping)
   
   └─ Resultado: João existe 2x (em bancos diferentes)

3. João faz entrevista do Hospital
   └─ Banco: talk_hospital_def
   └─ CandidateProfile(João_H, score=82)

4. Candidato Roaming: ❌ Não funciona
   └─ João do Shopping e João do Hospital são DIFERENTES
   └─ Sem sincronização, são como 2 pessoas
```

#### Análise LGPD

```
✅ Bom:
  - Isolamento completo (dados Hospital nunca no banco Shopping)
  - Segurança: Um hack no Shopping não afeta Hospital
  - Conformidade: Hospital pode auditar seu próprio banco
  - Backup: Cada cliente tem seu backup isolado
  - Conformidade regulatória: Mais fácil atender requisitos específicos

❌ Ruim:
  - Candidato compartilhado: ❌ Não existe
  - Infraestrutura: Complexa (N bancos de dados)
  - DevOps: Gerenciar migrations em múltiplos bancos
  - Escalabilidade: 100 clientes = 100 bancos
  - Replicação: Se quiser candidato compartilhado, precisa sync manual
```

#### Prós & Contras

| Aspecto | Pro | Con |
|---------|-----|-----|
| Candidato Compartilhado | ❌ João é 2 pessoas | ❌ Sem roaming |
| Infraestrutura | N/A | ❌ Complexa |
| LGPD | ✅ Isolamento perfeito | N/A |
| Escalabilidade | N/A | ❌ Limite infraestrutura |
| Segurança | ✅ Forte | N/A |
| Conformidade | ✅ Máxima | N/A |

---

### Opção 3: Híbrido (RECOMENDADO) ⭐

```
├─ Banco PÚBLICO: talk_public
│  ├─ users (João, Maria, Pedro)  ← Candidatos UMA VEZ
│  ├─ public_profiles (score genérico)
│  └─ public_applications (João se aplicou a Shopping, Hospital)
│
└─ Bancos PRIVADOS: talk_shopping_xyz, talk_hospital_def, talk_rede_abc
   ├─ user_references (referência para João no banco público)
   ├─ candidate_profiles (score específico por org)
   ├─ job_offers
   ├─ audit_logs
   └─ sensitive_data (dados sensíveis da org)

ISOLAMENTO:
  - Dados públicos (candidatos): compartilhados
  - Dados sensíveis (contratação, salário, feedback): isolados por org
```

#### Implementação

```python
# Banco PÚBLICO

class PublicUser(models.Model):
    """Candidato compartilhado entre todas as orgs"""
    email = EmailField(unique=True)
    first_name = CharField()
    last_name = CharField()
    cep = CharField(max_length=8)
    
    created_at = DateTimeField(auto_now_add=True)
    
    # Score genérico (compartilhado)
    generic_score = IntegerField(default=0)  # 0-100

class PublicApplication(models.Model):
    """Histórico: João se aplicou em qual org?"""
    user = ForeignKey(PublicUser)
    organization_id = IntegerField()  # Referência ao org (não FK)
    applied_at = DateTimeField(auto_now_add=True)
    status = CharField(choices=['pending', 'interview', 'offered', 'hired'])

# Bancos PRIVADOS (um por org)

class OrganizationUser(models.Model):
    """Referência ao candidato público"""
    public_user_id = IntegerField()  # Referência ao PublicUser
    organization = ForeignKey(Organization, on_delete=models.CASCADE)
    
    # Score específico dessa org
    org_specific_score = IntegerField(default=0)
    
    # Dados sensíveis
    interview_feedback = TextField(blank=True)
    hiring_notes = TextField(blank=True)
    salary_offered = DecimalField(max_digits=10, decimal_places=2, null=True)

class JobOffer(models.Model):
    """Ofertas de emprego (isoladas por org)"""
    organization = ForeignKey(Organization)
    user = ForeignKey(OrganizationUser)
    salary = DecimalField()
    position = CharField()
    status = CharField(choices=['pending', 'accepted', 'rejected'])
```

#### Fluxo: João em Múltiplos Clientes

```
1. João cadastra no Shopping XYZ (via QR)
   └─ Banco Público:
      └─ PublicUser(email="joao@email.com", score=0)
   └─ Banco Private (talk_shopping_xyz):
      └─ OrganizationUser(public_user_id=1, org_specific_score=78)
   └─ PublicApplication(user=João, org=Shopping, status='pending')

2. João faz entrevista Shopping
   └─ Score atualiza: Shopping score = 78
   └─ Banco Público: generic_score = 78

3. João escaneia QR do Hospital DEF
   └─ Sistema reconhece email "joao@email.com"
   └─ Banco Público: Já existe? ✅ Sim
   └─ PublicApplication: add (João, Hospital, status='pending')
   └─ Banco Private (talk_hospital_def):
      └─ OrganizationUser(public_user_id=1, org_specific_score=0)

4. João faz entrevista Hospital
   └─ Score atualiza: Hospital score = 82
   └─ Banco Público: generic_score = max(78, 82) = 82
   └─ Banco Private (hospital): org_specific_score = 82

5. HR do Shopping busca: "Vendedores score 70+, CEP 01310"
   └─ Conexão: banco talk_shopping_xyz
   └─ Query: SELECT ou FROM organization_user 
       WHERE org_specific_score >= 70
   └─ Resultado: João (score 78)
   └─ Dados sensíveis isolados (feedback, salário não vê hospital)

6. HR do Hospital busca: "Enfermeiros score 75+, CEP 01310"
   └─ Conexão: banco talk_hospital_def
   └─ Query: SELECT * FROM organization_user 
       WHERE org_specific_score >= 75
   └─ Resultado: João (score 82)
   └─ Dados sensíveis isolados (não vê dados Shopping)
```

#### Análise LGPD

```
✅ Bom:
  - Candidato compartilhado: ✅ João UMA VEZ
  - Isolamento de sensíveis: ✅ Cada org seu banco
  - Segurança: Um hack no Shopping não afeta Hospital
  - Conformidade: Hospital audita seu próprio banco
  - LGPD: Dados pessoais (nome, email) compartilhados
          Dados sensíveis (salário, feedback) isolados
  - Escalabilidade: Suporta centenas de clientes
  
❌ Ruim:
  - Um pouco mais complexo (mas gerenciável)
  - Sincronização genérico_score precisa de cuidado
  - Replicação de candidatos entre bancos
```

#### Prós & Contras

| Aspecto | Pro | Con |
|---------|-----|-----|
| Candidato Compartilhado | ✅ João UMA VEZ | ⚠️ Referência cruzada |
| Infraestrutura | ⚠️ Moderada | N/A |
| LGPD | ✅ Forte | N/A |
| Escalabilidade | ✅ Alta | N/A |
| Segurança | ✅ Alto | N/A |
| Conformidade | ✅ Máxima | N/A |

---

## 🎯 Parte 3: Recomendação Final

### RECOMENDADO: Opção 3 (Híbrido)

**Por quê?**

```
1. Candidato Compartilhado: ✅
   - João cadastra UMA VEZ
   - Visível para Shopping, Hospital, Rede
   - Sem duplicação

2. LGPD Compliance: ✅✅
   - Dados públicos (nome, email): banco compartilhado
   - Dados sensíveis (salário, feedback): banco isolado
   - Cada cliente tem seu próprio banco para auditoria
   - Conformidade regulatória clara

3. Escalabilidade: ✅
   - Suporta 1 cliente (hoje)
   - Suporta 100+ clientes (futuro)
   - Sem mudança de arquitetura

4. Simplicidade: ✅
   - Candidato roaming funciona naturalmente
   - Sem sync complexo
   - Sem migração forçada depois

5. Segurança: ✅
   - Um hack em Shopping não afeta Hospital
   - Isolamento em nível de banco de dados
   - Backup granular
```

### Por Que NÃO as Outras?

```
Opção 1 (Um Banco):
  ❌ LGPD fraco
  ❌ Cliente Hospital tem que confiar 100%
  ❌ Risco de leak entre clientes
  ❌ Não escala além de 50 clientes
  
  Use para: Fase 0 (prototype, antes de vender)

Opção 2 (Múltiplos Bancos):
  ❌ Candidato não compartilha
  ❌ Infraestrutura cara (N bancos)
  ❌ DevOps complexo
  ❌ João é 2 pessoas diferentes
  
  Use para: Clientes enterprise (banca, governo)
```

---

## 🏗️ Parte 4: Arquitetura Detalhada (Híbrida)

### Estrutura de Bancos

```
INFRAESTRUTURA FÍSICA:

PostgreSQL Server 1 (Cloud: AWS RDS)
├─ talk_public (candidatos compartilhados)
└─ Réplica read (analytics, backups)

PostgreSQL Server 2-N (CloudSQL por cliente)
├─ talk_shopping_xyz (isolado)
├─ talk_hospital_def (isolado)
├─ talk_rede_abc (isolado)
└─ ...talk_cliente_n (isolado)

Recomendação:
  - talk_public: AWS RDS (postgres.c5.large)
  - talk_client_*: CloudSQL small (escala conforme necessário)
```

### Roteamento de Conexão

```python
# settings.py

DATABASES = {
    'public': {  # Compartilhado
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talk_public',
        'HOST': 'aws-rds.amazonaws.com',
        'USER': 'talk_prod',
        'PASSWORD': os.environ['DB_PUBLIC_PASSWORD'],
    },
    'default': {  # Roteado dinamicamente
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talk_default',  # Placeholder
    }
}

# middleware.py

class DynamicDatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'public':
            return 'public'
        
        # Pega organization_id do request
        org_id = hints.get('organization_id')
        if org_id:
            db_name = get_database_for_organization(org_id)
            return db_name
        
        return 'default'
    
    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

def get_database_for_organization(org_id):
    """Retorna qual banco PostgreSQL usar"""
    # Cache em Redis por 1 hora
    cache_key = f'org_db_mapping:{org_id}'
    db_name = cache.get(cache_key)
    
    if not db_name:
        org = Organization.objects.using('public').get(id=org_id)
        db_name = org.database_name  # Ex: 'talk_shopping_xyz'
        cache.set(cache_key, db_name, 3600)
    
    return db_name
```

### Tabelas por Banco

```
BANCO PUBLIC (talk_public):
├─ Table: organizations
│  ├─ id
│  ├─ name (Shopping XYZ, Hospital DEF, etc)
│  ├─ slug (shopping-xyz, hospital-def)
│  ├─ segment (varejo, hospital)
│  ├─ database_name (talk_shopping_xyz, talk_hospital_def)
│  └─ connection_string
│
├─ Table: public_users (CANDIDATOS)
│  ├─ id
│  ├─ email ← Chave global
│  ├─ first_name, last_name
│  ├─ cep
│  ├─ generic_score (0-100)
│  └─ created_at
│
└─ Table: public_applications (HISTÓRICO)
   ├─ id
   ├─ public_user_id
   ├─ organization_id
   ├─ applied_at
   └─ status (pending, interview, hired)

BANCO PRIVADO talk_shopping_xyz:
├─ Table: organization (metadata local)
│  └─ id = 1 (Shopping XYZ)
│
├─ Table: organization_users (REFERÊNCIA)
│  ├─ id
│  ├─ public_user_id ← Referência ao public_users
│  ├─ organization_id = 1
│  ├─ org_specific_score
│  └─ sensitive_id (para auditoria)
│
├─ Table: job_offers (SENSÍVEL)
│  ├─ id
│  ├─ organization_user_id
│  ├─ position
│  ├─ salary ← SENSÍVEL (só Shopping vê)
│  └─ status
│
└─ Table: audit_logs (CONFORMIDADE)
   ├─ id
   ├─ user_id (admin que acessou)
   ├─ action (criou oferta, viu candidato)
   └─ timestamp

BANCO PRIVADO talk_hospital_def:
├─ (mesma estrutura)
├─ Table: organization_users (REFERÊNCIA)
│  └─ João: org_specific_score = 82 (diferente do Shopping)
├─ Table: job_offers
│  └─ Dados do Hospital (não vê Shopping)
└─ Table: audit_logs
   └─ Auditoria isolada do Hospital
```

---

## 🔐 Parte 5: LGPD & Segurança

### Consentimento (LGPD Art. 7)

```python
class PublicUser(models.Model):
    email = EmailField()
    
    # NOVO: LGPD Consent
    consent_recruiting = BooleanField(default=False)
    # "Autorizo meus dados a serem usados para recrutamento"
    
    consent_organizations = JSONField(default=list)
    # Quais orgs podem usar meus dados?
    # ["shopping-xyz", "hospital-def"]
    
    consent_date = DateTimeField(null=True)
    # Quando deu consentimento
    
    def can_apply_to(self, organization_id):
        """Verifica se pode aplicar a esta org"""
        if not self.consent_recruiting:
            return False
        
        org = Organization.objects.using('public').get(id=organization_id)
        return org.slug in self.consent_organizations
```

### Direito de Apagamento (LGPD Art. 17)

```python
def delete_public_user(email):
    """
    Apaga candidato (direito ao esquecimento)
    Usa 'soft delete' para auditoria
    """
    user = PublicUser.objects.using('public').get(email=email)
    
    # Soft delete (não remove fisicamente)
    user.deleted_at = now()
    user.email = f'deleted_{uuid.uuid4()}@talk.deleted'
    user.save(using='public')
    
    # Notifica todos os bancos privados
    for org in Organization.objects.using('public').all():
        db_name = org.database_name
        ORganizationUser.objects.using(db_name).filter(
            public_user_id=user.id
        ).update(deleted_at=now())
    
    return True
```

### Portabilidade de Dados (LGPD Art. 18)

```python
def export_user_data(email):
    """Exporta todos dados do candidato (LGPD Art. 18)"""
    user = PublicUser.objects.using('public').get(email=email)
    
    data = {
        'public': {
            'email': user.email,
            'name': f'{user.first_name} {user.last_name}',
            'score': user.generic_score,
        },
        'by_organization': {}
    }
    
    # Coleta dados de cada org
    for org in Organization.objects.using('public').all():
        org_user = OrganizationUser.objects.using(
            org.database_name
        ).get(public_user_id=user.id)
        
        data['by_organization'][org.slug] = {
            'score': org_user.org_specific_score,
            'applications': [...]
        }
    
    # Retorna JSON exportável
    return data
```

---

## 📋 Parte 6: Implementação Passo-a-Passo

### Fase 1: Setup Infraestrutura (1 semana)

```
[ ] Provisionar PostgreSQL AWS (talk_public)
[ ] Criar PostgreSQL CloudSQL (talk_shopping_xyz)
[ ] Configurar backups automatizados
[ ] Configurar replicação leitura (talk_public)
[ ] Testar failover
```

### Fase 2: Migrações Django (1 semana)

```
[ ] Criar app 'public' (PublicUser, PublicApplication)
[ ] Criar app 'organization' (OrganizationUser, JobOffer)
[ ] Criar router de banco de dados dinâmico
[ ] Testar roteamento (public → AWS, org → CloudSQL)
[ ] Testar transações (public + org junto)
```

### Fase 3: Migrations de Dados (1 semana)

```
[ ] Migrar users existentes → PublicUser (talk_public)
[ ] Copiar dados sensíveis → talk_shopping_xyz (etc)
[ ] Atualizar referências (public_user_id)
[ ] Testar integridade de dados
[ ] Backup antes de cutover
```

### Fase 4: LGPD Compliance (1 semana)

```
[ ] Implementar consentimento (PublicUser.consent_*)
[ ] Implementar direito ao esquecimento
[ ] Implementar portabilidade de dados
[ ] Auditoria de acessos (audit_logs)
[ ] Documentar para DPO
```

---

## ✅ Checklist de Decisão

```
[ ] Confirmar: Híbrido é a opção escolhida?
[ ] Confirmar: Cliente Shopping, Hospital, Rede = 3 bancos privados?
[ ] Confirmar: Candidato compartilhado em talk_public?
[ ] Confirmar: LGPD compliance é prioridade?
[ ] Confirmar: AWS + CloudSQL é infraestrutura?
[ ] Confirmar: Começar com 1 cliente (Shopping) antes de 3?
```

---

## 📊 Sumário: Opção Recomendada

| Aspecto | Opção 1 | Opção 2 | **Opção 3** |
|---------|---------|---------|-----------|
| Candidato Compartilhado | ✅ | ❌ | ✅ |
| LGPD | ⚠️ | ✅ | ✅ |
| Escalabilidade | ⚠️ | ❌ | ✅ |
| Infraestrutura | ✅ | ❌ | ✅ |
| Recomendação | Fase 0 | Enterprise | **PROD** |

**Próximo passo:** Confirmar decisão e iniciar Phase 1 (infraestrutura)
