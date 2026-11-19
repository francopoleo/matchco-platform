# 📚 Guia Completo: Course Editor + Quiz System

## ✅ Status Final - Versão 2.0

Todos os problemas foram **RESOLVIDOS, TESTADOS e OTIMIZADOS**:

### Melhorias Implementadas:
1. ✅ **Quiz Editor Central** - Nova página dedic ada para gerenciar perguntas (quiz-editor)
2. ✅ **Fluxo Intuitivo** - Criar pergunta → Editor de Pergunta → Adicionar Respostas → Voltar ao Editor
3. ✅ **Redirecionamentos Corretos** - Após criar/editar pergunta, volta direto ao editor
4. ✅ **UX Melhorado** - Cards com hover effects, ícones claros, ações óbvias
5. ✅ **Dados Hospitalares** - Comando para gerar dados de exemplo (hospital course + quizzes)
6. ✅ **Padrão de Padding** - TODOS os templates seguem pt-16 px-4 sm:px-6 lg:px-8
7. ✅ **Responsividade** - Mobile-first design, grid system adequado

---

## 🏥 Gerar Dados de Exemplo (Hospital)

### Criar Course com Dados Reais

Para testar o sistema com dados hospitalares reais, execute:

```bash
python manage.py create_hospital_sample_data <ORG_ID> [--user-id <USER_ID>]
```

**Exemplo:**
```bash
python manage.py create_hospital_sample_data 1
# ou especificar usuário:
python manage.py create_hospital_sample_data 1 --user-id 2
```

**O que será criado:**
- ✅ Curso: "Segurança do Paciente e Protocolos Hospitalares"
- ✅ 3 Módulos com tópicos reais:
  1. Higiene das Mãos e Prevenção de Infecções
  2. Identificação Segura do Paciente
  3. Controle de Infecções Relacionadas à Assistência
- ✅ 3 Quizzes com 7 questões (múltipla escolha e V/F)
- ✅ Respostas validadas para testes automáticos

---

## 🚀 Como Usar (Passo a Passo)

### **PARTE 1: CRIAR CONTEÚDO NO CURSO**

#### 1️⃣ Abrir Course Editor
```
1. Vá para: Console → Course Editor
2. Ou acesse: /console/course-editor/
3. Clique em um curso existente (ou crie um novo)
```

#### 2️⃣ Criar Módulo (se não existir)
```
Botão: "+ New Module"
Preencher:
  • Title: "Módulo 1: Introdução"
  • Description: "Conceitos básicos" (opcional)
Salvar
```

#### 3️⃣ Adicionar Conteúdo ao Módulo

Dentro do módulo, você verá botões para adicionar:
```
📝 Text         → Adicionar texto/conteúdo
🎥 Video        → Adicionar vídeo (YouTube, Vimeo)
📎 File/PDF     → Fazer upload de arquivo
✓ Quiz          → Criar quiz/teste
```

**Importante:** Clique no tipo de conteúdo que quer adicionar

---

### **PARTE 2: CRIAR QUIZ**

#### 1️⃣ Clicar em "+ Add Quiz" ou "✓ Quiz"
```
Você será levado para criar o quiz
```

#### 2️⃣ Preencher Configurações do Quiz
```
Campos obrigatórios:
  • Title*: "Quiz de Segurança"
  • Score mínimo*: 70 (0-100)
  
Campos opcionais:
  • Description: Explicar o que é o quiz
  • Type: Formativo / Prova / Certificação
  • Marcar: "Required" se for obrigatório
```

#### 3️⃣ Salvar Quiz
```
Ao clicar "Create Quiz":
  ✓ Quiz é criado com OWNER correto
  ✓ ORGANIZATION é setada automaticamente
  ✓ Você é redirecionado para o EDITOR DE QUIZ
  ✓ Conteúdo é linkado ao módulo automaticamente
```

---

### **PARTE 3: ADICIONAR PERGUNTAS**

#### 1️⃣ Você está no Quiz Editor
```
Página: Quizzes & Tests → [Nome do Quiz] → Add Questions
```

#### 2️⃣ Clicar em "+ Add Question"
```
Preencher:
  • Question Type*: 
      - Multiple Choice (opções de escolha)
      - True/False (V ou F)
      - Short Answer (resposta aberta)
      
  • Question Text*: "Qual é a resposta?"
  
  • Explanation: "Explicação da resposta" (aparece após submissão)
```

#### 3️⃣ Salvar Pergunta
```
Ao clicar "Add Question":
  ✓ Pergunta é criada
  ✓ ORDER é atribuída automaticamente
  ✓ Você vai para a tela de editar a pergunta
  ✓ Painel de RESPOSTAS aparece à direita
```

---

### **PARTE 4: ADICIONAR RESPOSTAS**

#### 1️⃣ No Painel de Respostas (lado direito)
```
Clique em: "+ Add Answer"
```

#### 2️⃣ Preencher Resposta
```
Campos:
  • Answer Text*: "A opção de resposta"
  • Correct: ✓ Marcar se for a resposta correta
```

#### 3️⃣ Validações Automáticas
```
✓ Obrigatório: Pelo menos 1 resposta marcada como correta
✓ Para M. Escolha: Típico 4 opções
✓ Para V/F: Exatamente 2 opções
```

#### 4️⃣ Adicionar Mais Respostas
```
Repetir o processo "+ Add Answer" para cada opção
```

---

## 📊 Estrutura Completa

