# 📚 Estratégia de Rastreamento de Conclusão de Módulos/Cursos

## Problema Atual
- ❌ Apenas navegar marca como concluído
- ❌ Não valida aprendizado real
- ❌ Sem rastreamento de tempo
- ❌ Sem requisitos claros

---

## 1️⃣ ANÁLISE DE MELHORES PRÁTICAS

### Udemy / Skillshare
- ✅ Videos: Marca completo em 95% do tempo
- ✅ Quizzes: Marca completo ao passar (min score)
- ✅ Textos: Marca completo ao ler (scroll 100%)
- ✅ Progressão: Sequencial (não deixa pular)
- ❌ Fraco em: Rastreamento de atenção

### LinkedIn Learning / Pluralsight
- ✅ Rastreamento de tempo gasto
- ✅ Progresso visual (%)
- ✅ "Retomar" se saiu no meio
- ✅ Estatísticas por usuário
- ✅ Marca "em andamento" quando inicia

### Sistemas Corporativos (SAP, Cornerstone)
- ✅ Tempo mínimo obrigatório
- ✅ Todos os vídeos DEVEM ser assistidos 100%
- ✅ Quizzes com score mínimo
- ✅ Certificado ao completar
- ✅ Limite de tempo para completar (ex: 30 dias)
- ✅ Relatórios detalhados

### Plataformas Médicas/Saúde
- ✅ Rigoroso: Tempo mínimo + quizzes obrigatórios
- ✅ Rastreia acesso, tempo e respostas
- ✅ Auditoria completa
- ✅ Bloqueio de progressão até requisitos

---

## 2️⃣ PLANO DE IMPLEMENTAÇÃO (3 NÍVEIS)

### NÍVEL 1: BÁSICO (Semana 1-2)
**Para começar rápido, sem complexidade**

```
Requisitos para marcar módulo como CONCLUÍDO:
├── Para TEXTO:
│   ├── Scroll até 100% da página
│   └── Tempo mínimo: 2 minutos (ou configurável)
│
├── Para VIDEO:
│   ├── Assistir até 95% do tempo total
│   └── (ex: video 10min → 9:30 min assistido)
│
└── Para QUIZ:
    ├── Passar no quiz (≥ score mínimo)
    ├── Só deixa ir pro próximo após passar
    └── Pode revisar respostas após passar
```

**Implementação:**
- ✅ Adicionar modelo `ModuleProgress` para rastrear
- ✅ JavaScript para video playback (95% rule)
- ✅ JavaScript para scroll tracking (texto)
- ✅ Quizzes já valida score
- ✅ Mostrar % de progresso
- ⏱️ Tempo: ~15 horas

**Banco de dados:**
```python
class ModuleProgress(models.Model):
    user = FK(User)
    module = FK(Module)
    started_at = DateTime
    completed_at = DateTime (null initially)
    progress_percent = IntegerField (0-100)
    time_spent_seconds = Integer
    
    # Por tipo de conteúdo
    text_scrolled_percent = Integer
    video_watched_percent = Integer
    quiz_passed = Boolean
```

**UI:**
```
[=====>     ] 50% Completo

✓ Texto: Lido
○ Video: 65% assistido (faltam 3:35 min)
○ Quiz: Não iniciado

[Próximo →] (desabilitado até 100%)
```

---

### NÍVEL 2: INTELIGENTE (Semana 3-4)
**Com rastreamento de tempo e requisitos customizáveis**

```
Por Módulo, configurar:
├── Tempo mínimo de permanência (ex: 5 min)
├── Video: % mínimo (padrão 95%, customizável)
├── Texto: scroll 100% ou tempo mínimo
├── Quiz: score mínimo + tentativas
└── Ordem: qual conteúdo completar primeiro
```

