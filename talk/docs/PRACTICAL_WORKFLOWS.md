# Talk: Fluxos Práticos Detalhados

**Versão:** 1.0  
**Data:** 2026-07-26  
**Objetivo:** Exemplos step-by-step de como Talk resolve problemas reais em cada setor

---

## 🏥 SAÚDE: Protocolo Novo de Tratamento

### Cenário
Hospital tem 500 profissionais de saúde (médicos, enfermeiros, fisioterapeutas, administrativos) em 3 unidades (Oncologia, Clínica Geral, Pronto-Socorro). ANVISA aprovou novo protocolo de coleta de sangue que deve ser conhecido por TODOS os profissionais em até 10 dias.

**Problema Antigo (sem Talk):**
- Diretor publica manual em PDF (30 páginas)
- Email para toda empresa (metade não lê)
- Reunião presencial (2h, só 60% vai)
- Planilha de presença (não prova conhecimento)
- Ninguém sabe quem realmente aprendeu
- 20% ainda usando protocolo antigo

**Prazo:** 10 dias  
**Métrica de Sucesso:** 95%+ de profissionais completarem trilha + compreenderem novo protocolo

---

### Fluxo com Talk (Dia 1 - Setup)

#### 1. Admin Prepara Conteúdo (1 hora)
```
Acessa: Admin > Cursos > Novo Curso
├─ Título: "Protocolo Novo: Coleta de Sangue"
├─ Descrição: "Esse protocolo entra em vigor dia 10/07. Todos precisam conhecer antes dessa data."
├─ Duração: 20 min
├─ Tipo: Obrigatório
│
├─ Módulo 1: Razão da mudança (3 min vídeo)
│  └─ Por que ANVISA pediu isso? Qual o risco antigo?
│
├─ Módulo 2: Passo-a-passo novo (10 min, com imagens)
│  ├─ Antes: Tubo tipo X
│  ├─ Depois: Tubo tipo Y
│  ├─ Diferença no tempo de espera
│  ├─ Fluxograma visual
│  └─ Checklist: O que fazer em cada etapa
│
├─ Módulo 3: Casos especiais (5 min, 3 cenários)
│  ├─ Paciente diabético
│  ├─ Paciente hipertenso
│  └─ Paciente na quimio (oncologia)
│
└─ Avaliação: 5 perguntas (só passa com 80%)
   ├─ "Qual tubo usar para coagulação?"
   ├─ "Se paciente está em quimio, qual o tempo de espera?"
   └─ Etc

Salva: "Rascunho"
```

#### 2. Admin Define Audiências (30 min)
```
Acessa: Curso > Audiências
├─ TODOS os profissionais podem ver ✓
│
├─ MAS direcionado para:
│  ├─ Profissionais que fazem coleta
│  │  ├─ Enfermeiros (Oncologia, Clínica, PS)
│  │  ├─ Flebotomistas
│  │  └─ Médicos (alguns fazem coleta)
│  │
│  └─ Administrativos (recebem versão leve - 5 min)
│     ├─ Saber que mudança existe
│     ├─ Saber comunicar ao paciente
│     └─ Avaliação: 2 perguntas
│
├─ Data de início: Hoje
├─ Data limite: Dia 10/07
├─ Frequência reminder: Dia 3, Dia 7, Dia 10
│
└─ Prioridade: CRÍTICA (aparece em vermelho na home)
```

#### 3. Admin Publica + Notifica (15 min)
```
Clica: Publicar

Automático:
├─ Email para todos os 500 profissionais
│  "Novo protocolo de coleta começou hoje. Leia em 20 min."
│
├─ Push no App Talk
│  Ícone de prioridade CRÍTICA
│  
├─ Feed corporativo
│  Notícia: "Protocolo novo de coleta, vigente a partir de 10/07"
│  Com link para trilha
│
└─ Dashboard do Diretor ativa
   "Protocolo: 0/500 completaram"
```

---

### Fluxo com Talk (Dias 2-9 - Aprendizagem)

#### Dia 2 - Terça (Primeiro acesso)
```
Enfermeira "Marta" abre Talk no celular
├─ Home vê:
│  ├─ [CRÍTICO] Protocolo novo: Coleta de Sangue
│  │  "20 min | Vence em 8 dias"
│  │  [Começar]
│  │
│  └─ [Rotina] Lembretes da próxima escala
│
├─ Clica em [Começar]
├─ Módulo 1: Assiste vídeo 3 min
├─ Pausa: "Volto depois"
└─ Progress: 15% (Módulo 1 visto)
```

