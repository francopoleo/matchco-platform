# Guia do Administrador - Setup por Setor

**Público**: Administradores de plataforma e admins de tenant  
**Última atualização**: 2026-10-02

---

## Shopping Center

### Visão Geral
Shopping center com múltiplas lojas, varejo, e diferentes segmentos (alimentação, moda, eletrônicos, etc).

### Características Específicas
- **Estrutura**: Múltiplas lojas independentes dentro de um shopping
- **Funções Típicas**: Atendente de caixa, repositor, vendedor, gerente de loja
- **Segmentos**: Alimentação, moda, beleza, eletrônicos, supermercado
- **Rotatividade**: Alta (retail típico)
- **Modelo de Negócio**: RH central do shopping coordena com gerentes de loja

### Funções Padrão
```
Atendente de caixa
Repositor
Vendedor
Gerente de loja
Assistente de atendimento
Supervisor
```

### Segmentos de Experiência
- Alimentação / Cafeteria
- Moda / Roupas
- Calçados
- Beleza / Cosméticos
- Eletrônicos
- Supermercado
- Loja de departamentos
- Serviços

### Fluxo de Setup

1. **Criar Organization**
```bash
python manage.py shell

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
```

2. **Importar Lojas** (do CSV)
```bash
# Preparar stores.csv com colunas: Name, Latitude, Longitude, Segment
# Exemplos:
# Loja A - Centro,-23.564,-46.652,Moda
# Loja B - Zona Sul,-23.560,-46.658,Alimentação
```

3. **Criar Usuários**
- Admin do shopping: acesso completo ao console
- Gerentes de loja: acesso limitado a suas lojas

4. **Criar QR Codes**
- Um QR por loja
- Modo MATCH ou VAGA conforme configurado

### Relatórios Importantes
- Conversão por loja (QR → cadastro → candidatura → contratação)
- Vagas abertas vs candidatos disponíveis
- Melhor segmento de origem de candidatos
- Velocidade média de contratação por loja

---

## Hospital

### Visão Geral
Hospital com múltiplos departamentos e especialidades.

### Características Específicas
- **Estrutura**: Departamentos/unidades (Emergência, UTI, Cirurgia, etc)
- **Funções Típicas**: Enfermeiro, técnico de enfermagem, médico, assistente administrativo
- **Especialidade**: Saúde; exigências regulatórias (LGPD para dados sensíveis)
- **Disponibilidade**: Turnos 24h (manhã, tarde, noite)
- **Rotatividade**: Média a baixa (contratos mais estruturados)
- **Modelo de Negócio**: RH central coordena contratações para departamentos

### Funções Padrão
```
Enfermeiro(a)
Técnico de Enfermagem
Médico(a)
Assistente Administrativo
Recepcionista
Nutricionista
Psicólogo(a)
Farmacêutico(a)
```

### Segmentos de Experiência
- Emergência
- Internação
- UTI
- Cirurgia
- Pediatria
- Maternidade
- Laboratório
- Farmácia

### Fluxo de Setup

1. **Criar Organization**
```bash
python manage.py shell

from configuration.models import Organization, Domain

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
```

2. **Importar Departamentos** (como "lojas" no sistema)
```bash
# Cada departamento é uma unidade com suas próprias vagas
# Departamentos: Emergência, UTI, Cirurgia, Pediatria, etc
```

3. **Criar Usuários**
- Admin do hospital: acesso completo
- Chefes de departamento: acesso limitado ao departamento
- Gerentes de RH: visão consolidada

4. **Configurações Especiais**
- Turnos: Manhã, Tarde, Noite (disponibilidade 24h)
- Compliance: Exigir validação de certificações de saúde quando aplicável
- Privacidade: Dados de saúde com criptografia reforçada

### Relatórios Importantes
- Vagas por departamento e especialidade
- Turnos mais difíceis de preencher
- Candidatos com certificações relevantes
- Tempo médio de contratação por especialidade
- Conformidade com regulamentações

---

## Farmácia / Drogaria

### Visão Geral
Rede de farmácias com múltiplas filiais/unidades.

### Características Específicas
- **Estrutura**: Filiais / unidades espalhadas geograficamente
- **Funções Típicas**: Atendente de caixa, balconista, farmacêutico, auxiliar
- **Modelo**: Franquia ou rede corporativa
- **Rotatividade**: Alta (varejo farmacêutico)
- **Competência**: Conhecimento de produtos, conselhos de saúde
- **Modelo de Negócio**: Franquias ou rede central coordena