```
COURSE
└── MODULES
    ├── TEXT (1 para n)
    ├── VIDEO (1 para n)
    ├── FILE (1 para n)
    └── QUIZ
        └── QUESTIONS
            └── ANSWERS
                ├── Correct: boolean
                └── Text: string

ADMIN TRACKING:
└── UserQuizAttempt (por usuário)
    ├── score, passed, time_spent
    └── UserAnswer (por questão respondida)
        ├── is_correct, selected_answer
        └── points_earned
```

---

## 🎯 Fluxo Visual (Resumido)

```
Course Editor
    ↓
    → Create/Edit Course
    ↓
    → Add Modules
    ↓
    → Add Content to Module:
         • Text
         • Video
         • File
         • QUIZ ← NOVO FLUXO
           ↓
           → Quiz Editor (Add Questions)
           ↓
           → Question Editor (Add Answers)
           ↓
           → Answer created with validation
           ↓
           → Back to Course Editor
```

---

## 🔐 Permissões & Dados

### Quem pode fazer o quê?

| Ação | Manager | Admin | Aluno |
|------|---------|-------|-------|
| Criar Quiz | ✓ | ✓ | ✗ |
| Editar Pergunta | ✓ | ✓ | ✗ |
| Ver Respostas | ✓ | ✓ | ✓ |
| Responder Quiz | ✗ | ✗ | ✓ |
| Ver Resultados | ✓ | ✓ | ✓ |
| Ver Histórico | ✓ | ✓ | ✓ (seu) |

### O que é rastreado?

Quando um aluno responde quiz:
- ✓ Cada pergunta respondida
- ✓ Se estava correta ou errada
- ✓ Score total em %
- ✓ Se passou ou falhou
- ✓ Tempo gasto
- ✓ Número de tentativa
- ✓ Data e hora

---

## 🐛 Troubleshooting

### Q: Quiz não aparece no módulo
**A:** O sistema cria automaticamente. Se não aparece:
1. Verifique se o quiz foi salvo
2. Recarregue a página (F5)
3. Verifique se pertence à mesma organização

### Q: Não consigo adicionar respostas
**A:** Possíveis causas:
1. Você está dentro de "Add Answer"?
2. Preencheu o "Answer Text"?
3. Há pelo menos 1 resposta como correta?

### Q: Score não calcula
**A:** Possíveis causas:
1. Não há respostas marcadas como correta
2. Estudante não finalizou o quiz
3. Recarregue e tente novamente

### Q: Estudante não consegue responder
**A:** Verifique:
1. Quiz está publicado no módulo?
2. Limite de tentativas não foi atingido?
3. Período de retentativa passou?

---

## 📱 Templates Atualizados

Todos os templates agora seguem o padrão:

```html
<!-- Header com padding correto -->
<div class="w-full pt-16 px-4 sm:px-6 lg:px-8">
    <div class="max-w-2xl mx-auto">
        <!-- Conteúdo com max-width responsivo -->
    </div>
</div>

<!-- Cards com styling Flowbite -->
<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6">
    <!-- Conteúdo do card -->
</div>

<!-- Formulários modernos -->
<input class="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700" />
```

---

## ✨ Features Completas

- ✅ Multi-tenant (por organização)
- ✅ Múltiplos tipos de perguntas
- ✅ Respostas com validação
- ✅ Rastreamento de tentativas
- ✅ Cálculo automático de score
- ✅ Feedback personalizado
- ✅ Histórico de respostas
- ✅ Dark mode
- ✅ Responsivo mobile
- ✅ Padding e styling padronizado
- ✅ Formulários Flowbite

---

## 🎓 Exemplo Completo (Real)

```
1. Criar Curso "Segurança do Paciente"
   Owner: admin
   Organization: Hospital Central

2. Criar Módulo "Protocolos de Cirurgia"
   
3. Adicionar Conteúdo:
   - TEXT: "Introdução aos protocolos"
   - VIDEO: "Técnica segura de cirurgia"
   - QUIZ: "Quiz de Segurança"

4. No Quiz "Quiz de Segurança":
   
   Pergunta 1: "Qual protocolo é obrigatório?"
   Respostas:
     ○ Protocolo A (correto ✓)
     ○ Protocolo B
     ○ Protocolo C
   
   Pergunta 2: "Verdadeiro ou Falso?"
   Respostas:
     ○ Verdadeiro (correto ✓)
     ○ Falso

5. Estudante vai para: /students/quiz/<id>/take/
   - Responde as questões
   - Clica "Submit Quiz"
   - Recebe feedback com gabarito
   - Score: 100% (Passou!)
   - Pode fazer retry se permitido
```

---

## 📞 Referência Rápida de URLs

```
Admin/Console:
/console/course-editor/                          # Lista cursos
/console/course-editor/<id>/                     # Editor do curso
/console/course-editor/modules/<id>/quiz/new/    # Criar quiz
/console/quizzes/<id>/editor/                    # Editor de perguntas
/console/quizzes/<id>/questions/new/             # Criar pergunta
/console/quizzes/<id>/questions/<qid>/edit/      # Editar pergunta
/console/quizzes/<id>/questions/<qid>/answers/new/ # Criar resposta

Estudante:
/students/quiz/<id>/take/                        # Responder quiz
/students/quiz/<id>/result/<aid>/                # Ver resultado
/students/quiz/<id>/attempts/                    # Histórico
```

---

## 🎉 Status: PRONTO PARA PRODUÇÃO

Todos os sistemas estão:
- ✅ Implementados
- ✅ Testados
- ✅ Documentados
- ✅ Seguindo padrões
- ✅ Com tratamento de erros
- ✅ Com rastreamento
- ✅ Multi-tenant seguro

**Você está pronto para usar!** 🚀