#### Dia 4 - Quinta (Continuação)
```
Marta recebe Push
├─ "Falta completar Protocolo novo: 6 dias"
├─ Abre Talk de novo
├─ Continua: Módulo 2
├─ Estuda passo-a-passo (10 min)
├─ Vê checklist visual
└─ Progress: 65%
```

#### Dia 6 - Sábado (Folga, mas lembra)
```
Marta recebe Email
├─ Subject: "Protocolo: você está quase lá"
├─ "Só faltam 2 módulos, 4 dias para completar"
├─ Clica link no email
├─ Módulo 3: Estuda casos especiais (5 min)
├─ Progress: 90%
```

#### Dia 9 - Segunda (Avaliação)
```
Marta abre Talk
├─ Vê notificação: "Última chance: Protocolo vence amanhã"
├─ Módulo 3 já fez
├─ Avaliação: 5 perguntas
│  Q1: "Qual tubo?" → Responde corretamente ✓
│  Q2: "Tempo de espera?" → Responde corretamente ✓
│  Q3: "Caso especial: diabético?" → Responde corretamente ✓
│  Q4: "Novo check?" → Erra primeira vez
│  → Talk oferece: "Volte ao Módulo 2 para rever"
│  → Revê 3 min
│  → Tenta novamente: Acerta ✓
│  Q5: "Quando começa?" → Acerta ✓
│
├─ Resultado: 100% (5/5)
├─ Status: ✓ CERTIFICADO
├─ Prova PDF baixada (para seu registro)
│
└─ Confete digital 🎉
   "Você está pronto para o novo protocolo!"
```

---

### Dashboard: Visão do Diretor (Dia 10)

```
Admin > Relatórios > Protocolo Novo

Aderência Geral:
├─ ✓ 475/500 completaram (95%)
├─ ⏳ 15 ainda em andamento
├─ ⏹️ 10 não iniciaram (lista de quem falta)

Por Unidade:
├─ Oncologia: 98% (152/155 completaram)
├─ Clínica Geral: 94% (185/197)
├─ Pronto-Socorro: 91% (138/151)

Por Função:
├─ Enfermeiros: 96% (250/260)
├─ Médicos: 92% (80/87)
├─ Administrativos: 89% (75/84)

Tempo Médio:
├─ Tempo para completar: 21 min
├─ Tempo para passar na avaliação: 1 tentativa
├─ Taxa de erro: 12% (primeira tentativa)

Engajamento:
├─ Assistiram vídeos: 99%
├─ Viram checklist: 98%
├─ Leram casos especiais: 93%

Ação do Diretor:
├─ Manda Email direto: "15 não completaram - motivar hoje"
│  └─ Talk envia Push automático para esses 15
│
└─ Gera Relatório para ANVISA
   "Todos os profissionais treinados, testados e certificados."
```

---

### Resultado (Dia 10)

**Antes (sem Talk):**
- 60% realmente leu o PDF
- 30% foi na reunião
- 10% dominava o novo protocolo
- Custo: 2h de reunião × 500 pessoas = 1000 horas
- Resultado: 10 dias depois, ainda tinha gente usando protocolo antigo

**Com Talk (10 dias depois):**
- 95% completou trilha
- 94% passou na avaliação
- 100% tem prova de competência (para auditoria)
- Custo: Plataforma + 1h do admin para preparar = muito menor
- Resultado: Protocolo implementado em segurança total

**ROI:**
- Tempo economizado: 1000h - 100h (engajamento) = 900h
- Valor: 900h × R$ 200/h (custo do profissional de saúde) = R$ 180.000
- Custo Talk: R$ 5.000
- ROI: 36x em 10 dias

---

---

## 🏦 SEGUROS: Novo Produto para Corretores

### Cenário
Seguradora lançou novo produto: "Seguro Vida Premium Plus" com comissionamento diferenciado. 800 corretores espalhados precisam conhecer produto, saber vender, dominarem tabela. Concorrência lançou igual, então precisa ser rápido.

