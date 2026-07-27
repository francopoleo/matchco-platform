# 📋 Quiz & Tests - Fluxo Completo

## 🚀 Como Funciona o Sistema de Quizzes

### 1️⃣ **Criando um Quiz no Course Editor**

**Passo 1: Abrir Course Editor**
```
Console → Course Editor → Selecionar Curso
```

**Passo 2: Adicionar módulo (se não existir)**
```
Botão: "+ New Module"
Preencher: Título e descrição
```

**Passo 3: Adicionar Quiz ao Módulo**
```
No módulo, clicar: "✓ Quiz" ou "+ Add Quiz"
Preencher:
  - Título do Quiz
  - Descrição (opcional)
  - Score mínimo para passar (0-100)
  - Tipo (Formativo/Prova/Certificação)
  - Marcar como "Obrigatório" se necessário
```

**Passo 4: Será redirecionado para o Quiz Editor**
```
Automaticamente vai para a tela de adicionar perguntas
```

---

### 2️⃣ **Adicionando Perguntas ao Quiz**

**No Quiz Editor:**
```
Botão: "+ Add Question"
Preencher:
  - Tipo da questão (Múltipla escolha/V-F/Resposta curta)
  - Texto da pergunta
  - Explicação (para feedback - opcional)
Clicar: "Add Question"
```

**Será redirecionado para editar a questão com a opção de adicionar respostas**

---

### 3️⃣ **Adicionando Respostas à Pergunta**

**Na tela de edição da pergunta:**
```
Lado direito: Painel "Answers"
Botão: "+ Add Answer"
Preencher:
  - Texto da resposta
  - Marcar "Correct" se for a resposta correta
Clicar: "Add Answer"
Repetir para cada opção
```

**Validações:**
- ✓ Obrigatório: Mínimo 1 resposta marcada como correta
- ✓ Para múltipla escolha: Típico 4 opções
- ✓ Para V/F: Exatamente 2 opções (True/False)

---

### 4️⃣ **Fluxo do Estudante - Responder Quiz**

**Estudante acessa o quiz:**
```
URL: /students/quiz/<id>/take/
```

**O que ele vê:**
```
- Questões na ordem (original ou aleatória)
- Opções de resposta (depende do tipo)
- Timer (se houver limite de tempo)
```

**Submeter:**
```
Botão: "Submit Quiz"
Sistema calcula score automaticamente
```

**Ver Resultado:**
```
Automaticamente redireciona para resultado
Mostra:
  - Score em %
  - Acertos/Total
  - Detalhamento de cada questão
  - Gabarito completo
  - Explicações
```

---

## 🔧 Componentes Principais

### **Views**

| Função | URL | Permissão |
|--------|-----|-----------|
| Criar Quiz (como conteúdo) | `/console/course-editor/modules/<id>/quiz/new/` | Manager |
| Editor de Quiz (adicionar perguntas) | `/console/quizzes/<id>/editor/` | Manager |
| Criar Pergunta | `/console/quizzes/<id>/questions/new/` | Manager |
| Editar Pergunta | `/console/quizzes/<id>/questions/<qid>/edit/` | Manager |
| Criar Resposta | `/console/quizzes/<id>/questions/<qid>/answers/new/` | Manager |
| Estudante Responder | `/students/quiz/<id>/take/` | Autenticado |
| Ver Resultado | `/students/quiz/<id>/result/<aid>/` | Autenticado |
| Histórico | `/students/quiz/<id>/attempts/` | Autenticado |

### **Modelos**

```
Quiz
├── Organization (FK)
├── Owner (FK - User)
├── Configurações:
│   ├── quiz_type (formativo/prova/certificação)
│   ├── required_score_to_pass (0-100)
│   ├── is_required (bool)
│   ├── allow_multiple_attempts (bool)
│   ├── max_attempts (int)
│   ├── time_limit_minutes (int)
│   └── ...mais 5 campos
│
├── Question (múltiplas)
│   ├── question_type (multiple_choice/true_false/short_answer)
│   ├── text (pergunta)
│   ├── explanation (feedback)
│   │
│   └── Answer (múltiplas)
│       ├── text (opção)
│       └── correct (bool)
│
└── UserQuizAttempt (histórico por usuário)
    ├── user (FK)
    ├── attempt_number
    ├── score (%)
    ├── passed (bool)
    └── UserAnswer (múltiplas)
        ├── question (FK)
        ├── selected_answer (FK)
        ├── is_correct (bool)
        └── points_earned
```

---

## ✅ O Que Funciona Agora

- ✅ Criar Quiz no Course Editor
- ✅ Adicionar Perguntas ao Quiz
- ✅ Adicionar Respostas às Perguntas
- ✅ 4 tipos de perguntas suportados
- ✅ Estudante pode responder quiz
- ✅ Sistema calcula score automaticamente
- ✅ Feedback com gabarito e explicações
- ✅ Histórico de tentativas
- ✅ Multi-tenant (por organização)
- ✅ Rastreamento completo de respostas

---

## 🎯 Exemplos de Uso

### Exemplo 1: Quiz Formativo (Praticar)
```
Tipo: Formativo
Obrigatório: Não
Múltiplas tentativas: Sim
Score mínimo: 70%
Feedback: Imediato por questão
```

### Exemplo 2: Prova (Avaliação)
```
Tipo: Prova
Obrigatório: Sim
Múltiplas tentativas: Sim (máx 3)
Período de retentativa: 7 dias
Score mínimo: 80%
Feedback: Apenas score final
Tempo limite: 60 minutos
```

### Exemplo 3: Certificação
```
Tipo: Certificação
Obrigatório: Sim
Múltiplas tentativas: Não
Score mínimo: 90%
Feedback: Adiado (após aprovação)
Pontos: +500
```

---

## 🐛 Troubleshooting

### Problema: Quiz não aparece no módulo
**Solução:** Verifique se o quiz foi criado com sucesso. O sistema deve criar automaticamente o link Content.

### Problema: Questões não salvam
**Solução:** Certifique-se de que:
- Você está logado como manager
- O quiz pertence à sua organização
- Você preencheu todos os campos obrigatórios

### Problema: Estudante não consegue responder
**Solução:** Verifique:
- Limite de tentativas não foi atingido
- Período de retentativa passou
- Quiz está publicado na disciplina

---

## 📊 Dados Rastreados

Cada tentativa de quiz do estudante registra:
- ✓ Quando começou e terminou
- ✓ Quanto tempo gastou
- ✓ Score em % (automático)
- ✓ Se passou ou falhou
- ✓ Cada resposta (correta/errada)
- ✓ Pontos ganhos

Admin pode ver tudo isso em:
```
Console → Quizzes & Tests → [Quiz] → Attempts
```
