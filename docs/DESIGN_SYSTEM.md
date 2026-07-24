# Talk Learning - Design System & Console Standardization

Documentação do padrão de design e estilo do console Talk Learning, padronizado com o Console do App.

## 📋 Visão Geral

O Talk Learning adota um design system moderno e acessível baseado em:
- **Tailwind CSS** para estilização utilitária
- **Flowbite** para componentes pré-construídos
- **Ícones SVG coloridos** para hierarquia visual
- **Dark mode** nativo com localStorage persistence
- **Responsive design** mobile-first

## 🎨 Paleta de Cores

### Cores Primárias
- **Azul**: `blue-600` (texto) com fundo `blue-50` / `blue-100`
- **Violeta**: `violet-600` com fundo `violet-50` / `violet-100`
- **Esmeralda**: `emerald-600` com fundo `emerald-50` / `emerald-100`
- **Âmbar**: `amber-600` com fundo `amber-50` / `amber-100`
- **Índigo**: `indigo-600` com fundo `indigo-50` / `indigo-100`
- **Verde**: `green-600` com fundo `green-50` / `green-100`
- **Roxo**: `purple-600` com fundo `purple-50` / `purple-100`
- **Rosa**: `pink-600` com fundo `pink-50` / `pink-100`

### Dark Mode
Para dark mode, todas as cores seguem o padrão:
- Fundo: `*-900/20` ou `*-900/40`
- Texto: `*-300` ou `*-400`

**Exemplo:**
```html
<div class="bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300">
```

## 🧱 Componentes

### 1. Console Base Template

**Arquivo**: `console/templates/console/console_base.html`

Estrutura base para todas as páginas do console:

```html
{% extends 'console/console_base.html' %}

{% block title %}Seu Título{% endblock %}

{% block content %}
  <!-- Seu conteúdo aqui -->
{% endblock %}
```

### 2. Navbar Console

**Arquivo**: `console/templates/console/navbar_console.html`

Incluso automaticamente em `console_base.html`. Inclui:
- Toggle do sidebar
- Dark mode toggle
- Menu do usuário (avatar, profile, logout)
- Logo "Talk Console"

### 3. Sidebar Console

**Arquivo**: `console/templates/console/sidebar_console.html`

Menu lateral responsivo com:
- Links de navegação com ícones
- Fechar automático em mobile ao clicar em link
- Overlay escurecido em mobile
- Transições suaves

### 4. KPI Cards (Cards de Métrica)

Padrão para exibir estatísticas com ícone colorido:

```html
<div class="group rounded-lg border border-blue-100 bg-blue-50/50 p-5 
            transition hover:border-blue-300 hover:shadow-md 
            dark:border-blue-900/40 dark:bg-blue-900/20">
    <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider 
                     text-blue-700 dark:text-blue-300">
            Label
        </span>
        <span class="flex h-12 w-12 shrink-0 items-center justify-center 
                     rounded-xl bg-blue-100 text-blue-600 
                     transition group-hover:scale-110 
                     dark:bg-blue-900/40 dark:text-blue-300">
            <!-- SVG Ícone aqui -->
        </span>
    </div>
    <p class="text-2xl font-bold text-gray-900 dark:text-white">123</p>
    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">Descrição</p>
</div>
```

## 📐 Layout & Spacing

### Containers
- **Max Width**: `max-w-6xl` para conteúdo principal
- **Padding Desktop**: `lg:p-8`
- **Padding Mobile**: `p-4`

### Grid
- **2 Colunas**: `sm:grid-cols-2`
- **3 Colunas**: `lg:grid-cols-3`
- **4 Colunas**: `lg:grid-cols-4`
- **Gap**: `gap-4` entre itens

## 🎯 Ícones SVG

### Padrão de Ícone com Cor

Estrutura recomendada para ícones dentro de containers coloridos:

