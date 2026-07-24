# Estratégia de Visibilidade e Audiência

**Versão:** 1.0  
**Status:** proposta base para implementação enterprise  
**Escopo:** Cursos, Feed, Wiki, testes, biblioteca, notificações e demais conteúdos do Talk Learning

## 1. Objetivo

Controlar quem pode visualizar cada conteúdo sem duplicar contas, sem espalhar regras pelos módulos e sem poluir a experiência de usuários de diferentes empresas.

A decisão central é:

```text
O conteúdo define a audiência.
O usuário possui vínculos organizacionais.
Um único serviço decide se o vínculo atende à audiência.
```

## 2. Hierarquia organizacional

```text
Tenant / Organização do sistema
└── Empresa
    └── Unidade de negócio
        └── Unidade operacional
```

### Tenant / Organização

Representa o espaço isolado dentro da instalação do Talk Learning. Permite que várias organizações usem o mesmo sistema sem misturar usuários, conteúdos ou políticas.

Exemplo:

```text
Talk Learning Brasil
```

### Empresa

Representa uma empresa ou cliente dentro da organização.

Exemplos:

```text
Epson
Cisco Brasil
```

### Unidade de negócio

Representa uma operação, parceiro, regional, canal comercial ou divisão da empresa.

Exemplos:

```text
Kalunga
FastShop
Epson Fábrica Manaus
Epson Escritório Alphaville
```

### Unidade operacional

Representa o nível mais específico de operação, como uma filial, loja, escritório, equipe ou local.

Exemplos:

```text
Kalunga Osasco
Kalunga Pinheiros
Escritório Cisco São Paulo
```

## 3. Dimensões que não são hierarquia

Algumas informações filtram a audiência, mas não devem ser tratadas como níveis organizacionais:

### Canal de negócio

Exemplos:

```text
Varejo
Distribuição
Corporativo
Educação
```

Um canal pode estar associado a uma ou várias unidades de negócio.

### Função

Exemplos:

```text
Gerente de loja
Gerente de informática
Vendedor
Técnico
Instrutor
```

Um usuário pode possuir mais de uma função. Função não deve ser um campo único no usuário.

## 4. Vínculo do usuário

O usuário não deve possuir apenas uma empresa fixa. Seu acesso deve ser representado por vínculos:

```text
User
└── Membership
    ├── Tenant
    ├── Empresa
    ├── Unidade de negócio (opcional)
    ├── Unidade operacional (opcional)
    ├── Canais
    ├── Funções
    ├── Principal ou secundário
    └── Ativo ou inativo
```

Um usuário pode ter mais de um vínculo ativo. O vínculo principal é usado para definir o contexto inicial após o login.

## 5. Escopos de audiência

Cada conteúdo pode ter uma política de audiência com um ou mais escopos:

| Escopo | Quem recebe |
|---|---|
| Tenant | Toda a organização |
| Empresa | Todos os usuários da empresa |
| Unidade de negócio | Usuários da unidade e unidades operacionais descendentes |
| Unidade operacional | Somente usuários daquela unidade |
| Canal | Usuários vinculados ao canal |
| Função | Usuários que possuem a função |

### Herança hierárquica

Uma regra em nível superior inclui os níveis abaixo:

```text
Empresa Epson
→ inclui suas unidades de negócio
→ inclui suas unidades operacionais
→ inclui os usuários vinculados a elas
```

Uma regra em nível inferior não sobe na hierarquia:

```text
Kalunga Osasco
→ não inclui Kalunga Pinheiros
→ não inclui toda a Epson
```

## 6. Combinação de regras

A política possui um modo de combinação:

### ALL

Todas as condições precisam ser atendidas.

```text
Empresa = Epson
E Canal = Varejo
E Função = Gerente de loja
```

Resultado: somente gerentes de loja do canal Varejo dentro da Epson.

### ANY

Qualquer condição atendida permite o acesso.

```text
Empresa = Cisco Brasil
OU Empresa = Epson
```

Resultado: usuários de uma das duas empresas podem visualizar.

### Regra recomendada

Dentro de uma regra, os valores da mesma dimensão usam `OR`:

```text
Unidade = Kalunga
OU Unidade = FastShop
```