**Funcionalidades:**
- ✅ Tempo total gasto por módulo
- ✅ Relatório: "João gastou 15min no Módulo 1"
- ✅ Requisitos customizáveis por módulo
- ✅ Badge visual (ex: "Tempo insuficiente")
- ✅ Retomar do ponto onde parou (video/texto)
- ✅ Status: "Em andamento", "Completo", "Bloqueado"

**Novo modelo:**
```python
class ModuleRequirements(models.Model):
    module = FK(Module)
    min_time_minutes = Integer (ex: 5)
    video_min_percent = Integer (ex: 95)
    text_min_scroll_percent = Integer (ex: 100)
    quiz_required = Boolean
    quiz_min_score = Integer (ex: 70)
    quiz_attempts_allowed = Integer
    content_order = JSONField (ex: ["text", "video", "quiz"])

class ModuleProgress(models.Model):
    # ... do Nível 1
    time_spent_minutes = Integer
    status = Choice(['not_started', 'in_progress', 'blocked', 'completed'])
    last_activity = DateTime
```

**Admin UI:**
```
Módulo: "Higiene das Mãos"

Requisitos:
- Tempo mínimo: 5 minutos
- Vídeo: Assistir 95% (min 9:30 de 10min)
- Texto: Ler 100%
- Quiz: Passar (≥ 70%)
- Ordem: 1) Texto, 2) Vídeo, 3) Quiz

Permitir pular? [ ] Sim [ ] Não
```

**⏱️ Tempo: ~25 horas**

---

### NÍVEL 3: PROFISSIONAL (Semana 5-6)
**Para treinamento corporativo e certificação**

```
Completo rastreamento + Certificação
├── Auditoria: log de tudo
├── Certificado: gerado automaticamente
├── Limite de tempo: "Completar em 30 dias"
├── Retreinamento: validar após 6 meses
└── Dashboard: relatórios detalhados
```

**Funcionalidades:**
- ✅ Certificado PDF gerado automaticamente
- ✅ Auditoria completa (quem, quando, quanto tempo)
- ✅ Limite de tempo por curso (deadline)
- ✅ Retrainig automático (ex: recertificar em 6 meses)
- ✅ Dashboard admin: "Status de 150 funcionários"
- ✅ Relatório por departamento
- ✅ Notificações: "João ainda não completou o curso"
- ✅ Bloqueio de progressão: "Você deve completar Módulo 1 antes do 2"
- ✅ Historico: "João completou 5x este curso"

**Novos modelos:**
```python
class CourseEnrollment(models.Model):
    user = FK(User)
    course = FK(Course)
    enrolled_at = DateTime
    deadline = DateTime (ex: 30 dias após inscrição)
    status = Choice(['enrolled', 'in_progress', 'completed', 'expired'])

class AuditLog(models.Model):
    user = FK(User)
    action = String (ex: "video_watched", "quiz_passed")
    module = FK(Module)
    timestamp = DateTime
    details = JSONField (ex: {"watched_percent": 95, "time_minutes": 10})

class Certificate(models.Model):
    user = FK(User)
    course = FK(Course)
    issued_at = DateTime
    valid_until = DateTime
    pdf_file = FileField
    status = Choice(['valid', 'expired', 'revoked'])
```

**Dashboard Admin:**
```
Treinamento: "Segurança do Paciente"

Participantes: 150
- ✅ Completos: 120 (80%)
- 🟡 Em andamento: 25 (17%)
- ❌ Não iniciados: 5 (3%)

Módulos (% de conclusão):
1. Higiene das Mãos: 95%
2. Identificação: 88%
3. Infecções: 92%

Deadline: 2026-09-30 (34 dias)

[Relatório PDF] [Notificar não iniciados] [Gerar certificados]
```

**⏱️ Tempo: ~40 horas**

---

## 3️⃣ COMPARAÇÃO VISUAL

