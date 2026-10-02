# 📍 Sistema de Documentação Contextual

**Data**: 2026-10-02  
**Status**: Novo sistema integrado

---

## O que é?

Sistema que **detecta automaticamente em qual página o usuário está** e mostra documentação relevante.

- **Admin em `/console/recruitment/candidatos/`** → Mostra doc sobre Candidatos
- **Admin em `/console/courses/`** → Mostra doc sobre Cursos
- **Usuário final em `/candidato/signup/`** → Mostra guia de Signup
- **Qualquer página** → Widget flutuante com ajuda contextual

---

## Arquivos Criados

```
/Users/franco/Dev/talk/talk/console/
├─ contextual_docs.py                    # Mapeamento de rotas → docs
├─ context_processors.py                 # Injeta contexto em templates
└─ templates/console/includes/
   └─ contextual_help_widget.html        # Widget flutuante
```

---

## Como Funciona

### 1. Mapeamento de Rotas

Arquivo: `console/contextual_docs.py`

```python
CONTEXTUAL_DOCS = {
    'recruitment_candidate_list': {
        'titulo': '👥 Candidatos',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md',
        'descricao': 'Gerencie candidatos, veja scores...',
    },
    # ... mais rotas
}
```

**Significa**: Quando a view é `recruitment_candidate_list`, mostra doc sobre Candidatos.

### 2. Context Processor

Arquivo: `console/context_processors.py`

A cada requisição:
1. Detecta qual view está sendo acessada
2. Procura a doc correspondente em `CONTEXTUAL_DOCS`
3. Injeta no contexto do template como `{{ doc }}`

```python
def documentation_context(request):
    resolver_match = resolve(request.path)
    view_name = resolver_match.url_name
    
    contextual_doc = get_contextual_doc(view_name, is_admin)
    
    return {
        'doc': contextual_doc,
        'doc_sections': doc_sections,
        'view_name': view_name,
    }
```

### 3. Registrado em Settings

Arquivo: `cep/settings/base.py`

```python
'context_processors': [
    ...
    'console.context_processors.documentation_context',  # ← Adicionado
]
```

### 4. Widget HTML

Arquivo: `templates/console/includes/contextual_help_widget.html`

Widget flutuante que aparece em qualquer página:
- Mostra título e descrição da doc relevante
- Links para documentação completa
- Menu de tópicos relacionados
- Pode ser fechado com ✕

---

## Como Usar em Templates

### Opção 1: Widget Automático (Recomendado)

Adicione em `templates/console/base.html` ou `templates/ui/base_public.html`:

```django
{# No final do body, antes do closing </body> #}
{% include "console/includes/contextual_help_widget.html" %}
```

**Resultado**: Widget aparece automaticamente em TODAS as páginas.

---

### Opção 2: Manual (Customizado)

Se quiser controlar manualmente onde aparece:

```django
{# Em templates/console/recruitment/candidate_list.html #}

<div class="page-content">
  {# ... conteúdo da página #}
</div>

{# Mostrar widget contextual #}
{% if doc %}
<div class="help-section">
  <h3>{{ doc.titulo }}</h3>
  <p>{{ doc.descricao }}</p>
  <a href="{% url 'console:documentation-index' %}">Ver documentação</a>
</div>
{% endif %}
```

---

## Adicionar Novas Páginas ao Sistema

### Passo 1: Identificar o `view_name`

No Django, cada view tem um `name` registrado em `urls.py`:

```python
# urls.py
path('candidatos/', CandidateListView.as_view(), name='candidate_list'),
#                                                  ↑ Este é o view_name
```

### Passo 2: Adicionar ao Mapeamento

Edite `console/contextual_docs.py`:

```python
CONTEXTUAL_DOCS = {
    # ... docs existentes
    
    # NOVA PÁGINA
    'candidate_list': {  # ← view_name da sua página
        'titulo': '👥 Meus Candidatos',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md',
        'ancora': 'candidatos',  # âncora no documento (opcional)
        'descricao': 'Visualize e gerencie candidatos inscritos',
    },
}
```

### Passo 3: Pronto!

A documentação aparecerá automaticamente quando acessar essa página.

---

## Exemplo: Fluxo Completo

### 1. Usuário acessa página
```
GET /console/recruitment/candidatos/
```

### 2. Django roteia
```python
# urls.py encontra:
path('candidatos/', CandidateListView.as_view(), name='candidate_list')
```

### 3. Context Processor detecta
```python
view_name = 'candidate_list'
contextual_doc = CONTEXTUAL_DOCS['candidate_list']
# {
#     'titulo': '👥 Meus Candidatos',
#     'secao': 'Recrutamento',
#     'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md',
#     'descricao': '...'
# }
```

### 4. Template renderiza
```django
<div class="fixed bottom-6 right-6">
  <h3>{{ doc.titulo }}</h3>  {# "👥 Meus Candidatos" #}
  <p>{{ doc.descricao }}</p> {# "Visualize e gerencie..." #}
  <a href="...">Ver documentação</a>
</div>
```

### 5. Browser mostra
```
┌─────────────────────────┐
│ 👥 Meus Candidatos      │
├─────────────────────────┤
│ Visualize e gerencie... │
│                         │
│ → Documentação completa │
│ → Ver meus candidatos   │
│ → Mais tópicos          │
└─────────────────────────┘
```

---

## Seções Disponíveis

```python
doc_sections = {
    'Recrutamento': [...],  # Docs sobre recrutamento
    'Cursos': [...],        # Docs sobre cursos
    'Admin': [...],         # Docs de administração
    'Candidato': [...],     # Docs para usuário final
}
```

---

## Diferença: Admin vs Usuário Final

O sistema detecta automaticamente:

```python
is_admin = request.path.startswith('/console/')
```

- **`/console/*`** → Admin (mostra docs administrativas)
- Qualquer outra página → Usuário final (mostra docs públicas)

---

## Customizações Possíveis

### Mudar posição do widget
Arquivo: `contextual_help_widget.html`

```html
<div class="fixed bottom-6 right-6">  {# ← Mude aqui #}
```

Opções:
- `bottom-6 right-6` → Canto inferior direito (padrão)
- `bottom-6 left-6` → Canto inferior esquerdo
- `top-6 right-6` → Canto superior direito
- `top-6 left-6` → Canto superior esquerdo

### Mudar tema
```html
<div class="bg-white dark:bg-gray-800">  {# Cores #}
<div class="bg-gradient-to-r from-blue-50">  {# Gradiente #}
```

### Adicionar ícone
```html
<h3>{{ doc.titulo }}  <span class="icon">?</span></h3>
```

---

## Teste

### 1. Start server
```bash
python talk/manage.py runserver 0.0.0.0:8001
```

### 2. Acesse uma página admin
```
https://direct.ddns.net/console/recruitment/candidatos/
```

### 3. Widget deve aparecer canto inferior direito

---

## Status

✅ **PRONTO PARA USAR**

Apenas adicione `{% include "console/includes/contextual_help_widget.html" %}` ao seu template base.

---

## Próximos Passos (Opcional)

- [ ] Adicionar mais mapeamentos (rotas → docs)
- [ ] Customizar widget por página (cores, posição)
- [ ] Analytics (quais docs são mais clicadas)
- [ ] Feedback ("Esta página foi útil?")
- [ ] Tutorial tours (primeiros cliques do usuário novo)
- [ ] Notificações (novo documento publicado)