Dimensões diferentes seguem o modo da política:

```text
Empresa Epson
E Canal Varejo
E Função Gerente
```

## 7. Conteúdo sem política

Conteúdo sem política ativa é público dentro do Tenant, respeitando:

- autenticação;
- estado publicado;
- expiração, quando existir;
- isolamento entre Tenants.

Conteúdo com política inativa deve seguir o comportamento definido pelo produto. A recomendação é voltar ao escopo público do Tenant, mas registrar a alteração no histórico.

## 8. Conteúdo com política

Conteúdo com política ativa só aparece quando pelo menos um vínculo ativo do usuário atende à política.

Exemplos:

```text
Feed:
Empresa = Epson
```

```text
Wiki:
Unidade de negócio = Kalunga
E Canal = Varejo
```

```text
Curso:
Empresa = Cisco Brasil
E Função = Técnico
```

## 9. Negação e exceções

A negação deve ser usada com cuidado e sempre ficar explícita na interface administrativa.

Exemplo:

```text
Empresa = Epson
E Unidade operacional != Escritório Alphaville
```

Regras de negação devem ser avaliadas depois da expansão hierárquica e ter prioridade sobre permissões gerais.

## 10. Serviço central de decisão

Nenhum módulo deve acessar diretamente `company`, `unit`, `function` ou `channel` para decidir visibilidade.

Todos devem usar um serviço único:

```python
audience.can_view(user, content)
```

O serviço deve:

1. verificar autenticação;
2. verificar Tenant ativo;
3. verificar publicação e expiração;
4. carregar todos os vínculos ativos do usuário;
5. expandir a hierarquia organizacional;
6. avaliar canais e funções;
7. aplicar ALL ou ANY;
8. aplicar negações;
9. retornar uma decisão auditável.

Exemplo de resposta:

```python
AudienceDecision(
    allowed=True,
    reason='matched_business_unit_and_channel',
    policy_id=12,
)
```

## 11. Aplicação por produto

### Feed

O Feed deve aceitar políticas simples e temporais:

```text
Empresa
Unidade de negócio
Canal
Função
```

### Wiki

O Wiki pode usar políticas mais específicas e permanentes:

```text
Empresa
Unidade de negócio
Unidade operacional
Canal
Função
```

### Cursos

Cursos podem ser disponibilizados por empresa, canal, função ou combinação deles. A matrícula não deve ignorar a política: o usuário só deve conseguir se matricular se puder visualizar o curso.

### Console

Administradores globais podem acessar todos os Tenants. Administradores de empresa devem visualizar somente sua empresa. Gestores de unidade devem visualizar sua unidade e seus descendentes.

## 12. Isolamento multiempresa

Todo conteúdo enterprise deve pertencer a um Tenant, direta ou indiretamente.

Regras obrigatórias:

- consultas do usuário sempre filtram pelo Tenant ativo;
- conteúdos de outro Tenant nunca aparecem na busca;
- URLs diretas também passam pelo `AudienceService`;
- APIs aplicam a mesma decisão das páginas HTML;
- administradores cross-tenant precisam de permissão explícita;
- troca de Tenant deve ser uma ação visível e auditável.

## 13. Migração de nomenclatura

O vocabulário novo recomendado é:

| Conceito atual | Conceito novo |
|---|---|
| `EpsonUnit` | `Organization` ou `Tenant` |
| `Company` | `Company` |
| `CompanyUnit` | `BusinessUnit` |
| novo | `OperationalUnit` |
| `ChannelType` | `BusinessChannel` |
| `Functions` | `JobFunction` |
| novo | `Membership` |

Como não há legado a preservar, a implementação pode substituir os modelos atuais diretamente e criar uma migração inicial limpa.

## 14. Decisão de produto

O usuário deve receber somente o conteúdo relevante para seu contexto. A hierarquia e as dimensões permitem uma comunicação precisa:

```text
Feed geral da Epson
Feed exclusivo do Varejo
Wiki exclusivo da Kalunga
Curso exclusivo de técnicos Cisco
```

Essa separação reduz ruído, melhora a relevância da Home e permite que o mesmo Talk Learning opere para várias empresas sem misturar dados.