### Funções Padrão
```
Atendente de Caixa
Balconista de Manipulação
Farmacêutico(a)
Auxiliar de Farmácia
Gerente de Filial
Operador de Logística
```

### Segmentos de Experiência
- Atendimento ao público
- Medicamentos genéricos
- Medicamentos controlados (exigência legal)
- Cosméticos e higiene
- Insumos para saúde
- Manipulação de fórmulas

### Fluxo de Setup

1. **Criar Organization**
```bash
python manage.py shell

from configuration.models import Organization, Domain

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
```

2. **Importar Filiais**
```bash
# CSV com todas as filiais/unidades
# Cada filial é uma localização com sua própria demanda
```

3. **Criar Usuários**
- Admin da rede: acesso completo
- Gerentes de filial: acesso à filial
- RH central: visão consolidada

4. **Configurações Especiais**
- Certificações: Validação de farmacêuticos registrados
- Medicamentos: Separar perguntas sobre medicamentos controlados
- Logística: Disponibilidade para turno de distribuição

### Relatórios Importantes
- Rotatividade por filial
- Filiais com maior dificuldade de contratação
- Candidatos com experiência em manipulação
- Conversão de candidatos por região geográfica

---

## Guia de Decisões por Setor

### Entrada de Dados

| Setor | CPF Obrigatório | Currículo Obrigatório | Experiência Mínima |
|---|---|---|---|
| Shopping | Não (depois na contratação) | Não | Não exigida |
| Hospital | Sim (compliance) | Sim (verificação de credenciais) | Sim (especialidades) |
| Farmácia | Não (depois na contratação) | Não | Não exigida |

### Validações

| Setor | Certificações | Turno 24h | Distância Máxima |
|---|---|---|---|
| Shopping | Não | Não | Configurável por loja |
| Hospital | Sim (COREN, etc) | Sim | Sem limite (plantões) |
| Farmácia | Farmacêuticos: Sim | Sim | Configurável por filial |

### Publicação de Vagas

| Setor | Vaga Permanente | Vaga Temporária | Vaga em Edital |
|---|---|---|---|
| Shopping | Sim | Sim | Não |
| Hospital | Sim | Sim (plantões) | Sim (concursos públicos) |
| Farmácia | Sim | Sim | Não |

### Consentimento

| Setor | Pool de Lojas | Pool de Rede | Pool Externo |
|---|---|---|---|
| Shopping | Opt-in | Opt-in | Não |
| Hospital | Opt-in | Opt-in (direcionado) | Não |
| Farmácia | Opt-in | Opt-in | Não |

---

## Troubleshooting por Setor

### Shopping
- **Problema**: Muitas candidaturas para poucas vagas em segmentos populares
  **Solução**: Implementar limite de exposição / rotação de candidatos

- **Problema**: Candidatos cadastram em múltiplas lojas do mesmo shopping simultaneamente
  **Solução**: Explicar o sistema de pool; incentivar consentimento único

### Hospital
- **Problema**: Difícil encontrar profissionais com certificação válida
  **Solução**: Integrar validação com COREN/CREMESP; mostrar status de certificação

- **Problema**: Turno de noite com poucas candidaturas
  **Solução**: Marcar preferência de turno como obrigatória; oferecer incentivos

### Farmácia
- **Problema**: Rotatividade muito alta; candidatos saem rápido
  **Solução**: Implementar feedback pós-contratação; identificar padrões

- **Problema**: Filiais distantes com poucas candidaturas
  **Solução**: Permitir candidatura remota; considerar reubicação para candidatos

---

## Checklist de Compliance por Setor

### Shopping
```
☐ Política de privacidade acessível
☐ Consentimento de contato explícito
☐ Dados de menores com cuidado (se houver estágio)
☐ Aviso de anti-discriminação visível
```

### Hospital
```
☐ Confirmação de credenciais de saúde
☐ Dados de saúde criptografados
☐ Conformidade com LGPD para dados sensíveis
☐ Avisos sobre trabalho em saúde
☐ Validade de certifications registrada
```

### Farmácia
```
☐ Validação de farmacêuticos registrados
☐ Conformidade com regulamentações de medicamentos
☐ Dados de saúde protegidos
☐ Avisos sobre manipulação (se aplicável)
```

---

**Última Atualização**: 2026-10-02  
**Referência**: [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md) para setup técnico
