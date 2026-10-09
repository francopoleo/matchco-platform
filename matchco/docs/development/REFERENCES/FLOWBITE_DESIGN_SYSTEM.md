# 🎨 Flowbite Design System & UI Standards

**Status:** ✅ REQUIRED for all pages  
**Version:** 1.0  
**Last Updated:** 2026-07-27

Comprehensive design system and UI standards for MatchCo Console using Tailwind CSS + Flowbite.

---

## 📐 Layout Base Standard

Every console page must follow this layout pattern:

### Required HTML Structure

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Page Title' %}{% endblock %}

{% block content %}
<div class="w-full pt-16 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto">
        <!-- Page content here -->
    </div>
</div>
{% endblock %}
```

### Mandatory Characteristics

- ✅ **Full-width**: `w-full` (100% of screen)
- ✅ **Responsive padding**: `px-4 sm:px-6 lg:px-8` (mobile-first)
- ✅ **Top padding**: `pt-16` (below navbar)
- ✅ **Max width container**: `max-w-7xl mx-auto` (readability)
- ✅ **Dark mode support**: All elements include dark: variants

### ❌ WRONG Patterns (Avoid)

```django
<!-- DON'T: Fixed max-width -->
<div class="mx-auto w-full max-w-6xl p-6"></div>

<!-- DON'T: Uniform padding -->
<div class="w-full p-6"></div>

<!-- DON'T: Unnecessary centering -->
<div class="mx-auto w-full"></div>
```

---

## 🎨 Color Palette

### Primary Colors

| Color | Light Mode | Dark Mode | Use Case |
|-------|-----------|-----------|----------|
| **Blue** | `bg-blue-50` + `text-blue-600` | `dark:bg-blue-900/20 dark:text-blue-300` | Primary actions, info |
| **Violet** | `bg-violet-50` + `text-violet-600` | `dark:bg-violet-900/20 dark:text-violet-300` | Secondary |
| **Emerald** | `bg-emerald-50` + `text-emerald-600` | `dark:bg-emerald-900/20 dark:text-emerald-300` | Success, positive |
| **Amber** | `bg-amber-50` + `text-amber-600` | `dark:bg-amber-900/20 dark:text-amber-300` | Warning, caution |
| **Red** | `bg-red-50` + `text-red-600` | `dark:bg-red-900/20 dark:text-red-300` | Error, danger |
| **Green** | `bg-green-50` + `text-green-600` | `dark:bg-green-900/20 dark:text-green-300` | Completion, success |
| **Purple** | `bg-purple-50` + `text-purple-600` | `dark:bg-purple-900/20 dark:text-purple-300` | Premium, special |
| **Pink** | `bg-pink-50` + `text-pink-600` | `dark:bg-pink-900/20 dark:text-pink-300` | Highlight |

### Dark Mode Pattern

```html
<div class="bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300">
    Content with proper dark mode support
</div>
```

---

## 🧱 Component Library

### 1. Page Header

```django
<header class="mb-8">
    <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
            <p class="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                {% trans 'Section' %}
            </p>
            <h1 class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                {% trans 'Page Title' %}
            </h1>
            <p class="mt-1 text-gray-600 dark:text-gray-400">
                Optional subtitle or description
            </p>
        </div>
        <a href="{% url 'create' %}" class="btn-primary">
            <i class="fas fa-plus mr-2"></i>{% trans 'New' %}
        </a>
    </div>
</header>
```

### 2. KPI Cards (Metric Display)

```html
<div class="group rounded-lg border border-blue-100 bg-blue-50/50 p-5 
            transition hover:border-blue-300 hover:shadow-md
            dark:border-blue-900/30 dark:bg-blue-900/10 dark:hover:shadow-blue-900/30">
    <div class="mb-3 flex items-center justify-between">
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            Metric Label
        </p>
        <i class="fas fa-chart-line h-5 w-5 text-blue-600 dark:text-blue-400"></i>
    </div>
    <p class="text-2xl font-bold text-gray-900 dark:text-white">
        42
    </p>
    <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">
        +12% from last month
    </p>
