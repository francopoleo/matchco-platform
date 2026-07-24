# Console Talk - Quick Reference Guide

Guia rápido para usar o novo console padronizado.

## 🎯 Estrutura Base

Todas as páginas do console devem estender este template:

```html
{% extends 'console/console_base.html' %}
{% load i18n %}

{% block title %}Seu Título{% endblock %}

{% block content %}
    <!-- Seu conteúdo aqui -->
{% endblock %}

{% block extra_js %}
    <!-- Scripts adicionais se necessário -->
{% endblock %}
```

## 🎨 8 Cores Principais

Use estas 8 cores para KPI Cards e componentes:

### 1️⃣ Azul (Padrão)
```html
border-blue-100 bg-blue-50/50 text-blue-700
dark:border-blue-900/40 dark:bg-blue-900/20 dark:text-blue-300
```
**Uso**: Total, Principais, Default

### 2️⃣ Violeta
```html
border-violet-100 bg-violet-50/50 text-violet-700
dark:border-violet-900/40 dark:bg-violet-900/20 dark:text-violet-300
```
**Uso**: Available, Secondary

### 3️⃣ Esmeralda
```html
border-emerald-100 bg-emerald-50/50 text-emerald-700
dark:border-emerald-900/40 dark:bg-emerald-900/20 dark:text-emerald-300
```
**Uso**: Progress, Sucesso

### 4️⃣ Âmbar
```html
border-amber-100 bg-amber-50/50 text-amber-700
dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-300
```
**Uso**: Categories, Avisos

### 5️⃣ Verde
```html
border-green-100 bg-green-50/50 text-green-700
dark:border-green-900/40 dark:bg-green-900/20 dark:text-green-300
```
**Uso**: Saúde, OK, Completo

### 6️⃣ Roxo
```html
border-purple-100 bg-purple-50/50 text-purple-700
dark:border-purple-900/40 dark:bg-purple-900/20 dark:text-purple-300
```
**Uso**: Premium, Especial

### 7️⃣ Rosa
```html
border-pink-100 bg-pink-50/50 text-pink-700
dark:border-pink-900/40 dark:bg-pink-900/20 dark:text-pink-300
```
**Uso**: Alerta, Importante

### 8️⃣ Índigo
```html
border-indigo-100 bg-indigo-50/50 text-indigo-700
dark:border-indigo-900/40 dark:bg-indigo-900/20 dark:text-indigo-300
```
**Uso**: Info, Neutro

## 📦 Componentes Prontos

### KPI Card (Métrica)
```html
<div class="group rounded-lg border border-{COLOR}-100 bg-{COLOR}-50/50 p-5 
            transition hover:border-{COLOR}-300 hover:shadow-md 
            dark:border-{COLOR}-900/40 dark:bg-{COLOR}-900/20">
    <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider 
                     text-{COLOR}-700 dark:text-{COLOR}-300">
            LABEL
        </span>
        <span class="flex h-12 w-12 shrink-0 items-center justify-center 
                     rounded-xl bg-{COLOR}-100 text-{COLOR}-600 
                     transition group-hover:scale-110 
                     dark:bg-{COLOR}-900/40 dark:text-{COLOR}-300">
            <svg class="h-6 w-6"><!-- ÍCONE --></svg>
        </span>
    </div>
    <p class="text-2xl font-bold text-gray-900 dark:text-white">123</p>
    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">Descrição</p>
</div>
```

### KPI Card Grid (4 Colunas)
```html
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <!-- 4x KPI Cards aqui -->
</div>
```

### KPI Card Grid (3 Colunas)
```html
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <!-- 3x KPI Cards aqui -->
</div>
```

## 🔤 Tipografia

### Títulos
```html
<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Título H1</h1>
<h2 class="text-2xl font-bold text-gray-900 dark:text-white">Título H2</h2>
<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Título H3</h3>
```

### Corpo de Texto
```html
<p class="text-gray-600 dark:text-gray-400">Texto normal</p>
<p class="text-sm text-gray-600 dark:text-gray-400">Texto pequeno</p>
<p class="text-xs text-gray-500 dark:text-gray-500">Texto muito pequeno</p>
```

### Labels
```html
<span class="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">
    LABEL
</span>
```

## 📐 Espaçamento

