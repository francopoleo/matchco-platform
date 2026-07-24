# Console Talk - Integration Checklist

Checklist para padronizar outras páginas do console.

---

## 📋 Preparação

### Pré-requisitos
- [ ] Leu `docs/DESIGN_SYSTEM.md`
- [ ] Leu `docs/CONSOLE_QUICK_REFERENCE.md`
- [ ] Viu exemplo em `courses/templates/courses/course/list.html`
- [ ] Entende estrutura de cores (8 cores + dark mode)

---

## 🔄 Conversão de Página

### Step 1: Template Base
- [ ] Mude de `{% extends 'ui/base.html' %}` para `{% extends 'console/console_base.html' %}`
- [ ] Remova navbar/sidebar manual (agora automático)
- [ ] Teste se navbar e sidebar aparecem
- [ ] Teste dark mode toggle

### Step 2: Cores
- [ ] Identifique todos os elementos coloridos
- [ ] Substitua cores genéricas por paleta (blue, violet, emerald, amber, etc)
- [ ] Adicione classes `dark:` para cada `bg-*` e `text-*`
- [ ] Teste em light mode
- [ ] Teste em dark mode

### Step 3: Componentes
- [ ] Converta KPI cards para novo padrão (veja exemplo)
- [ ] Atualize buttons para seguir padrão
- [ ] Atualize cards/boxes para bordas sutis
- [ ] Adicione efeitos hover onde apropriado

### Step 4: Responsividade
- [ ] Verifique grids (`sm:grid-cols-2`, `lg:grid-cols-4`)
- [ ] Teste em mobile (< 640px)
- [ ] Teste em tablet (640-1024px)
- [ ] Teste em desktop (> 1024px)
- [ ] Verifique padding responsivo (`p-4 lg:p-8`)

### Step 5: Sidebar
- [ ] Adicione link do novo página ao sidebar
- [ ] Use ícone SVG apropriado
- [ ] Teste navegação funciona

### Step 6: Testes
- [ ] Valide HTML (sem erros)
- [ ] Verifique todas as cores
- [ ] Dark mode toggle funciona
- [ ] Layout responsivo OK
- [ ] Todos os links funcionam
- [ ] Não há console errors

### Step 7: Documentação
- [ ] Atualize CLAUDE.md se necessário
- [ ] Documente qualquer customização
- [ ] Adicione exemplos de código

---

## 🎨 Checklist de Design

### Cores
```html
<!-- Template para cada cor -->

<!-- Cor: Blue -->
<div class="border-blue-100 bg-blue-50/50 text-blue-700
            dark:border-blue-900/40 dark:bg-blue-900/20 dark:text-blue-300">
</div>

<!-- Cor: Violet -->
<div class="border-violet-100 bg-violet-50/50 text-violet-700
            dark:border-violet-900/40 dark:bg-violet-900/20 dark:text-violet-300">
</div>

<!-- Cor: Emerald -->
<div class="border-emerald-100 bg-emerald-50/50 text-emerald-700
            dark:border-emerald-900/40 dark:bg-emerald-900/20 dark:text-emerald-300">
</div>

<!-- Cor: Amber -->
<div class="border-amber-100 bg-amber-50/50 text-amber-700
            dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-300">
</div>

<!-- Cor: Green -->
<div class="border-green-100 bg-green-50/50 text-green-700
            dark:border-green-900/40 dark:bg-green-900/20 dark:text-green-300">
</div>

<!-- Cor: Purple -->
<div class="border-purple-100 bg-purple-50/50 text-purple-700
            dark:border-purple-900/40 dark:bg-purple-900/20 dark:text-purple-300">
</div>

<!-- Cor: Pink -->
<div class="border-pink-100 bg-pink-50/50 text-pink-700
            dark:border-pink-900/40 dark:bg-pink-900/20 dark:text-pink-300">
</div>

<!-- Cor: Indigo -->
<div class="border-indigo-100 bg-indigo-50/50 text-indigo-700
            dark:border-indigo-900/40 dark:bg-indigo-900/20 dark:text-indigo-300">
</div>
```

- [ ] Cada elemento tem `dark:` classe correspondente
- [ ] Só usa cores da paleta (não genéricas)
- [ ] Ícones têm fundo e cor coordenados
- [ ] Nenhuma cor orfã sem dark mode

### Layout
- [ ] Usa `max-w-6xl` para container
- [ ] Usa `mx-auto` para centralizar
- [ ] Padding: `p-4 lg:p-8`
- [ ] Grid gaps: `gap-4` ou `gap-6`
- [ ] Margins: `mb-4`, `mb-6`, `mb-8`

### Tipografia
- [ ] Títulos: `text-2xl font-bold`
- [ ] Subtítulos: `text-lg font-semibold`
- [ ] Corpo: `text-gray-600 dark:text-gray-400`
- [ ] Labels: `text-xs uppercase font-semibold`

