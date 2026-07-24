# Checklist Rápido - Criar/Alterar Página

**Tempo**: ~30 min por página  
**Dificuldade**: ⭐ Fácil (copy & cola)

---

## 📋 Antes de Começar

- [ ] Li [PAGE_LAYOUT_STANDARD.md](PAGE_LAYOUT_STANDARD.md)?
- [ ] Tenho um tipo de página similar para copiar?
- [ ] Vim neste checklist para validar?

---

## 🏗️ Passo 1: Estrutura Base (5 min)

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Page Title' %}{% endblock %}

{% block content %}
<div class="w-full">
    <!-- Seções aqui -->
</div>
{% endblock %}
```

**Checklist**:
- [ ] Estende de `console/base.html`
- [ ] Tem `{% block title %}`
- [ ] Tem `<div class="w-full">`

---

## 🎨 Passo 2: Componentes (10 min)

Escolha padrão por tipo:

### Tipo A: Dashboard (KPI Grid)
```django
<!-- Header -->
<header class="mb-8 px-4 lg:px-8">
    <h1 class="text-3xl font-bold">Title</h1>
</header>

<!-- KPI Grid -->
<div class="px-4 lg:px-8 mb-8">
    <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div class="kpi"><!-- 1 --></div>
        <div class="kpi"><!-- 2 --></div>
        <div class="kpi"><!-- 3 --></div>
        <div class="kpi"><!-- 4 --></div>
    </div>
</div>

<!-- Tabela/Cards -->
<div class="px-4 lg:px-8">
    <!-- Content -->
</div>
```

**Checklist**:
- [ ] Header com `mb-8 px-4 lg:px-8`
- [ ] KPI Grid com `gap-6 sm:grid-cols-2 lg:grid-cols-4`
- [ ] Seções separadas com `mb-8`

### Tipo B: Lista com Filtro
```django
<!-- Header -->
<header class="mb-8 px-4 lg:px-8">
    <h1 class="text-3xl font-bold">Title</h1>
    <a href="{% url 'create' %}" class="btn-primary">New</a>
</header>

<!-- Filtro Form -->
<form method="get" class="card mb-8 mx-4 lg:mx-8">
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Filters -->
    </div>
</form>

<!-- Tabela Desktop -->
<div class="px-4 lg:px-8 mb-8 hidden md:block">
    <table class="table">
        <!-- Content -->
    </table>
</div>

<!-- Cards Mobile -->
<div class="space-y-3 px-4 lg:px-8 md:hidden">
    <!-- Cards -->
</div>
```

**Checklist**:
- [ ] Header com button de ação
- [ ] Form filtro em card
- [ ] Tabela em `hidden md:block`
- [ ] Cards em `md:hidden`

### Tipo C: Formulário
```django
<!-- Header -->
<header class="mb-8 px-4 lg:px-8">
    <h1 class="text-3xl font-bold">Title</h1>
</header>

<!-- Form Card -->
<div class="px-4 lg:px-8 pb-8">
    <div class="card max-w-2xl">
        <div class="card-header">
            <h2 class="card-title">Form Title</h2>
        </div>
        
        <form method="post" class="card-body space-y-4">
            {% csrf_token %}
            <!-- Fields -->
        </form>
        
        <div class="card-footer">
            <button type="submit" class="btn-primary">Save</button>
            <button type="reset" class="btn-secondary">Clear</button>
        </div>
    </div>
</div>
```

**Checklist**:
- [ ] Card limitado com `max-w-2xl`
- [ ] Form com `{% csrf_token %}`
- [ ] Buttons em footer
- [ ] Space between fields (`space-y-4`)

---

## 📱 Passo 3: Responsividade (5 min)

- [ ] Testou em mobile (375px)?
- [ ] Testou em tablet (768px)?
- [ ] Testou em desktop (1024px+)?
- [ ] Sem scrollbar horizontal em mobile?
- [ ] Conteúdo legível em mobile?
- [ ] Buttons funcionam em mobile?
- [ ] Forms visíveis completamente?

**Classes Essenciais**:
```
sm:  → 640px (tablets portrait)
md:  → 768px (tablets landscape)
lg:  → 1024px (desktops small)
xl:  → 1280px (desktops large)
2xl: → 1536px (4K)
```

---

## 🌙 Passo 4: Dark Mode (2 min)

- [ ] Todos textos têm `dark:text-white`?
- [ ] Todos backgrounds têm `dark:bg-gray-800`?
- [ ] Todos borders têm `dark:border-gray-700`?
- [ ] Testou dark mode (clique ícone moon)?
- [ ] Nada fica ilegível no dark?

**Template Rápido**:
```django
<!-- Texto -->
<p class="text-gray-900 dark:text-white">Text</p>

<!-- Background -->
<div class="bg-white dark:bg-gray-800">Content</div>