**Problema Antigo (sem Talk):**
- Webinar gravado + enviado (50% assiste)
- Email com PDF e tabela (arquivo se perde, versão fica desatualizada)
- Alguns corretores ligam pra matriz pedir esclarecimento (custo)
- Nem sabe quem realmente aprendeu
- Primeiro mês: produto não vende bem (corretores com dúvida)
- Comissão errada em 5% dos casos

**Prazo:** 2 dias para vender  
**Métrica de Sucesso:** 80%+ de corretores certificados em produto, vendas no dia 3

---

### Fluxo com Talk

#### Dia 1 - Análise (Manhã)

```
Gerente de Produto cria no Talk:

Trilha: "Novo Produto: Vida Premium Plus"
├─ Público: Corretores ativos + gestores de corretoria
├─ Duração: 45 min
│
├─ Módulo 1: Posicionamento (10 min, vídeo + PDF)
│  ├─ O que é Vida Premium Plus
│  ├─ Por que corretores devem vender isso
│  ├─ Diferenciais vs concorrência
│  ├─ Margin + Comissão por faixa
│  └─ Resumo 1-page (baixável)
│
├─ Módulo 2: Simulador Interativo (15 min)
│  ├─ "Cliente tem 30 anos, quer R$ 500k de cobertura"
│  │  Quanto custa por mês? Qual comissão?
│  ├─ "Cliente tem 50 anos, saúde frágil"
│  │  Precisa de avaliação médica? Quanto sai?
│  ├─ "Cliente é PJ"
│  │  Como funciona? Diferença de preço?
│  │
│  └─ Simulador atualiza com preços REAIS em tempo real
│
├─ Módulo 3: Objeções + Respostas (10 min)
│  ├─ "Quanto sai o novo produto vs Vida Standard?"
│  │  → Aqui está a tabela comparativa + resposta
│  │
│  ├─ "Cliente tem comorbidade"
│  │  → Fluxograma: deve fazer avaliação ou já nega?
│  │
│  └─ "Comissão cai para faixa X de cobertura?"
│     → Não. Veja tabela de comissão progressiva
│
├─ Módulo 4: Cases de Sucesso (5 min)
│  ├─ Caso 1: Corretor Y vendeu para casal, renda alta
│  │  "Como eu estruturei: calculadora aqui, case aqui"
│  │
│  └─ Caso 2: Corretor Z vendeu pra cliente resistente
│     "Objection dele e como eu respondi"
│
├─ Módulo 5: Certificação (5 min, 10 perguntas)
│  ├─ Q1: "Simulador: cliente 30 anos, 500k → quanto sai?"
│  ├─ Q2: "Qual comissão para cobertura de 750k?"
│  ├─ Q3: "Cliente com diabetes: precisa de avaliação?"
│  ├─ Q4: "Qual o diferencial principal vs concorrência?"
│  ├─ Q5-Q10: Situações reais
│  │
│  └─ Só passa com 80% = Corretor certificado
│
├─ Recurso: Wiki Produto Vida Premium Plus
│  ├─ Tabela de preços (sempre atualizada)
│  ├─ Tabela de comissão
│  ├─ Simulador (link)
│  ├─ Fluxograma de aprovação
│  ├─ Perguntas frequentes
│  ├─ Contato de suporte (Se tiver dúvida)
│  │
│  └─ A cada mudança de preço, Wiki atualiza
│     E talk manda notificação: "Preço de Premium Plus mudou"
│
└─ Prioridade: CRÍTICA
   Data limite: 48 horas
   Reminder: 12h, 24h, 36h
```

#### Dia 1 - Tarde (Publicação)

```
Clica: Publicar

Automático:
├─ Email para 800 corretores
│  Subject: "Novo Produto Vida Premium - Comece a vender amanhã"
│  Body: "Trilha de 45 min + simulador + wiki"
│
├─ Push no App Talk
│  [CRÍTICA] Novo Produto: Vida Premium Plus
│  "Comece agora - Limite: 48h"
│
├─ Feed Corretores
│  Post: "Produto novo lançado!"
│  Com link para trilha + simulador
│
└─ Dashboard Gerente
   "Produto: 0/800 certificados"
```

#### Dia 1 - Noite (Corretores Começam)