```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│     RECURSO     │   NÍVEL 1    │   NÍVEL 2    │   NÍVEL 3    │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Básico          │ ✅ Sim       │ ✅ Sim       │ ✅ Sim       │
│ Tempo rastreado │ ❌ Não       │ ✅ Sim       │ ✅ Sim       │
│ Customizável    │ ❌ Não       │ ✅ Sim       │ ✅ Sim       │
│ Certificado     │ ❌ Não       │ ❌ Não       │ ✅ Sim       │
│ Auditoria       │ ❌ Não       │ ❌ Não       │ ✅ Sim       │
│ Dashboard       │ ❌ Não       │ 🟡 Básico    │ ✅ Completo  │
│ Deadline        │ ❌ Não       │ ❌ Não       │ ✅ Sim       │
│ Complexidade    │ Baixa        │ Média        │ Alta         │
│ Tempo Dev       │ 15h          │ 25h          │ 40h          │
└─────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 4️⃣ MINHA RECOMENDAÇÃO

### Para Talk (Hospital/Saúde) - **Híbrido: Nível 1 + Nível 3**

**POR QUÊ:**
- Saúde é regulatória (precisa auditoria)
- Certificados são importantes
- Mas não precisa de UI tão complexa no início

**FASES:**
```
FASE 1 (Semanas 1-2): Implementar Nível 1 básico
├── Rastrear: texto (scroll), video (95%), quiz (score)
├── Bloquear: não deixar pular sem completar
├── Mostrar: % de progresso simples
└── Usar para: primeiros testes

FASE 2 (Semanas 3-4): Adicionar Nível 3 (Auditoria + Certificado)
├── Adicionar: AuditLog (rastreia tudo)
├── Gerar: Certificados PDF automáticos
├── Adicionar: CourseEnrollment (deadline)
└── Criar: Dashboard básico admin

FASE 3 (Semana 5+): Melhorar UI + Customização (Nível 2)
├── Admin: customizar requisitos por módulo
├── Dashboard: mais detalhado
├── Notificações: email de progresso
└── Relatórios: por usuário/departamento
```

---

## 5️⃣ TECNOLOGIA POR RECURSO

### Video Tracking (95% rule)
```javascript
// Ao 95% do vídeo, marcar como completo
video.addEventListener('timeupdate', function() {
    const percent = (video.currentTime / video.duration) * 100;
    if (percent >= 95) {
        markModuleComplete('video', 95);
    }
});
```

### Scroll Tracking (Texto)
```javascript
// Detectar se scrollou até o final
window.addEventListener('scroll', function() {
    const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
    if (scrollPercent >= 100) {
        markModuleComplete('text', 100);
    }
});
```

### Time Tracking
```python
# Backend
class ModuleProgress(models.Model):
    started_at = timezone.now()
    
    @property
    def time_spent_minutes(self):
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return (timezone.now() - self.started_at).total_seconds() / 60
```

### Certificado PDF
```python
# Gerar certificado ao completar
from reportlab.pdfgen import canvas

def generate_certificate(user, course):
    c = canvas.Canvas("certificate.pdf")
    c.drawString(100, 100, f"Certificado de {user.name}")
    c.drawString(100, 80, f"Completou: {course.title}")
    c.drawString(100, 60, f"Data: {timezone.now().date()}")
    c.save()
```

---

## 6️⃣ BANCO DE DADOS (Estrutura)

```sql
-- Nível 1: Rastreamento básico
CREATE TABLE module_progress (
    id INT PRIMARY KEY,
    user_id INT,
    module_id INT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP NULL,
    progress_percent INT (0-100),
    time_spent_seconds INT,
    video_watched_percent INT,
    text_scrolled_percent INT,
    quiz_passed BOOLEAN
);

-- Nível 2: Requisitos customizáveis
CREATE TABLE module_requirements (
    id INT PRIMARY KEY,
    module_id INT UNIQUE,
    min_time_minutes INT,
    video_min_percent INT,
    text_min_scroll INT,
    quiz_required BOOLEAN,
    quiz_min_score INT,
    content_order JSON
);

