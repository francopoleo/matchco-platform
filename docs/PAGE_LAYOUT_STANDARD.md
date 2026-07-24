# Padrão de Layout de Página - Talk Console

**Versão**: 1.0  
**Data**: 2026-07-24  
**Status**: ✅ OBRIGATÓRIO para todas as páginas

---

## 📐 Layout Base Padrão

Toda página do Talk Console deve seguir este padrão de layout:

### Estrutura HTML

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Page Title' %}{% endblock %}

{% block content %}
<div class="w-full">
    <!-- Page content -->
</div>
{% endblock %}
```

### Características Obrigatórias

- ✅ **Full-width**: `w-full max-w-full` (100% da tela)
- ✅ **Padding responsivo**: `px-4 lg:px-8` (4px mobile, 8px desktop)
- ✅ **Padding vertical**: `py-8` (consistente)
- ✅ **Sem limite de largura**: ~~`max-w-6xl`~~ ❌ REMOVIDO
- ✅ **Sem centering**: ~~`mx-auto`~~ ❌ REMOVIDO

---

## 🎯 Padrão de Container Principal

### Padrão visual vigente do Talk Learning

As páginas de Learning (Home, Cursos, Feed e Wiki) devem seguir o mesmo padrão visual da página `/course-list/`:

```django
<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <div class="w-full max-w-full px-6 py-8">
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Page title</h1>
      <p class="mt-1 text-gray-600 dark:text-gray-400">Page description</p>
    </header>
  </div>
</div>
```

KPIs devem usar `rounded-xl border border-gray-200 bg-white p-5 shadow-sm`, com `mb-3 flex items-center justify-between`, label uppercase, ícone `h-12 w-12`, valor `text-2xl` e descrição `text-xs`. No dark mode, usar `dark:border-gray-700 dark:bg-gray-800`.

### ✅ CORRETO

```django
<div class="w-full">
    <!-- Conteúdo da página -->
</div>
```

**Ou com padding externo** (quando necessário):

```django
<div class="w-full px-4 py-8 lg:px-8">
    <!-- Conteúdo da página -->
</div>
```

### ❌ ERRADO

```django
<!-- Não use max-width fixo -->
<div class="mx-auto w-full max-w-6xl p-6">
    <!-- ❌ EVITAR: Limita largura -->
</div>

<!-- Não use padding uniforme -->
<div class="w-full p-6">
    <!-- ❌ PROBLEMA: Mesmo padding mobile/desktop -->
</div>

<!-- Não use mx-auto -->
<div class="mx-auto w-full">
    <!-- ❌ EVITAR: Centering desnecessário -->
</div>
```

---

## 📋 Estrutura Completa de Página

### Exemplo: Dashboard

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Dashboard' %}{% endblock %}

{% block content %}
<div class="w-full">
    <!-- SEÇÃO 1: Header -->
    <header class="mb-8 flex flex-wrap items-center justify-between gap-4 px-4 lg:px-8">
        <div>
            <p class="text-sm text-gray-600 dark:text-gray-400">Talk Console</p>
            <h1 class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                {% trans 'Dashboard' %}
            </h1>
        </div>
        <a href="{% url 'action' %}" class="btn-primary">
            <i class="fas fa-plus mr-2"></i>{% trans 'New Item' %}
        </a>
    </header>

    <!-- SEÇÃO 2: KPI Grid -->
    <div class="px-4 lg:px-8 mb-8">
        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div class="kpi">
                <!-- KPI content -->
            </div>
            <!-- More KPIs -->
        </div>
    </div>

    <!-- SEÇÃO 3: Tabela/Cards -->
    <div class="px-4 lg:px-8">
        <div class="rounded-lg border border-gray-200 bg-white shadow-sm">
            <table class="table">
                <!-- Table content -->
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🔧 Padrão por Tipo de Página

### Tipo 1: Página com Header + Conteúdo

```django
<div class="w-full">
    <!-- Header -->
    <header class="mb-8 px-4 lg:px-8">
        <h1 class="text-3xl font-bold">Title</h1>
    </header>

    <!-- Conteúdo -->
    <div class="px-4 lg:px-8">
        <!-- Content here -->
    </div>
</div>
```

### Tipo 2: Página com Filtro + Tabela

```django
<div class="w-full">
    <!-- Header -->
    <header class="mb-8 px-4 lg:px-8">
        <h1 class="text-3xl font-bold">Title</h1>
    </header>

    <!-- Filtro -->
    <form method="get" class="card mb-8 mx-4 lg:mx-8">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <!-- Filter fields -->
        </div>
    </form>

    <!-- Tabela -->
    <div class="px-4 lg:px-8">
        <div class="overflow-x-auto rounded-lg border border-gray-200">
            <table class="table">
                <!-- Table content -->
            </table>
        </div>
    </div>

    <!-- Mobile view (cards) -->
    <div class="space-y-3 px-4 lg:px-8 md:hidden">
        <!-- Mobile cards -->
    </div>