```
Corretor "João" abre Talk no celular (durante café)
├─ Home vê: [CRÍTICA] Novo Produto - 48h
├─ Clica: Começar
├─ Módulo 1: Assista vídeo (10 min)
├─ Entendi: comissão é 15% na faixa 1-500k
├─ Pausa
└─ Progress: 22%

Noite:
├─ Recebe Push: "Falta 39h para fechar cadastro"
└─ Acessa link, continua
```

#### Dia 2 - Manhã (Simulador)

```
João volta no Talk
├─ Continua: Módulo 2 (Simulador)
├─ Primeira tentativa:
│  "Cliente 30 anos, quer 500k"
│  João clica nas opções
│  Simulador calcula: R$ 89/mês, comissão R$ 1.335
│  João: "Ok, isso faz sentido"
│
├─ Segunda tentativa:
│  "Cliente 50 anos, saúde frágila"
│  João tenta
│  Simulador: "Precisa de avaliação médica"
│  "Clique para ver fluxograma de aprovação"
│  João estuda 2 min
│  "Ah, entendi. Quando ele quer cobertura alta, tem que passar por médico"
│
├─ Terceira: Cliente PJ
│  João faz 2 min
│  "Mesma tabela de preço, legal!"
│
└─ Progress: 60%
```

#### Dia 2 - Tarde (Objeções + Cases)

```
João continua:
├─ Módulo 3: Objeções
│  "Ah, tem uma objeção que eu corro riscos aqui:"
│  "Comissão é menor que produto antigo"
│  Acha na lista de objeções
│  Lee: "Não, confira: faixa X paga mais, porque é produto premium"
│  Vê comparação lado-a-lado
│  "Ah, só achei que era menos!"
│
├─ Módulo 4: Cases
│  Vê caso de Corretor Y (mesmo estado que João)
│  "Y vendeu para casal, aqui está a estrutura"
│  João: "Vou usar essa estrutura também"
│
├─ Módulo 5: Certificação
│  10 perguntas
│  João acerta 9/10 na primeira tentativa
│  Erra a Q7 (comissão em caso X)
│  Talk oferece: "Revire Módulo 3, pergunta 7"
│  João revê (1 min)
│  Tenta novamente: acerta
│  Status: ✓ CERTIFICADO
│
└─ Prova PDF: João baixa para seu registro
```

#### Dia 2 - Fim do dia (Vendas Começam)

```
João abre email do corretor que recebi do cliente:
├─ "Oi João, tenho interesse naquele seguro novo que você mencionou"
├─ Cliente: 35 anos, quer 800k
├─ João abre simulador do Talk (ou faz na cabeça)
├─ Calcula: R$ 145/mês, comissão R$ 2.000
│  (alta comissão, porque cobertura é grande!)
├─ Manda orçamento ao cliente
└─ Primeira venda do novo produto

Ao mesmo tempo:
├─ Dashboard Gerente mostra:
│  "Produto: 650/800 certificados (81%)"
│  "Primeiras vendas: 47 (2 horas após público ver)"
│  "Ticket médio: R$ 152/mês"
└─ Gerente: "Ótimo começo!"
```

#### Dia 3 (Validação de Sucesso)

```
Dashboard Gerente:
├─ 790/800 certificados (98%)
├─ Vendas nos primeiros 2 dias: 240
├─ Ticket médio: R$ 148/mês (dentro do esperado)
├─ Comissão média: R$ 2.200 (bom sinal de vendas qualificadas)
│  (Se fosse 500k média, comissão seria 1.5k, logo estão vendendo bem)
│
├─ Tempo médio pra certificar: 42 min
├─ Taxa de sucesso na avaliação: 94% (primeiro acerto)
│
└─ 10 corretores que não fizeram ainda
   Talk envia ultimatum: "Último dia - termine agora"
   Até fim do dia: 8 completam
   2 que não completaram: Gerente liga (achaca via: falta de acesso app, etc)
   Resultado final: 798/800 (99.75% certificados)
```

---

### Resultado (Dia 3)

**Antes (sem Talk):**
- Webinar 1h30 min
- 50% assistiu (400 corretores)
- Desses, 30% realmente aprendeu (120 pessoas seguras)
- 2 semanas para produto pegue tração
- Comissões erradas (time de suporte gasta horas corrigindo)
- Custo: 1.5h × 800 pessoas (tempo perdido) + 40h (suporte) + retrabalho

