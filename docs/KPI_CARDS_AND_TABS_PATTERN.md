# KPI Cards & Tabs Pattern - Guia Padronizado

Padrão correto para KPI cards e abas (tabs) nas páginas do console.

## 🎯 Padrão KPI Card (Correto)

### Estrutura HTML

```html
<div class="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
    <!-- Header: Label + Ícone Colorido -->
    <div class="mb-3 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">
            LABEL
        </span>
        <!-- Ícone com cor (h-12 w-12, não maior!) -->
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-{COLOR}-100 text-{COLOR}-600 transition group-hover:scale-110 dark:bg-{COLOR}-900/40 dark:text-{COLOR}-300">
            <svg class="h-6 w-6"><!-- SVG --></svg>
        </span>
    </div>
    
    <!-- Valor: Cinza escuro, text-2xl (não text-3xl!) -->
    <p class="text-2xl font-bold text-gray-900 dark:text-white">123</p>
    
    <!-- Descrição: Texto pequeno cinza -->
    <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">Descrição</p>
</div>
```

### Características Importantes

| Aspecto | Correto | Errado | Por quê |
|---------|---------|--------|--------|
| Fundo card | `bg-white` | `bg-blue-50/50` | Contraste com valores |
| Tamanho número | `text-2xl` | `text-3xl` | Proporções visuais |
| Cor número | `text-gray-900` | `text-blue-700` | Melhor legibilidade |
| Ícone | `h-12 w-12` | `h-14 w-14` | Não dominar o card |
| Ícone fundo | `bg-{COLOR}-100` | `bg-gradient-to-br` | Simples e limpo |
| Label | `text-xs uppercase` | `text-sm` | Hierarquia visual |
| Descrição | `text-xs gray` | `text-sm gray` | Complementar |
| Borda | `border-gray-200` | `border-{COLOR}-200` | Não competir com ícone |

### Cores de Ícone (Opções)

```html
<!-- Blue (Padrão) -->
<span class="bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300">

<!-- Violet (Secondary) -->
<span class="bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-300">

<!-- Emerald (Success) -->
<span class="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-300">

<!-- Amber (Warning) -->
<span class="bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-300">

<!-- Green (OK) -->
<span class="bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-300">

<!-- Purple (Premium) -->
<span class="bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-300">
```

### Grid Layout

```html
<!-- 4 Colunas (Padrão) -->
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

<!-- 3 Colunas -->
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">

<!-- 2 Colunas -->
<div class="grid gap-4 sm:grid-cols-2">
```

### Exemplo Completo (Copy & Paste)

```html
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <!-- Card 1: Azul -->
    <div class="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-3 flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">Total</span>
            <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600 transition group-hover:scale-110 dark:bg-blue-900/40 dark:text-blue-300">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
            </span>
        </div>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">1,234</p>
        <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">Total items</p>
    </div>

    <!-- Card 2: Violet -->
    <div class="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-3 flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">Active</span>
            <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-violet-100 text-violet-600 transition group-hover:scale-110 dark:bg-violet-900/40 dark:text-violet-300">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m7 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </span>
        </div>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">432</p>
        <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">Active now</p>
    </div>

    <!-- Card 3: Emerald -->
    <div class="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-3 flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">Success</span>
            <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 transition group-hover:scale-110 dark:bg-emerald-900/40 dark:text-emerald-300">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7Z"/>
                </svg>
            </span>
        </div>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">98%</p>
        <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">Completion</p>
    </div>

    <!-- Card 4: Amber -->
    <div class="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-3 flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">Pending</span>
            <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-600 transition group-hover:scale-110 dark:bg-amber-900/40 dark:text-amber-300">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                </svg>
            </span>
        </div>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">23</p>
        <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">Awaiting action</p>
    </div>
</div>
```

---

## 📑 Padrão Tabs/Abas (Correto)

### Estrutura HTML

```html
<div class="flex gap-2" role="tablist" aria-label="View options">
    <!-- Tab Ativo (Cards) -->
    <button id="cards-tab" type="button" 
            class="view-tab inline-flex items-center gap-2 rounded-lg border-2 border-blue-600 bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 dark:hover:bg-blue-800" 
            data-view="cards" aria-selected="true">
        <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 6h6M9 12h6m-6 6h6M3 6a3 3 0 013-3h12a3 3 0 013 3v12a3 3 0 01-3 3H6a3 3 0 01-3-3V6z"/>
        </svg>
        Cards
    </button>

    <!-- Tab Inativo (List) -->
    <button id="list-tab" type="button" 
            class="view-tab inline-flex items-center gap-2 rounded-lg border-2 border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700" 
            data-view="list" aria-selected="false">
        <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
        List
    </button>
</div>
```

### JavaScript (Importante!)