<!-- Border -->
<div class="border-gray-200 dark:border-gray-700">Content</div>
```

---

## ✅ Passo 5: Checklist Final (3 min)

**Layout**:
- [ ] `<div class="w-full">` no topo?
- [ ] Removeu `max-w-6xl`?
- [ ] Removeu `mx-auto`?
- [ ] Tem `px-4 lg:px-8` em seções?

**Componentes**:
- [ ] Usa `.badge` para status?
- [ ] Usa `.table` para tabelas?
- [ ] Usa `.card` para containers?
- [ ] Usa `.kpi` para KPIs?
- [ ] Usa `.btn-*` para buttons?

**Responsividade**:
- [ ] Funciona mobile (375px)?
- [ ] Funciona tablet (768px)?
- [ ] Funciona desktop (1024px+)?
- [ ] Sem scrollbar horizontal?

**Dark Mode**:
- [ ] Text: `dark:text-white` ou `dark:text-gray-*`?
- [ ] BG: `dark:bg-gray-800` ou `dark:bg-gray-900`?
- [ ] Border: `dark:border-gray-700` ou `dark:border-gray-600`?

**Código**:
- [ ] Sem espaços em branco desnecessários?
- [ ] Indentação consistente (2 ou 4 espaços)?
- [ ] Nomes de classes claros?
- [ ] Comentários só onde necessário?

**Performance**:
- [ ] Nenhum CSS inline?
- [ ] Nenhuma classe Tailwind duplicada?
- [ ] Nenhum JS desnecessário?

---

## 🚀 Submeter para Revisão

**Antes de fazer commit**:

1. **Local test**:
   ```bash
   python manage.py runserver 8010
   ```
   - Acesse a página
   - Teste em mobile, tablet, desktop
   - Teste dark mode

2. **Validação**:
   - [ ] Sem erros no console (F12)?
   - [ ] Sem warnings?
   - [ ] Estrutura HTML válida?

3. **Commit**:
   ```bash
   git add .
   git commit -m "feat: [PAGE_NAME] - implement Flowbite layout standard"
   ```

---

## 📚 Referências Rápidas

| Documento | Para |
|-----------|------|
| [PAGE_LAYOUT_STANDARD.md](PAGE_LAYOUT_STANDARD.md) | Estrutura completa |
| [FLOWBITE_QUICK_REFERENCE.md](FLOWBITE_QUICK_REFERENCE.md) | Componentes |
| [FLOWBITE_IMPLEMENTATION.md](FLOWBITE_IMPLEMENTATION.md) | Detalhes técnicos |
| [DEV_CHECKLIST.md](DEV_CHECKLIST.md) | Este arquivo |

---

## 💡 Dicas Rápidas

### Copiar de Páginas Similares
```
Dashboard:      console/dashboard.html
Lista:          console/publication_list.html
Tabela:         console/policy_list.html
Courses:        courses/course/list.html
```

### Debugging
Se algo não funciona:

1. **Layout errado?**
   → Verifique `px-4 lg:px-8` em seções

2. **Dark mode quebrado?**
   → Adicione `dark:` classes

3. **Responsividade errada?**
   → Teste com `F12` device toggle

4. **Componente feio?**
   → Copie exatamente de exemplo

### Performance
- Não adicione CSS custom
- Use apenas classes Tailwind
- Evite JavaScript quando possível
- Reutilize componentes

---

## ❓ FAQ Rápido

**P: Posso usar `max-w-6xl`?**  
**R**: Não no wrapper principal. Só em cards/forms específicos.

**P: E `mx-auto`?**  
**R**: Não, remova. O padding lateral cria espaço.

**P: Qual padding usar?**  
**R**: Padrão `px-4 lg:px-8`. Ajuste conforme necessário.

**P: Como fazer full-width?**  
**R**: Use `w-full max-w-full` + `px-4 lg:px-8`.

**P: Responsividade garante funciona?**  
**R**: Teste em 3 tamanhos: mobile, tablet, desktop.

---

## 🎓 Template Copy & Paste

### Dashboard Completo
```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Dashboard' %}{% endblock %}

{% block content %}
<div class="w-full">
    <header class="mb-8 px-4 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
            {% trans 'Dashboard' %}
        </h1>
    </header>

    <div class="px-4 lg:px-8 mb-8">
        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div class="kpi">
                <div>
                    <p class="kpi-label">Total</p>
                    <p class="kpi-value">0</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Lista Completa
```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Items' %}{% endblock %}

{% block content %}
<div class="w-full">
    <header class="mb-8 flex items-center justify-between px-4 lg:px-8">
        <h1 class="text-3xl font-bold">{% trans 'Items' %}</h1>
        <a href="{% url 'create' %}" class="btn-primary">New</a>
    </header>

    <div class="px-4 lg:px-8 hidden md:block">
        <table class="table">
            <thead>
                <tr><th>Name</th></tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr><td>{{ item.name }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

---

**Tempo Total**: ~30 min  
**Dificuldade**: ⭐ Fácil  
**Sucesso Rate**: 95% ✅

Boa sorte! 🚀