</div>
```

**Usage Example:**
```django
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <!-- KPI Card 1 -->
    <div class="group rounded-lg border border-blue-100 bg-blue-50/50 p-5...">...</div>
    <!-- KPI Card 2 -->
    <div class="group rounded-lg border border-emerald-100 bg-emerald-50/50 p-5...">...</div>
</div>
```

### 3. Buttons

**Primary Action:**
```html
<button class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 
               transition font-medium dark:bg-blue-700 dark:hover:bg-blue-600">
    Primary Action
</button>
```

**Secondary Action:**
```html
<button class="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700
               hover:bg-gray-50 transition dark:border-gray-600 dark:bg-gray-800 
               dark:text-gray-300 dark:hover:bg-gray-700">
    Secondary Action
</button>
```

**Danger Action:**
```html
<button class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700
               transition font-medium dark:bg-red-700 dark:hover:bg-red-600">
    Delete
</button>
```

### 4. Badges/Status Indicators

```html
<!-- Success -->
<span class="px-3 py-1 rounded-full text-xs font-medium 
            bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">
    ✓ Complete
</span>

<!-- Warning -->
<span class="px-3 py-1 rounded-full text-xs font-medium 
            bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300">
    ⚠ Pending
</span>

<!-- Error -->
<span class="px-3 py-1 rounded-full text-xs font-medium 
            bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300">
    ✗ Failed
</span>
```

### 5. Cards (Content Containers)

```html
<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm
            dark:border-gray-700 dark:bg-gray-800 dark:shadow-gray-900/20">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        Card Title
    </h3>
    <p class="mt-2 text-gray-600 dark:text-gray-400">
        Card content goes here
    </p>
</div>
```

### 6. Tables

```html
<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
    <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-600 dark:text-gray-400">
                    Column
                </th>
            </tr>
        </thead>
        <tbody>
            <tr class="border-t border-gray-200 hover:bg-gray-50 
                      dark:border-gray-700 dark:hover:bg-gray-800">
                <td class="px-4 py-3 text-gray-900 dark:text-white">
                    Data
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

### 7. Forms

```html
<form class="space-y-6">
    <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Field Label
        </label>
        <input type="text" 
               class="w-full px-4 py-2 rounded-lg border border-gray-300 
                      bg-white text-gray-900 placeholder-gray-500
                      focus:border-blue-500 focus:ring-2 focus:ring-blue-200
                      dark:border-gray-600 dark:bg-gray-800 dark:text-white
                      dark:placeholder-gray-400 dark:focus:ring-blue-900/50"
               placeholder="Enter value">
    </div>
    
    <button type="submit" class="px-6 py-2 rounded-lg bg-blue-600 text-white 
                                hover:bg-blue-700 transition font-medium">
        Submit
    </button>
</form>
```

### 8. Alerts & Notifications

```html
<!-- Info -->
<div class="rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 
            dark:border-blue-900 p-4">
    <p class="text-sm text-blue-800 dark:text-blue-200">
        ℹ️ This is an informational message
    </p>
</div>

<!-- Success -->
<div class="rounded-lg bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200
            dark:border-emerald-900 p-4">
    <p class="text-sm text-emerald-800 dark:text-emerald-200">
        ✓ Operation successful
    </p>
</div>

<!-- Warning -->
<div class="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200
            dark:border-amber-900 p-4">
    <p class="text-sm text-amber-800 dark:text-amber-200">
        ⚠️ Warning message
    </p>
</div>

<!-- Error -->
<div class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200
            dark:border-red-900 p-4">
    <p class="text-sm text-red-800 dark:text-red-200">
        ✗ Error occurred
    </p>
</div>
```

---

## 📐 Complete Page Example

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Dashboard' %}{% endblock %}