```html
<span class="flex h-12 w-12 shrink-0 items-center justify-center 
             rounded-xl bg-{color}-100 text-{color}-600 
             dark:bg-{color}-900/40 dark:text-{color}-300">
    <svg class="h-6 w-6" fill="none" stroke="currentColor" 
         stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" 
              d="M..."/>
    </svg>
</span>
```

### Comportamentos com Hover
- Scale 110%: `group-hover:scale-110`
- Transição suave: `transition`
- Shadow: `hover:shadow-md`

## 📱 Responsive

### Breakpoints Tailwind
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### Sidebar
- **Mobile**: Drawer com overlay (translate-x-full)
- **Desktop (lg+)**: Sidebar fixo ao lado

### Exemplo:
```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
```

## 🌓 Dark Mode

### Implementação
1. Detecta preferência do sistema: `(prefers-color-scheme: dark)`
2. Persiste escolha em localStorage: `color-theme`
3. Aplica classe `dark` ao `<html>`

### Uso em Componentes
```html
<div class="bg-gray-50 dark:bg-gray-900 
            text-gray-900 dark:text-white">
```

### Toggle Dark Mode
Implementado em `navbar_console.html` com ícones sun/moon.

## 🎬 Transições & Animações

### Padrão de Hover
```html
<button class="transition hover:bg-gray-100 dark:hover:bg-gray-700">
```

### Transições Nomeadas
```html
<!-- Slide in sidebar -->
<aside class="transition-transform">

<!-- Scale icon on hover -->
<span class="transition group-hover:scale-110">

<!-- Fade transitions -->
<div class="transition duration-300">
```

## 🚀 Páginas do Console

### Course List (`courses/course/list.html`)

Atualizada com novo design:
- ✅ KPI Cards com ícones coloridos (Azul, Violeta, Esmeralda, Âmbar)
- ✅ Cards de curso melhorados
- ✅ Filtros e busca padronizados
- ✅ Dark mode completo

## 📦 Arquivos & Estrutura

```
talk/console/templates/console/
├── console_base.html           # Template base (extends ui/base.html)
├── navbar_console.html         # Navbar com logo, theme toggle, user menu
├── sidebar_console.html        # Sidebar com navegação e overlay mobile
└── [outras páginas específicas]

courses/templates/courses/course/
└── list.html                   # Página de cursos (com novo design)
```

## 🔧 Customização

### Mudar Cor de um Card
Substitua todas as instâncias de `blue` pelo nome da cor:

```html
<!-- De: -->
<div class="border-blue-100 bg-blue-50/50 dark:border-blue-900/40 dark:bg-blue-900/20">
    <span class="text-blue-700 dark:text-blue-300">
    <span class="bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300">

<!-- Para: -->
<div class="border-green-100 bg-green-50/50 dark:border-green-900/40 dark:bg-green-900/20">
    <span class="text-green-700 dark:text-green-300">
    <span class="bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-300">
```

### Adicionar Nova Página ao Console

1. Crie o template: `console/templates/console/minha_pagina.html`
2. Estenda `console_base.html`:
   ```html
   {% extends 'console/console_base.html' %}
   {% block content %}...{% endblock %}
   ```
3. Navbar e sidebar aparecem automaticamente
4. Faça o link na `sidebar_console.html`

## 📖 Referências

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Flowbite Components](https://flowbite.com/docs/components/)
- [Dark Mode Guide](https://tailwindcss.com/docs/dark-mode)
- [Responsive Design](https://tailwindcss.com/docs/responsive-design)

## ✅ Checklist de Conformidade

Ao criar nova página no console, verifique:

- [ ] Estende `console/console_base.html`
- [ ] Usa cores da paleta (não cores genéricas)
- [ ] Ícones SVG em containers coloridos (h-12 w-12, rounded-xl)
- [ ] Dark mode classes para fundo e texto
- [ ] Responsivo com grid (sm/lg breakpoints)
- [ ] Link adicionado ao sidebar
- [ ] Testado em light e dark mode
- [ ] Testado em mobile (< 640px)

---

**Última atualização**: 2026-07-24
**Versão**: 1.0
**Responsável**: Design System Talk Learning