```javascript
function setView(view) {
    const isCards = view === 'cards';
    cardPanel.classList.toggle('hidden', !isCards);
    tablePanel.classList.toggle('hidden', isCards);
    
    tabs.forEach(tab => {
        const active = tab.dataset.view === view;
        tab.setAttribute('aria-selected', active);
        
        if (active) {
            // Tab ativo: azul
            tab.classList.add('border-blue-600', 'bg-blue-600', 'text-white');
            tab.classList.remove('border-gray-200', 'bg-white', 'text-gray-700', 
                                 'dark:border-gray-700', 'dark:bg-gray-800', 'dark:text-gray-300');
        } else {
            // Tab inativo: branco
            tab.classList.remove('border-blue-600', 'bg-blue-600', 'text-white');
            tab.classList.add('border-gray-200', 'bg-white', 'text-gray-700', 
                             'dark:border-gray-700', 'dark:bg-gray-800', 'dark:text-gray-300');
        }
    });
    
    localStorage.setItem('view-preference', view);
}

// Inicializar
const tabs = Array.from(document.querySelectorAll('.view-tab'));
tabs.forEach(tab => tab.addEventListener('click', () => setView(tab.dataset.view)));
setView(localStorage.getItem('view-preference') || 'cards');
```

### Características Importantes

| Aspecto | Correto | Errado | Por quê |
|---------|---------|--------|--------|
| Ativo | `bg-blue-600 border-blue-600` | `bg-brand` | Classes Tailwind reais |
| Inativo | `bg-white border-gray-200` | `bg-gray-100` | Mais contraste |
| Ícone | Sempre presente | Opcional | Hierarquia visual |
| Transição | `transition hover:` | Sem hover | Feedback ao usuário |
| Dark mode | Classes `dark:` | Nenhuma | Suporte completo |
| Gap | `gap-2` | Sem espaço | Separação visual |
| JS Class Toggle | Adicionar/remover corretos | Usar classes antigas | Funcionalidade |

---

## ❌ Erros Comuns

### ❌ Erro 1: KPI com fundo colorido
```html
<!-- ERRADO -->
<div class="bg-blue-50/50">
    <p class="text-blue-700">Valor</p>  <!-- Muito pouco contraste! -->
</div>

<!-- CORRETO -->
<div class="bg-white dark:bg-gray-800">
    <p class="text-gray-900 dark:text-white">Valor</p>  <!-- Alto contraste -->
</div>
```

### ❌ Erro 2: KPI muito grande
```html
<!-- ERRADO -->
<p class="text-3xl font-bold">123</p>  <!-- Domina o card -->

<!-- CORRETO -->
<p class="text-2xl font-bold">123</p>  <!-- Proporcional -->
```

### ❌ Erro 3: Ícone muito grande
```html
<!-- ERRADO -->
<span class="h-14 w-14">  <!-- h-14 = 56px, enorme! -->

<!-- CORRETO -->
<span class="h-12 w-12">  <!-- h-12 = 48px, balanceado -->
```

### ❌ Erro 4: Tabs com classes antigas
```javascript
// ERRADO
tab.classList.toggle('bg-brand', active);      // bg-brand não existe!
tab.classList.toggle('text-white', active);   // Sem remover outras classes

// CORRETO
if (active) {
    tab.classList.add('border-blue-600', 'bg-blue-600', 'text-white');
    tab.classList.remove('border-gray-200', 'bg-white', 'text-gray-700', ...);
}
```

### ❌ Erro 5: Tab sem dark mode
```html
<!-- ERRADO -->
<button class="bg-white border-gray-200">  <!-- Falta dark mode -->

<!-- CORRETO -->
<button class="bg-white border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
```

---

## ✅ Checklist para Novas Páginas

### KPI Cards
- [ ] Fundo branco (`bg-white`)
- [ ] Borda cinza (`border-gray-200`)
- [ ] Número texto-2xl (`text-2xl`) e cinza escuro
- [ ] Ícone h-12 w-12 (não maior!)
- [ ] Ícone com cor (blue, violet, emerald, amber, etc)
- [ ] Label `text-xs uppercase`
- [ ] Descrição `text-xs gray`
- [ ] Hover effect (`hover:shadow-md`)
- [ ] Dark mode classes (`dark:`)
- [ ] Grid responsivo (sm/lg)

### Tabs
- [ ] 2+ botões com ícones
- [ ] Border-2 para definição
- [ ] Ativo: azul (`bg-blue-600 border-blue-600`)
- [ ] Inativo: branco (`bg-white border-gray-200`)
- [ ] Hover effects
- [ ] Dark mode classes
- [ ] JavaScript correto para toggle
- [ ] localStorage para persistência
- [ ] aria-selected para acessibilidade

---

## 🎯 Resumo Visual

### KPI Card
```
┌─────────────────────┐
│ LABEL        [ICON] │  ← Ícone colorido, 12x12
│                     │
│ 1,234               │  ← text-2xl, cinza escuro
│ Description         │  ← text-xs, cinza
└─────────────────────┘
Fundo branco, borda cinza, sombra sutil
```

### Tabs
```
[■ Cards] [□ List]
 └─ Azul  └─ Branco com border gray
    (ativo) (inativo)
```

---

## 📚 Referências

- [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) - Cores completas
- [CONSOLE_QUICK_REFERENCE.md](CONSOLE_QUICK_REFERENCE.md) - Exemplos
- [course/list.html](/talk/courses/templates/courses/course/list.html) - Implementação real

---

**Versão**: 1.0  
**Data**: 2026-07-24  
**Padrão**: Oficial Talk Learning Console

Use este documento como base para TODAS as novas páginas do console!