</div>
```

### Tipo 3: Página com Grid (Dashboard/KPIs)

```django
<div class="w-full">
    <!-- Header -->
    <header class="mb-8 px-4 lg:px-8">
        <h1 class="text-3xl font-bold">Title</h1>
    </header>

    <!-- KPI Grid -->
    <div class="mb-8 px-4 lg:px-8">
        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div class="kpi">
                <!-- KPI content -->
            </div>
        </div>
    </div>

    <!-- Gráficos/Conteúdo -->
    <div class="px-4 lg:px-8">
        <div class="grid gap-6 lg:grid-cols-2">
            <!-- Charts or cards -->
        </div>
    </div>
</div>
```

### Tipo 4: Página com Formulário

```django
<div class="w-full">
    <!-- Header -->
    <header class="mb-8 px-4 lg:px-8">
        <h1 class="text-3xl font-bold">Title</h1>
    </header>

    <!-- Form -->
    <div class="px-4 lg:px-8 pb-8">
        <div class="card max-w-2xl">
            <div class="card-header">
                <h2 class="card-title">Form Title</h2>
            </div>
            
            <form method="post" class="card-body space-y-4">
                {% csrf_token %}
                <!-- Form fields -->
            </form>
            
            <div class="card-footer">
                <button type="submit" class="btn-primary">Save</button>
                <button type="reset" class="btn-secondary">Clear</button>
            </div>
        </div>
    </div>
</div>
```

---

## 📱 Responsividade Garantida

### Classes Essenciais

```
px-4          → Padding horizontal mobile (16px)
lg:px-8       → Padding horizontal desktop (32px)
py-8          → Padding vertical (32px)
w-full        → Largura 100%
max-w-full    → Sem limite de largura
```

### Exemplo

```django
<!-- Mobile: 4px padding horizontal -->
<!-- Desktop (lg+): 8px padding horizontal -->
<div class="px-4 lg:px-8">
    Content scales nicely on all screen sizes
</div>
```

---

## 🎨 Spacing Padrão

| Seção | Classe | Espaço |
|-------|--------|---------|
| Header | `mb-8` | 32px abaixo |
| Container | `px-4 lg:px-8` | 16px mobile, 32px desktop |
| Vertical | `py-8` | 32px (top/bottom) |
| Between items | `gap-6` | 24px entre items |
| Card spacing | `mb-8` | 32px entre seções |

---

## ✅ Checklist para Novas Páginas

Quando criar ou alterar uma página, verifique:

- [ ] **Layout principal**: `<div class="w-full">`
- [ ] **Sem max-width fixo**: Removeu `max-w-6xl`, `max-w-4xl`, etc?
- [ ] **Sem mx-auto**: Não usou centering?
- [ ] **Padding responsivo**: `px-4 lg:px-8` ou dentro de containers
- [ ] **Header com padding**: `mb-8 px-4 lg:px-8`
- [ ] **Conteúdo com padding**: Cada seção tem `px-4 lg:px-8`
- [ ] **Dark mode**: Todos elementos têm `dark:` variantes?
- [ ] **Responsividade mobile**: Teste em smartphone (375px width)
- [ ] **Responsividade tablet**: Teste em tablet (768px width)
- [ ] **Responsividade desktop**: Teste em desktop (1024px+ width)
- [ ] **Full-width**: Conteúdo usa 100% da tela?

---

## 🔄 Migração de Páginas Antigas

### Antes (COM restrição de largura)

```django
<div class="mx-auto w-full max-w-6xl p-6">
    <h1>Title</h1>
    <div>Content</div>
</div>
```

### Depois (Full-width padrão)

```django
<div class="w-full">
    <!-- Header -->
    <header class="mb-8 px-4 lg:px-8">
        <h1 class="text-3xl font-bold">Title</h1>
    </header>

    <!-- Content -->
    <div class="px-4 lg:px-8">
        Content
    </div>
</div>
```

### Steps para Migrar
1. Remove `mx-auto` e `max-w-6xl`
2. Muda `p-6` para `px-4 lg:px-8` ou seções específicas
3. Adiciona `mb-8` entre seções principais
4. Testa responsividade (mobile/tablet/desktop)

**Tempo**: ~5 min por página

---

## 📚 Integração com Componentes Flowbite

### Cards

```django
<!-- COM padding correto -->
<div class="px-4 lg:px-8 mb-8">
    <div class="card">
        <!-- Conteúdo -->
    </div>
</div>
```

### Tabelas

```django
<!-- COM padding correto -->
<div class="px-4 lg:px-8 mb-8">
    <div class="overflow-x-auto rounded-lg border">
        <table class="table">
            <!-- Conteúdo -->
        </table>
    </div>
</div>
```

### KPI Grid

```django
<!-- COM padding correto -->
<div class="px-4 lg:px-8 mb-8">
    <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div class="kpi"><!-- KPI 1 --></div>
        <div class="kpi"><!-- KPI 2 --></div>
        <div class="kpi"><!-- KPI 3 --></div>
        <div class="kpi"><!-- KPI 4 --></div>
    </div>