**Com Talk (2 dias depois):**
- Trilha 45 min
- 98% completou (784 corretores)
- Desses, 94% passou na avaliação (737 pessoas realmente certificadas)
- Primeira venda no dia 2
- Comissão correta (simulador previne erros)
- Custo: 0.75h de tempo (engajamento leve) + 2h (prep da trilha)

**ROI:**
- Velocidade: 2 dias vs 14 dias = 12 dias antes
- Vendas antecipadas em 12 dias × R$ 152/mês × 240 vendas = R$ 3.6M
- Comissões certas: evita 5-10 erros × R$ 2.000 = R$ 20k
- Custo Talk: R$ 15k (para corretoras)
- **ROI: 240x em 3 dias** (absurdo, mas baseado em real)

---

---

## 🏭 MANUFATURA: Nova Linha de Produção

### Cenário
Fábrica tem 3 linhas de produção, está trazendo uma 4ª linha (investimento R$ 50M). A nova linha é 30% mais rápida, mais eficiente. 200 operários precisam ser treinados em 5 dias (não pode parar produção). Cada dia que atrasa = R$ 500k de perda.

**Problema Antigo (sem Talk):**
- Treinamento presencial (40h total)
- Turno A aprende seg-sex
- Turno B aprende seg-sex
- Terceiro turno fica sem treino (fazem plantão)
- Resultado: 2 semanas para todo mundo estar ready
- Qualidade ruim (retrabalho 10%)

**Prazo:** 5 dias  
**Métrica de Sucesso:** 200 operários treinados, testados, prontos para operar com erro <1%

---

### Fluxo com Talk

#### Dia 0 - Preparação (Admin)

```
Gerente de Produção prepara no Talk:

Trilha: "Nova Linha 4: Como Operar"
├─ Público: Operadores, supervisores (TODOS precisam saber basics)
├─ Duração: 8 horas
│  (Split em 4 módulos de 2h, para não sobrecarregar)
│
├─ Módulo 1: Tour Virtual (30 min, vídeo 360°)
│  ├─ Aqui está a máquina
│  ├─ Veja os componentes principais
│  ├─ Compare com Linha 3 (diferenças)
│  ├─ Vídeo de operação (6 min, real)
│  └─ Vídeo de parada de emergência (3 min, crítico)
│
├─ Módulo 2: Startup da Linha (2 horas, passo-a-passo)
│  ├─ Checklist pré-operação (20 itens visuais)
│  │  ✓ Óleo verificado? Foto
│  │  ✓ Sensores limpos? Foto
│  │  ✓ Calibração OK? Foto
│  │  Cada um com instruções
│  │
│  ├─ Sequência de botões (não pode errar)
│  │  Diagrama interativo
│  │  Clica em cada botão, sequência aparece
│  │  Simulação de som (quando liga realmente faz som)
│  │
│  ├─ Primeiros 5 minutos rodando
│  │  Vídeo real: tudo começou OK
│  │  Quais sinais procurar? Temperatura, pressão, velocidade
│  │
│  └─ Primeira produção de 10 unidades
│     Como inspecionar qualidade
│     Referência de bom vs defeito
│
├─ Módulo 3: Operação Normal (2 horas)
│  ├─ Velocidade esperada: 850 unidades/dia
│  ├─ Como manter: checklist a cada 2h
│  ├─ Ajustes durante o dia (se sai do normal)
│  ├─ Pausa segura (como desligar bem)
│  └─ Limpeza end-of-shift
│
├─ Módulo 4: Emergências & Troubleshooting (2 horas)
│  ├─ Alarme vermelho: parar tudo! (Video)
│  ├─ Alarme amarelo: desacelera (pode ter problema)
│  ├─ Problema comum 1: sensor sujo
│  │  Sintoma: "Número de unidades cai"
│  │  Solução: limpa sensor (3 min)
│  │  Vídeo step-by-step
│  │
│  ├─ Problema comum 2: óleo baixo
│  │  Sintoma: "Máquina faz barulho estranho"
│  │  Solução: check óleo, top-up
│  │
│  └─ Quando chamar supervisor (vs auto-fix)
│     Fluxograma: "Se X, faça Y. Se não resolveu, chame supervisor"
│
├─ Avaliação Parte 1: Múltipla escolha (20 perguntas)
│  ├─ "Qual a velocidade esperada?" → Opções
│  ├─ "Se alarme vermelho, você deve..."
│  ├─ "Sensor sujo causa qual sintoma?"
│  └─ Só passa com 90%
│
├─ Avaliação Parte 2: Simulação Prática
│  ├─ Simulador: "Você está operando, 30 min passou"
│  ├─ Cenário 1: "Temperatura sobe. O que faz?"
│  │  Operador escolhe ação
│  │  Simulador mostra resultado (certo/errado)
│  │
│  ├─ Cenário 2: "Número de unidades cai. O que é?"
│  │  "Sensor? Óleo? Configuração?"
│  │
│  └─ Cenário 3: "Alarme vermelho dispara"
│     "Ação correta é:"
│     Só passa se acertar
│
├─ Wiki: Linha 4 (Referência sempre disponível)
│  ├─ Especificações técnicas
│  ├─ Tabela de manutenção (quando fazer o quê)
│  ├─ Número de emergência
│  ├─ Peças de reposição comuns
│  └─ Atualizada conforme surgem problemas reais
│
└─ Prioridade: CRÍTICA
   Liberação: Hoje (dia 0)
   Limite: Final de dia 5
   Reminder: Cada dia (não pode perder prazo)
```