-- Nível 3: Auditoria + Certificação
CREATE TABLE course_enrollment (
    id INT PRIMARY KEY,
    user_id INT,
    course_id INT,
    enrolled_at TIMESTAMP,
    deadline TIMESTAMP,
    status VARCHAR (enrolled, in_progress, completed, expired)
);

CREATE TABLE audit_log (
    id INT PRIMARY KEY,
    user_id INT,
    action VARCHAR,
    module_id INT,
    timestamp TIMESTAMP,
    details JSON
);

CREATE TABLE certificate (
    id INT PRIMARY KEY,
    user_id INT,
    course_id INT,
    issued_at TIMESTAMP,
    valid_until TIMESTAMP,
    pdf_file VARCHAR,
    status VARCHAR
);
```

---

## 7️⃣ USER STORIES

### Estudante
```
"Eu quero ver meu progresso no curso"
- Visualizar % de conclusão
- Ver qual módulo falta
- Saber quanto tempo gastei

"Eu quero saber o que falta para completar"
- Badge mostrando "Faltam 3:45 min do vídeo"
- "Responder quiz para desbloquear próximo"
```

### Admin/Gestor Treinamento
```
"Eu quero rastrear quem completou"
- Dashboard: "120 de 150 funcionários"
- Relatório: "João completou em 2 horas"
- Auditoria: "Quem fez o quizz em que data/hora"

"Eu quero gerar certificados"
- Automático ao completar
- Relatório: "Emitidos 120 certificados"

"Eu quero customizar requisitos"
- Admin: "Este módulo precisa 10min mínimo"
- Admin: "Este vídeo deve ser 100% assistido"
```

---

## 8️⃣ TIMELINE PROPOSTO

```
SEMANA 1-2: Nível 1 (Básico)
├── Seg 1: Modelagem + video tracking
├── Seg 2: Text tracking + Quiz validation
└── Teste: Funciona baseline

SEMANA 3-4: Nível 3 (Auditoria)
├── Seg 3: AuditLog + Certificate models
├── Seg 4: PDF generation + Dashboard básico
└── Teste: Certificados gerados

SEMANA 5-6: Nível 2 (Polish)
├── Seg 5: ModuleRequirements + Admin UI
├── Seg 6: Relatórios + Notificações
└── Teste: Tudo integrado

SEMANA 7: QA + Documentação
└── Testes end-to-end

TOTAL: ~7 semanas (1.5 meses) para sistema completo
```

---

## 9️⃣ CHECKLIST FINAL

### Para começar AGORA (Nível 1):
- [ ] Criar modelo `ModuleProgress`
- [ ] Adicionar video playback tracking
- [ ] Adicionar scroll tracking para textos
- [ ] Bloquear próximo módulo até completar
- [ ] Mostrar % de progresso
- [ ] Testar com real users

### Próxima iteração (Nível 3):
- [ ] Adicionar `AuditLog`
- [ ] Gerar certificados PDF
- [ ] Adicionar `CourseEnrollment` com deadline
- [ ] Dashboard admin básico

### Futuro (Nível 2):
- [ ] `ModuleRequirements` (customização)
- [ ] Admin UI melhorado
- [ ] Relatórios avançados
- [ ] Notificações automáticas

---

## 🎯 RESUMO EXECUTIVO

| Aspecto | Decision |
|---------|----------|
| **Abordagem** | Implementar Nível 1 + Nível 3 (híbrido) |
| **Razão** | Saúde precisa auditoria, Nível 1 é rápido |
| **Tempo total** | ~7 semanas para sistema completo |
| **Start ASAP** | Nível 1 (2 semanas) |
| **Quick wins** | Video 95%, Quiz score, Certificados |
| **Prioridade máxima** | Auditoria (saúde = regulatória) |

---

**Próximos passos:**
1. Você quer começar com Nível 1 AGORA?
2. Ou quer planejar tudo junto antes de começar?
3. Quer que eu implemente Nível 1 já?

Me diga! 🚀
