# Guia de Login e Acesso a Conteúdo Pessoal

## Credenciais de Acesso

### Superadmin (Acesso a Todas as Organizações)
- **Email ou Usuário:** `superadmin` ou `superadmin@example.com`
- **Senha:** `Admin@Talk123!`
- **Acesso:** Todas as 7 organizações, painel admin completo

### Admins de Organização
Cada organização tem um admin com acesso completo:

```
Hospital Demo:
  Email: admin-hospital-demo@example.com
  Usuário: admin_hospital_demo
  Senha: Admin@Talk123!

Seguradora Demo:
  Email: admin-seguradora-demo@example.com
  Usuário: admin_seguradora_demo
  Senha: Admin@Talk123!

Escola Demo:
  Email: admin-escola-demo@example.com
  Usuário: admin_escola_demo
  Senha: Admin@Talk123!

Manufatura XYZ:
  Email: admin-manufatura-xyz@example.com
  Usuário: admin_manufatura_xyz
  Senha: Admin@Talk123!

Retail 800:
  Email: admin-retail-800@example.com
  Usuário: admin_retail_800
  Senha: Admin@Talk123!

FinTech Rapido:
  Email: admin-fintech-rapido@example.com
  Usuário: admin_fintech_rapido
  Senha: Admin@Talk123!

Farmalab Biotech:
  Email: admin-farmalab-biotech@example.com
  Usuário: admin_farmalab_biotech
  Senha: Admin@Talk123!
```

### Gerentes e Membros da Organização

Cada organização tem 2 gerentes e 5 membros:

```
Hospital Demo - Gerente 1:
  Email: manager1-hospital-demo@example.com
  Usuário: manager1_hospital_demo
  Senha: (definida no seed - use email/username para login)

Hospital Demo - Membro 1:
  Email: user1-hospital-demo@example.com
  Usuário: user1_hospital_demo
  Senha: (definida no seed - use email/username para login)

[Padrão similar para outras organizações e usuários]
```

## Como Logar

### URL de Login
```
http://localhost:8000/login/
```

### Processo de Login
1. Acesse a página de login
2. Digite **email OU username** (o sistema aceita ambos)
3. Digite a senha
4. Clique em "Entrar"

**Exemplo:**
- Campo: `superadmin` OU `superadmin@example.com`
- Senha: `Admin@Talk123!`

## Informações Pessoais e Notificações

### Acessar Dashboard Pessoal
1. Após logar, você verá a página inicial do console
2. Clique no seu perfil no canto superior direito
3. Selecione "Minhas Informações" ou "Perfil"

### Ver Notificações
1. Procure o ícone de sino (🔔) no topo da página
2. Clique para ver notificações de:
   - Novas publicações (Feeds/Wikis)
   - Novos documentos atribuídos
   - Trilhas de aprendizado atribuídas
   - Comunicados importantes

### Trocar Organização (Multi-tenant)
1. Se você tem acesso a múltiplas organizações (admin)
2. Clique no seletor de organização no topo
3. Selecione a organização desejada
4. A interface muda para mostrar conteúdo dessa organização

## Acessar Conteúdo Pessoal

### 1. Feed (Notícias e Comunicados)
- Menu: **Conteúdo > Feed**
- Mostra todas as publicações de tipo "Feed" da sua organização
- Ordenado por data de publicação
- Indicadores de importância: Crítica (🔴), Importante (🟠), Rotina (🟢)

### 2. Wiki (Documentação)
- Menu: **Conteúdo > Wiki**
- Guias e documentação da organização
- Contém procedimentos, manuais e políticas
- Organizado por tópico

### 3. Documentos
- Menu: **Conteúdo > Documentos**
- Documentos importantes da organização
- Inclui:
  - Manuais
  - Políticas
  - Procedimentos
  - Formulários

### 4. Minhas Trilhas de Aprendizado
- Menu: **Conteúdo > Minhas Trilhas** OU **Aprendizado**
- Mostra trilhas atribuídas a você
- Status de conclusão
- Trilhas obrigatórias têm marcação especial (⚠️)

**Trilhas Criadas:**
- **Trilhas Obrigatórias:** Todos os membros devem completar
  - Segurança/Conformidade
  - Procedimentos Essenciais
  - Onboarding

- **Trilhas Recomendadas:** Para desenvolvimento
  - Avançado
  - Especialização
  - Liderança

## Conteúdo por Organização

### Hospital Demo
**Feeds/Wikis:**
- Protocolo de Segurança do Paciente
- Guia Completo de HIPAA
- Procedimentos de Emergência
- Laboratório de Imagem - Novo Equipamento
- Boas Práticas em Atendimento

**Documentos:**
- Manual de Segurança do Paciente
- Conformidade HIPAA
- Protocolos de Emergência
- Guia de Equipamentos Médicos

**Trilhas:**
- Segurança do Paciente 101 (Obrigatória)
- Conformidade HIPAA (Obrigatória)
- Procedimentos de Emergência (Obrigatória)
- Novo Equipamento Médico (Recomendada)

### Seguradora Demo
**Feeds/Wikis:**
- Novo Produto: Cobertura Integral para PMEs
- Guia Completo de Processamento de Sinistros
- Regulações Q3 2024
- Rede de Prestadores
- Canais Digitais para Clientes

**Documentos:**
- Modelos de Política
- Manual de Processamento de Sinistros
- Guia de Conformidade Regulatória
- Rede de Prestadores
- Cobertura de Produtos

**Trilhas:**
- Processamento de Sinistros Avançado (Obrigatória)
- Produtos de Seguro (Recomendada)
- Conformidade Regulatória (Obrigatória)
- Atendimento ao Cliente (Recomendada)

### [Outras organizações seguem padrão similar]

## Exemplo de Fluxo de Um Novo Usuário

1. **Login:**
   - Acesse http://localhost:8000/login/
   - Use: `user1-hospital-demo@example.com` / `Admin@Talk123!`

2. **Dashboard:**
   - Vê dashboard com notificações
   - Vê trilhas atribuídas

3. **Explorar Conteúdo:**
   - Conteúdo > Feed → vê comunicados
   - Conteúdo > Wiki → vê documentação
   - Conteúdo > Documentos → acessa documentos

4. **Iniciar Trilhas:**
   - Conteúdo > Minhas Trilhas
   - Clica em trilha obrigatória
   - Começa os passos da trilha

5. **Ver Notificações:**
   - Clica no ícone de sino
   - Vê notificações de conteúdo novo

## Pontos Importantes

### Rate Limiting
Se receber erro de "muitas tentativas de login":
- Aguarde 1 hora antes de tentar novamente
- OU execute: `python manage.py shell` → `from django.core.cache import cache; cache.clear()`

### Acesso Baseado em Organização
- Usuários só veem conteúdo da sua organização
- Admins podem trocar de organização para gerenciar
- Superadmin tem acesso a tudo

### Hierarquias de Grupos
- Menu: **Grupos > Hierarquias**
- Visualize estrutura departamental
- Veja membros de cada departamento
- (Acessível do console admin)

## URLs Úteis

```
Dashboard: http://localhost:8000/console/
Feed: http://localhost:8000/console/publications/
Documentos: http://localhost:8000/console/documents/
Grupos: http://localhost:8000/console/groups/
Admin: http://localhost:8000/admin/
```

## Suporte

Para resetar dados ou testar novamente:
```bash
python manage.py seed_complete_system --clear
python manage.py seed_production_data
```

Isso recria tudo com dados completos e consistentes.