{% block content %}
<div class="w-full pt-16 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
                {% trans 'Dashboard' %}
            </h1>
            <p class="mt-1 text-gray-600 dark:text-gray-400">
                Welcome to your learning dashboard
            </p>
        </header>

        <!-- KPI Cards -->
        <div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div class="group rounded-lg border border-blue-100 bg-blue-50/50 p-5
                        dark:border-blue-900/30 dark:bg-blue-900/10">
                <p class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">
                    Total Courses
                </p>
                <p class="mt-2 text-2xl font-bold text-gray-900 dark:text-white">24</p>
            </div>
        </div>

        <!-- Content Cards -->
        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm
                    dark:border-gray-700 dark:bg-gray-800">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                Recent Courses
            </h2>
            <p class="mt-2 text-gray-600 dark:text-gray-400">
                Your most accessed courses
            </p>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🎯 Design Principles

### 1. Mobile-First
- Start with mobile (320px) design
- Progressively enhance for larger screens
- Use responsive classes: `sm:`, `md:`, `lg:`, `xl:`

### 2. Accessibility
- Sufficient color contrast (WCAG AA minimum)
- Semantic HTML (use `<button>` not `<div onclick>`)
- Focus states visible (`:focus`, `:focus-ring`)
- Alt text for images

### 3. Dark Mode
- All interactive elements include `dark:` variants
- Use opacity masks: `dark:*-900/20`
- Test both light and dark modes

### 4. Consistency
- Use defined color palette only
- Match padding/spacing across components
- Keep font sizes limited (sm, base, lg, xl, 2xl)

### 5. Performance
- Minimize image sizes (lazy load when possible)
- Use CSS instead of JavaScript for animations
- Optimize Tailwind build output

---

## 🔧 Tailwind Configuration

Key settings in `tailwind.config.js`:

```javascript
module.exports = {
    theme: {
        fontFamily: {
            sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        },
        extend: {
            colors: {
                // Using default Tailwind palette
                // No custom colors needed
            },
        },
    },
    plugins: [
        require('flowbite/plugin'),
    ],
}
```

---

## 📋 Component Checklist

Before submitting any page:

- [ ] Uses `pt-16 px-4 sm:px-6 lg:px-8` padding structure
- [ ] Has dark mode support (`dark:` classes)
- [ ] Colors from approved palette only
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Links have hover states
- [ ] Buttons have focus/active states
- [ ] Text has sufficient contrast
- [ ] Forms have proper labels
- [ ] Error states clearly marked
- [ ] No hardcoded colors (use Tailwind classes)

---

## 🚀 Common Patterns

### Success Message
```html
<div class="rounded-lg bg-emerald-50 border border-emerald-200 p-4
            dark:bg-emerald-900/20 dark:border-emerald-900">
    <p class="text-sm text-emerald-800 dark:text-emerald-200">
        ✓ {{ message }}
    </p>
</div>
```

### Empty State
```html
<div class="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center
            dark:border-gray-600">
    <p class="text-gray-600 dark:text-gray-400">
        No items found
    </p>
    <a href="#" class="mt-4 inline-block text-blue-600 hover:underline
                       dark:text-blue-400">
        Create one now
    </a>
</div>
```

### Loading State
```html
<div class="flex items-center justify-center p-8">
    <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-300
                border-t-blue-600 dark:border-gray-600 dark:border-t-blue-400">
    </div>
</div>
```

---

## 📱 Responsive Breakpoints

| Class | Width | Use |
|-------|-------|-----|
| `sm:` | 640px | Tablets (landscape) |
| `md:` | 768px | Tablets (portrait) |
| `lg:` | 1024px | Desktops |
| `xl:` | 1280px | Large desktops |
| `2xl:` | 1536px | Extra large screens |

Example:
```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
    <!-- Cards that stack on mobile, 2 cols on tablet, 3-4 cols on desktop -->
</div>
```

---

## 🎓 Resources

- **Tailwind CSS Docs**: https://tailwindcss.com/docs
- **Flowbite Components**: https://flowbite.com/docs/components/
- **Dark Mode Guide**: https://tailwindcss.com/docs/dark-mode

---

**Version:** 1.0  
**Status:** Active & Required  
**Next Review:** Quarterly or when major Tailwind/Flowbite updates released