#### Dia 1 - Turno A (Manhã)

```
100 operários de Turno A
├─ Recebem: Tablet com Talk pré-carregado
├─ 2 facilitadores: Um por 50 pessoas
│
├─ 08h00: Módulo 1 (Tour Virtual) - 30 min
│  ├─ Todos assistem vídeo 360° na tela grande (projetor)
│  ├─ Turno todo vê a mesma coisa ao mesmo tempo
│  ├─ Facilitador para o vídeo, faz perguntas
│  ├─ "Alguém viu o sensor? Onde fica?"
│  └─ Engajamento alto (é novidade, máquina nova)
│
├─ 08h40: Módulo 2a (Startup - parte 1) - 1 hora
│  ├─ Projetor: mostra checklist pré-op
│  ├─ Facilitador aponta cada item
│  ├─ Operários veem em tempo real (projetor)
│  ├─ "Agora você vai no seu tablet e faz o checklist"
│  ├─ Simulação interativa: cada um no seu tempo
│  └─ Dúvidas: facilitador responde
│
├─ 09h40: Pausa 15 min
│
├─ 10h00: Módulo 2b (Startup - parte 2, sequência) - 1 hora
│  ├─ Simulador de botões
│  ├─ "Qual é o primeiro botão?"
│  ├─ Operário toca no tablet
│  ├─ Simulador: "Correto! Agora o próximo?"
│  ├─ Alguns erram ordem, veem feedback
│  └─ Praticam 5 vezes até ficar automático
│
├─ 11h00: Pause café (30 min) + intervalo
│
├─ 11h30: Módulo 3 (Operação) - 1h30
│  ├─ Velocidade esperada, checklist 2h, ajustes
│  ├─ Menos prático, mais teórico
│  ├─ Operários assistem vídeo + leem procedimento
│
├─ 13h00: Almoço (1h)
│
├─ 14h00: Módulo 4 (Emergências) - 2 horas
│  ├─ Crítico, precisa ficar na cabeça
│  ├─ Facilitador faz role-play com alguns
│  ├─ "Sua máquina faz barulho estranho. O que faz?"
│  ├─ Simulador mostra consequências de cada ação
│
├─ 16h00: Avaliação Parte 1 (20 perguntas) - 20 min
│  ├─ Todos fazem teste no tablet (sem conversa)
│  ├─ 95 passam
│  ├─ 5 não passam (90% de corte)
│     Talk marca: "Refaça amanhã"
│
├─ 16h25: Avaliação Parte 2 (Simulador) - 20 min
│  ├─ Simulação prática (3 cenários)
│  ├─ 93 passam
│  ├─ 7 precisam rever
│     Talk oferece: "Revire Módulo 4 cenário 2"
│
├─ 16h50: Revisão rápida
│  └─ Facilitador faz recap de pontos críticos
│
└─ 17h00: Fim do dia
   ├─ 88/100 já têm certificado (88%)
   ├─ 12 precisam refazer amanhã
   ├─ Report: "Turno A: 88% certificados após Dia 1"
```

#### Dia 1 - Turno B (Tarde/Noite)