---

## 📱 Checklist Responsivo

### Mobile (< 640px)
- [ ] Sidebar é drawer (overlay)
- [ ] Hamburger menu funciona
- [ ] Touch-friendly buttons
- [ ] Grid em 1 coluna
- [ ] Padding reduzido (`p-4`)
- [ ] Sem scroll horizontal

### Tablet (640px - 1024px)
- [ ] Grid em 2 colunas
- [ ] Sidebar ainda drawer
- [ ] Confortável ao ler
- [ ] Padding normal

### Desktop (> 1024px)
- [ ] Sidebar fixo à esquerda
- [ ] Grid em 3-4 colunas
- [ ] Content deslocado (lg:ml-64)
- [ ] Padding maior (p-8)
- [ ] Uso completo de espaço

---

## 🌓 Checklist Dark Mode

### Light Mode
- [ ] Cores bright mas não cegantes
- [ ] Texto preto/cinza escuro
- [ ] Fundos branco/cinza claro
- [ ] Suficiente contraste

### Dark Mode
- [ ] Cores desaturadas
- [ ] Texto branco/cinza claro
- [ ] Fundos preto/cinza escuro
- [ ] Suficiente contraste (WCAG AA)
- [ ] Transição suave ao toggle

### Persistência
- [ ] Dark mode persiste ao refresh
- [ ] localStorage atualiza
- [ ] Detecta preferência do sistema

---

## 🔗 Checklist de Links

### Sidebar
- [ ] Novo item listado em `sidebar_console.html`
- [ ] URL correta no `href`
- [ ] Ícone SVG presente
- [ ] Ativo quando página é acessada

### Navbar
- [ ] Logo leva para console home
- [ ] Tema toggle funciona
- [ ] Menu usuário funciona
- [ ] Logout funciona (se aplicável)

---

## 📚 Exemplos Copiar & Colar

### KPI Card Básico (Blue)
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
            <svg class="h-6 w-6"><!-- ícone --></svg>
        </span>
    </div>
    <p class="text-2xl font-bold text-gray-900 dark:text-white">123</p>
    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">Description</p>
</div>
```

### Grid 4 Colunas
```html
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <!-- 4x KPI Cards ou elementos -->
</div>
```

### Seção Container
```html
<section class="rounded-lg border border-gray-200 bg-white p-6 
                dark:border-gray-700 dark:bg-gray-800">
    <h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
        Título
    </h2>
    <!-- Conteúdo -->
</section>
```

---

## ❌ Erros Comuns

### ❌ Erro: Cor sem dark mode
```html
<!-- ERRADO -->
<div class="bg-blue-50 text-blue-700">

<!-- CORRETO -->
<div class="bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
```

### ❌ Erro: Cor genérica (não paleta)
```html
<!-- ERRADO -->
<div class="bg-red-50 text-red-700">  <!-- Vermelho não está na paleta -->

<!-- CORRETO -->
<div class="bg-pink-50 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300">
```

### ❌ Erro: Grid sem responsividade
```html
<!-- ERRADO -->
<div class="grid grid-cols-4">  <!-- Sempre 4 colunas, quebra em mobile -->

<!-- CORRETO -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
```

### ❌ Erro: Sidebar genérico
```html
<!-- ERRADO - criar próprio navbar/sidebar -->
{% include 'ui/navbar.html' %}

<!-- CORRETO - usar console_base que já inclui -->
{% extends 'console/console_base.html' %}
```

### ❌ Erro: Ícone sem container colorido
```html
<!-- ERRADO -->
<svg class="h-6 w-6 text-blue-600">

<!-- CORRETO -->
<span class="flex h-12 w-12 items-center justify-center 
             rounded-xl bg-blue-100 text-blue-600 
             dark:bg-blue-900/40 dark:text-blue-300">
    <svg class="h-6 w-6">
</span>
```

---

## ✅ Validação Final

Antes de considerar página pronta:

- [ ] Passes todos os checks acima
- [ ] Valida W3C (sem erros)
- [ ] Sem console JavaScript errors
- [ ] Lighthouse score > 80
- [ ] Acessibilidade checado
- [ ] Compatibilidade browsers modernos
- [ ] Performance aceitável
- [ ] Usabilidade mobile OK

---

## 📞 Suporte

### Dúvidas sobre:
- **Design System**: Veja `docs/DESIGN_SYSTEM.md`
- **Cores**: Veja seção "Paleta de Cores"
- **Componentes**: Veja `docs/CONSOLE_QUICK_REFERENCE.md`
- **Exemplos**: Veja `courses/templates/courses/course/list.html`

---

**Versão**: 1.0  
**Última atualização**: 2026-07-24  
**Responsável**: Design System Talk Learning