### Padding
- `p-3` - Small (12px)
- `p-4` - Default (16px)
- `p-5` - Medium (20px)
- `p-6` - Large (24px)
- `p-8` - XLarge (32px)

### Margin
- `mb-2` - Margin bottom small (8px)
- `mb-4` - Margin bottom default (16px)
- `mb-6` - Margin bottom large (24px)
- `mb-8` - Margin bottom XLarge (32px)

### Gap (entre grid items)
```html
<div class="grid gap-4"><!-- 16px entre items --></div>
<div class="grid gap-6"><!-- 24px entre items --></div>
<div class="grid gap-8"><!-- 32px entre items --></div>
```

## 📱 Responsividade

### Grid 2 colunas em mobile, 4 em desktop
```html
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
```

### Grid 1 coluna em mobile, 3 em tablet, 4 em desktop
```html
<div class="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
```

### Mostrar/Esconder por breakpoint
```html
<div class="hidden lg:block">Visível apenas em lg+</div>
<div class="lg:hidden">Escondido em lg+</div>
```

### Padding responsivo
```html
<div class="p-4 lg:p-8"><!-- p-4 mobile, p-8 desktop --></div>
```

## 🌓 Dark Mode

Toda cor deve ter variante dark:

```html
<!-- ❌ ERRADO -->
<div class="bg-blue-50 text-blue-700">

<!-- ✅ CORRETO -->
<div class="bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
```

## 🎬 Efeitos Hover

### Scale (Zoom)
```html
<span class="transition group-hover:scale-110">Ícone que cresce</span>
<button class="hover:scale-105 transition">Botão que cresce</button>
```

### Shadow (Sombra)
```html
<div class="transition hover:shadow-md">Card com shadow</div>
```

### Cor
```html
<button class="text-blue-600 hover:text-blue-700 transition">Link</button>
```

### Fundo
```html
<div class="bg-gray-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition">
```

## 🔗 Links Úteis

### Documentação Completa
- 📖 [Design System](/docs/DESIGN_SYSTEM.md)
- 📝 [Mudanças Implementadas](/docs/CONSOLE_STANDARDIZATION_CHANGES.md)

### Tailwind Docs
- [Cores](https://tailwindcss.com/docs/customizing-colors)
- [Spacing](https://tailwindcss.com/docs/customizing-spacing)
- [Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [Dark Mode](https://tailwindcss.com/docs/dark-mode)

## 📋 Checklist para Novas Páginas

- [ ] Estende `console/console_base.html`
- [ ] Usa apenas as 8 cores principais
- [ ] Todas as cores têm variante `dark:`
- [ ] Responsive com sm/lg breakpoints
- [ ] Ícones SVG em containers coloridos
- [ ] Testado em light e dark mode
- [ ] Testado em mobile

## 🚀 Exemplo Completo

```html
{% extends 'console/console_base.html' %}
{% load i18n %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="mx-auto max-w-6xl">
    <h1 class="mb-8 text-3xl font-bold text-gray-900 dark:text-white">
        Dashboard
    </h1>

    <!-- KPI Cards -->
    <div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Blue -->
        <div class="group rounded-lg border border-blue-100 bg-blue-50/50 p-5 
                    transition hover:border-blue-300 hover:shadow-md 
                    dark:border-blue-900/40 dark:bg-blue-900/20">
            <div class="mb-2 flex items-center justify-between">
                <span class="text-xs font-semibold uppercase 
                            text-blue-700 dark:text-blue-300">
                    Total
                </span>
                <span class="flex h-12 w-12 items-center justify-center 
                            rounded-xl bg-blue-100 text-blue-600 
                            group-hover:scale-110 dark:bg-blue-900/40 
                            dark:text-blue-300">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor">
                        <!-- Ícone aqui -->
                    </svg>
                </span>
            </div>
            <p class="text-2xl font-bold">1,234</p>
            <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Total items
            </p>
        </div>

        <!-- Mais 3 cards aqui... -->
    </div>

    <!-- Conteúdo -->
    <section class="rounded-lg border border-gray-200 bg-white p-6 
                    dark:border-gray-700 dark:bg-gray-800">
        <h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
            Seção
        </h2>
        <p class="text-gray-600 dark:text-gray-400">
            Seu conteúdo aqui
        </p>
    </section>
</div>
{% endblock %}
```

---

**Versão**: 1.0
**Última atualização**: 2026-07-24