</div>
```

---

## 🌙 Dark Mode Automático

Todas as páginas suportam dark mode automaticamente via Tailwind `dark:` classes.

```django
<!-- Automáticamente terá dark mode -->
<div class="bg-white dark:bg-gray-800">
    <p class="text-gray-900 dark:text-white">Text</p>
</div>
```

---

## 📊 Páginas Já Convertidas

| Página | Status | Último Update |
|--------|--------|--------------|
| Console Dashboard | ✅ | 2026-07-24 |
| Publication List | ✅ | 2026-07-24 |
| Policy List | ✅ | 2026-07-24 |
| Course List | ✅ | 2026-07-24 |

---

## 📝 Páginas Pendentes

Páginas que precisam ser migradas para este padrão:

- [ ] User Management
- [ ] Course Management
- [ ] Analytics/Reports
- [ ] Settings
- [ ] Profile
- [ ] Other admin pages

---

## 🔗 Referências Relacionadas

- [FLOWBITE_QUICK_REFERENCE.md](FLOWBITE_QUICK_REFERENCE.md) - Exemplos de componentes
- [FLOWBITE_IMPLEMENTATION.md](FLOWBITE_IMPLEMENTATION.md) - Componentes detalhados
- [README.md](README.md) - Índice geral

---

## 💡 Dicas & Boas Práticas

### 1. Sempre use Sections Lógicas

```django
<div class="w-full">
    <!-- Header Section -->
    <section class="mb-8 px-4 lg:px-8">
        ...
    </section>

    <!-- Filter Section -->
    <section class="mb-8 px-4 lg:px-8">
        ...
    </section>

    <!-- Content Section -->
    <section class="px-4 lg:px-8">
        ...
    </section>
</div>
```

### 2. Grouping com Containers

```django
<!-- Bom: Agrupa conteúdo relacionado -->
<div class="px-4 lg:px-8 mb-8">
    <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Grid items -->
    </div>
</div>
```

### 3. Padding Consistente

```django
<!-- Todos os containers no mesmo nível devem ter mesmo padding -->
<header class="mb-8 px-4 lg:px-8">...</header>
<section class="mb-8 px-4 lg:px-8">...</section>
<section class="px-4 lg:px-8">...</section>
```

### 4. Espaçamento entre Seções

```django
<!-- Use mb-8 para separar seções principais -->
<div class="mb-8">Seção 1</div>
<div class="mb-8">Seção 2</div>
<div>Seção 3 (última, sem mb)</div>
```

---

## 🚀 Performance

- ✅ **No CSS overhead**: Usa apenas classes Tailwind
- ✅ **JIT compilation**: Apenas classes usadas são geradas
- ✅ **Mobile-first**: Otimizado para mobile por padrão
- ✅ **Fast rendering**: Sem complexidade de layout

---

## ❓ FAQ

### P: Por que remover `max-w-6xl`?
**R**: Para permitir **full-width** em telas modernas (ultralarga). O conteúdo ainda tem padding lateral, então não fica "esticado".

### P: Posso usar `max-w-*` em cards específicos?
**R**: Sim! Use `max-w-2xl` apenas em **cards de formulário** ou **conteúdo específico**, não no layout principal.

```django
<!-- OK para formulário -->
<div class="max-w-2xl mx-auto">
    <form>...</form>
</div>

<!-- ERRADO para layout principal -->
<div class="max-w-6xl mx-auto">
    <!-- Todo conteúdo -->
</div>
```

### P: E se o conteúdo ficar muito largo em 4K?
**R**: O padding lateral (`px-4 lg:px-8`) cria espaço. Se necessário, use `max-w-7xl` APENAS na grid ou container específico, não no wrapper principal.

### P: Qual padding usar?
**R**: Padrão é `px-4 lg:px-8`. Se precisar diferentes, ajuste conforme necessário, mas mantenha consistência.

---

## 📞 Suporte

**Dúvida sobre layout?**
- Consulte este documento
- Veja exemplos em páginas já convertidas (console/dashboard.html)
- Copie padrão do tipo de página mais similar

---

**Status Final**: ✅ PADRÃO OBRIGATÓRIO  
**Versão**: 1.0  
**Data**: 2026-07-24  

---

## Resumo Executivo

| Item | Regra |
|------|-------|
| **Container Principal** | `<div class="w-full">` |
| **Max-width** | ~~`max-w-6xl`~~ → `max-w-full` |
| **Centering** | ~~`mx-auto`~~ → Sem centering |
| **Padding H** | `px-4 lg:px-8` |
| **Padding V** | `py-8` ou sections com `mb-8` |
| **Dark Mode** | Automático com `dark:` classes |
| **Responsividade** | Mobile-first, 5 breakpoints |

✨ **Resultado**: Páginas modernas, full-width, responsivas e documentadas!