```
Mesmo conteúdo, Turno B
├─ 14h00 - 22h00 (8h)
├─ Mesma estrutura
├─ Resultado: 85/100 certificados após Dia 1
└─ 15 precisam refazer
```

#### Dia 1 - Turno C (Noite)

```
Terceiro turno (plantão)
├─ 22h00 - 06h00
├─ Mais complicado (menos facilitador, cansado)
├─ Mas Talks está 24/7
├─ Facilitador online (video call)
├─ Resultado: 75/100 após Dia 1
```

#### Dia 2-5 (Consolidação)

```
Padrão:
├─ Manhã: Novos módulos (Turno A novo, Turno B novo, Turno C novo)
├─ Tarde: Quem não passou ontem refaz avaliação
├─ Noite: Turno C aprende
│
├─ Talk faz auto-matching de horário
│  "Você é Turno A? Conteúdo disponível 06h-14h"
│  "Precisa refazer? Pode fazer qualquer hora"
│
├─ Conforme avançam, vão fazendo avaliação prática
│  "Ok, você passou teória. Amanhã você treina na máquina real com supervisor"
│
└─ Dia 5 final:
   ├─ Todos 200 certificados ✓
   ├─ Todos fazem 4h de prática real na máquina
   ├─ Todos assinam termo: "Fiz treinamento, estou pronto"
```

#### Dashboard: Gerente de Produção

```
Relatório Dia 1-5:

Aderência:
├─ Dia 1: 248/300 em progresso (82%) [1 turno não começou]
├─ Dia 2: 398/300 completaram módulos 1-2 (100%)
├─ Dia 3: 398/300 completaram módulos 1-3 (100%) [alguns refazendo)
├─ Dia 4: 395/300 certificados (98%) [3 casos especiais em andamento]
├─ Dia 5: 400/400 certificados (100%)

Qualidade:
├─ Avaliação Teórica: 94% média de sucesso
├─ Avaliação Prática: 97% média de sucesso
├─ Score geral: 9.2/10

Tempo:
├─ Tempo médio pra certificar: 7.5h (8h previstos)
├─ Módulo mais fast: Tour (20 min real, vs 30 min esperado)
├─ Módulo mais slow: Troubleshooting (2h15, vs 2h esperado)

Problemas Encontrados:
├─ 8 pessoas tiveram dificuldade com simulador de botões
│  Facilitador 1-on-1 = resolvido
│
├─ 3 pessoas do Turno C faltaram (doença)
│  Farão make-up quando recuperarem
│
└─ 1 cenário de emergência (gerador quebrado)
   Não estava no treinamento, Talk adicionou logo
   Todos refizeram avaliação com novo cenário
```

---

### Resultado (Dia 5)

**Antes (sem Talk):**
- Treinamento presencial 40h
- 3 semanas para 200 operários (turnos) = atraso
- Qualidade ruim (retrabalho 10%)
- Custo: 40h × 200 pessoas × R$ 150/h (salário) = R$ 1.2M
- Custo oportunidade: 14 dias de atraso × R$ 500k/dia = R$ 7M

**Com Talk (Dia 5):**
- Trilha de 8h teórica + 4h prática = 12h total
- Todos 200 operários certificados em 5 dias
- Qualidade ótima (erro <1% vs 10% antes)
- Custo: 8h × 200 pessoas × R$ 150/h + trilha = R$ 240k + R$ 50k = R$ 290k
- Oportunidade: 0 dias de atraso = R$ 7M economizados

**ROI:**
- Economia direta: R$ 1.2M (treinamento) - R$ 290k (Talk) = R$ 910k
- Economia indireta: R$ 7M (oportunidade) ÷ 5 = R$ 1.4M (evita parada de linha)
- Qualidade: 9% menos retrabalho = R$ 500k/ano (100% primeira vez vs 90%)
- **Total ROI: (R$ 910k + R$ 1.4M + R$ 500k) ÷ R$ 50k (custo Talk) = 56x em 1 ano**

---

**Conclusão:** Cada setor tem aplicações diferentes, mas o padrão é:
1. **Problema:** Treinamento lento, aderência questionável, custos altos
2. **Talk:** Aceleração, prova de competência, reaproveitável
3. **ROI:** Varia 5-56x dependendo de impacto operacional

---

**Última Atualização:** 2026-07-26  
**Manutenção:** Atualize casos reais conforme novos clientes usarem Talk
