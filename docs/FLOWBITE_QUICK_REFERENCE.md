# Flowbite - Referência Rápida de Componentes

**Guia prático para aplicar Flowbite em todas as páginas do Talk Console**

---

## 📋 Índice de Componentes

1. [Layout Base](#layout-base)
2. [Headers & Títulos](#headers--títulos)
3. [Badges](#badges)
4. [Botões](#botões)
5. [Tabelas](#tabelas)
6. [Cards](#cards)
7. [KPI Cards](#kpi-cards)
8. [Formulários](#formulários)
9. [Dropdowns](#dropdowns)
10. [Alerts](#alerts)
11. [Padrões Completos](#padrões-completos)

---

## Layout Base

### Estrutura de Página Padrão

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Page Title' %}{% endblock %}

{% block content %}
<div class="w-full">
    <!-- Page Header -->
    <header class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
            <p class="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">Section</p>
            <h1 class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{% trans 'Page Title' %}</h1>
        </div>
        <!-- Action Button -->
        <a href="{% url 'action' %}" class="btn-primary">
            <i class="fas fa-plus mr-2"></i>{% trans 'New Item' %}
        </a>
    </header>

    <!-- Content Sections -->
    {% block page_content %}{% endblock %}
</div>
{% endblock %}
```

### Máxima Largura (Full Width)
- A página agora ocupa **100% da largura disponível**
- Padding responsivo: 4px mobile, 8px desktop
- Funciona bem em telas ultralarga (até 4K)

---

## Headers & Títulos

### Header Padrão com Ação

```django
<header class="mb-8 flex flex-wrap items-center justify-between gap-4">
    <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            Talk Console
        </p>
        <h1 class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            {% trans 'Publications' %}
        </h1>
    </div>
    <a href="{% url 'create' %}" class="btn-primary">
        <i class="fas fa-plus"></i> {% trans 'New' %}
    </a>
</header>
```

### Subtítulo com Descrição

```django
<header class="mb-6">
    <p class="text-sm text-gray-600 dark:text-gray-400">
        {% trans 'Manage all publications and content' %}
    </p>
    <h1 class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
        {% trans 'Publications' %}
    </h1>
</header>
```

---

## Badges

### Status Badge Simples

```django
<!-- Success -->
<span class="badge badge-success">
    <i class="fas fa-check-circle"></i> Active
</span>

<!-- Danger -->
<span class="badge badge-danger">
    <i class="fas fa-times-circle"></i> Inactive
</span>

<!-- Warning -->
<span class="badge badge-warning">
    <i class="fas fa-exclamation-circle"></i> Pending
</span>

<!-- Info -->
<span class="badge badge-info">
    <i class="fas fa-info-circle"></i> Information
</span>
```

### Badge em Loop (Dinâmico)

```django
{% for item in items %}
<span class="badge badge-{% if item.is_active %}success{% else %}danger{% endif %}">
    {% if item.is_active %}
        <i class="fas fa-check"></i> Active
    {% else %}
        <i class="fas fa-ban"></i> Inactive
    {% endif %}
</span>
{% endfor %}
```

### Badge com Contador

```django
<span class="badge badge-info">
    <i class="fas fa-comment"></i> {{ item.comments_count }} Comments
</span>
```

---

## Botões

### Botões Básicos

```django
<!-- Primary Button -->
<button class="btn-primary">
    <i class="fas fa-save mr-2"></i>Save
</button>

<!-- Secondary Button -->
<button class="btn-secondary">
    <i class="fas fa-times mr-2"></i>Cancel
</button>

<!-- Danger Button -->
<button class="btn-danger">
    <i class="fas fa-trash mr-2"></i>Delete
</button>

<!-- Success Button -->
<button class="btn-success">
    <i class="fas fa-check mr-2"></i>Approve
</button>
```

### Botões em Grid (Ação Múltipla)

```django
<div class="flex flex-wrap gap-3">
    <button class="btn-primary">Save Changes</button>
    <button class="btn-secondary">Cancel</button>
    <button class="btn-danger">Delete</button>
</div>
```

### Botão Grande em Modal

```django
<button class="w-full rounded-sm bg-blue-600 px-4 py-3 text-center font-semibold text-white hover:bg-blue-700">
    {% trans 'Confirm Action' %}
</button>
```

---

## Tabelas

### Tabela Padrão Flowbite

```django
<div class="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
    <table class="table">
        <thead>
            <tr>
                <th scope="col">{% trans 'Name' %}</th>
                <th scope="col">{% trans 'Email' %}</th>
                <th scope="col">{% trans 'Status' %}</th>
                <th scope="col">{% trans 'Action' %}</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr>
                <th scope="row" class="font-medium">{{ user.name }}</th>
                <td>{{ user.email }}</td>
                <td>
                    <span class="badge badge-{% if user.is_active %}success{% else %}danger{% endif %}">
                        {% if user.is_active %}Active{% else %}Inactive{% endif %}
                    </span>
                </td>
                <td>
                    <a href="{% url 'edit' user.pk %}" class="text-blue-600 hover:underline">
                        {% trans 'Edit' %}
                    </a>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                    {% trans 'No results found.' %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

### Tabela com Checkboxes

```django
<table class="table">
    <thead>
        <tr>
            <th scope="col" class="w-4 p-4">
                <input type="checkbox" class="rounded-sm border-gray-300">
            </th>
            <th scope="col">{% trans 'Name' %}</th>
            <th scope="col">{% trans 'Status' %}</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td class="w-4 p-4">
                <input type="checkbox" class="rounded-sm border-gray-300">
            </td>
            <td>{{ item.name }}</td>
            <td>
                <span class="badge badge-success">{{ item.status }}</span>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Tabela Responsiva (Mobile/Desktop)

```django
<!-- Desktop: Table -->
<div class="hidden overflow-x-auto rounded-lg border border-gray-200 md:block">
    <table class="table">
        <!-- Conteúdo da tabela -->
    </table>
</div>

<!-- Mobile: Cards -->
<div class="space-y-3 md:hidden">
    {% for item in items %}
    <div class="card">
        <div class="flex items-start justify-between">
            <div>
                <h3 class="font-semibold text-gray-900">{{ item.name }}</h3>
                <p class="mt-1 text-sm text-gray-600">{{ item.category }}</p>
            </div>
            <span class="badge badge-success">{{ item.status }}</span>
        </div>
    </div>
    {% endfor %}
</div>
```

---

## Cards

### Card Básico

```django
<div class="card">
    <h2 class="text-lg font-bold text-gray-900">Card Title</h2>
    <p class="mt-3 text-gray-600">Card content goes here</p>
</div>
```

### Card com Header e Footer

```django
<div class="card">
    <div class="card-header">
        <h2 class="card-title">{% trans 'Settings' %}</h2>
        <p class="card-subtitle">{% trans 'Manage your preferences' %}</p>
    </div>
    
    <div class="card-body">
        <!-- Form or content here -->
    </div>
    
    <div class="card-footer">
        <button class="btn-primary">{% trans 'Save' %}</button>
        <button class="btn-secondary">{% trans 'Cancel' %}</button>
    </div>
</div>
```

### Card em Grid (Dashboard)

```django
<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
    {% for section in sections %}
    <a href="{% url 'view' section.pk %}" class="card group transition-all hover:shadow-md">
        <div class="flex items-start justify-between">
            <div>
                <h3 class="font-semibold text-gray-900 group-hover:text-blue-600">
                    {{ section.title }}
                </h3>
                <p class="mt-1 text-sm text-gray-600">{{ section.description }}</p>
            </div>
            <i class="fas fa-arrow-right text-gray-400 group-hover:text-blue-600"></i>
        </div>
    </a>
    {% endfor %}
</div>
```

---

## KPI Cards

### KPI Card Simples

```django
<div class="kpi">
    <div>
        <p class="kpi-label">{% trans 'Total Users' %}</p>
        <p class="kpi-value">1,234</p>
        <p class="kpi-hint">{% trans 'Active users this month' %}</p>
    </div>
    <div class="kpi-icon">
        <i class="fas fa-users"></i>
    </div>
</div>
```

### KPI com Unidade e Trend

```django
<div class="kpi">
    <div>
        <p class="kpi-label">{% trans 'Revenue' %}</p>
        <p class="kpi-value">
            $12,450
            <span class="kpi-unit">USD</span>
        </p>
        <p class="kpi-hint">
            <i class="fas fa-arrow-up text-green-600"></i> 12% from last month
        </p>
    </div>
    <div class="kpi-icon success">
        <i class="fas fa-chart-line"></i>
    </div>
</div>
```

### KPI Grid (Dashboard)

```django
<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
    <div class="kpi">
        <div>
            <p class="kpi-label">{% trans 'Publications' %}</p>
            <p class="kpi-value">{{ pub_count }}</p>
        </div>
        <div class="kpi-icon">
            <i class="fas fa-newspaper"></i>
        </div>
    </div>

    <div class="kpi">
        <div>
            <p class="kpi-label">{% trans 'Users' %}</p>
            <p class="kpi-value">{{ user_count }}</p>
        </div>
        <div class="kpi-icon success">
            <i class="fas fa-users"></i>
        </div>
    </div>

    <div class="kpi">
        <div>
            <p class="kpi-label">{% trans 'Revenue' %}</p>
            <p class="kpi-value">${{ revenue }}</p>
        </div>
        <div class="kpi-icon warning">
            <i class="fas fa-dollar-sign"></i>
        </div>
    </div>

    <div class="kpi">
        <div>
            <p class="kpi-label">{% trans 'Pending' %}</p>
            <p class="kpi-value">{{ pending_count }}</p>
        </div>
        <div class="kpi-icon danger">
            <i class="fas fa-exclamation-circle"></i>
        </div>
    </div>
</div>
```

---

## Formulários

### Form Padrão

```django
<form method="post" class="card">
    {% csrf_token %}
    
    <div class="card-header">
        <h2 class="card-title">{% trans 'Contact Information' %}</h2>
    </div>
    
    <div class="card-body space-y-4">
        <!-- Text Input -->
        <div>
            <label for="name" class="mb-2 block text-sm font-medium text-gray-900">
                {% trans 'Full Name' %}
            </label>
            <input 
                type="text" 
                id="name" 
                name="name"
                class="form-input-compact w-full"
                placeholder="{% trans 'Enter your name' %}"
            >
        </div>

        <!-- Email Input -->
        <div>
            <label for="email" class="mb-2 block text-sm font-medium text-gray-900">
                {% trans 'Email' %}
            </label>
            <input 
                type="email" 
                id="email" 
                name="email"
                class="form-input-compact w-full"
                placeholder="user@example.com"
            >
        </div>

        <!-- Select -->
        <div>
            <label for="status" class="mb-2 block text-sm font-medium text-gray-900">
                {% trans 'Status' %}
            </label>
            <select id="status" name="status" class="form-select-compact w-full">
                <option value="">{% trans 'Select status' %}</option>
                <option value="active">{% trans 'Active' %}</option>
                <option value="inactive">{% trans 'Inactive' %}</option>
            </select>
        </div>

        <!-- Textarea -->
        <div>
            <label for="notes" class="mb-2 block text-sm font-medium text-gray-900">
                {% trans 'Notes' %}
            </label>
            <textarea 
                id="notes" 
                name="notes"
                rows="4"
                class="form-input-compact w-full"
                placeholder="{% trans 'Enter notes' %}"
            ></textarea>
        </div>

        <!-- Checkbox -->
        <div class="flex items-center">
            <input 
                type="checkbox" 
                id="agree" 
                name="agree"
                class="rounded-sm border-gray-300"
            >
            <label for="agree" class="ml-2 text-sm text-gray-700">
                {% trans 'I agree to the terms' %}
            </label>
        </div>
    </div>
    
    <div class="card-footer flex flex-wrap gap-3">
        <button type="submit" class="btn-primary">{% trans 'Save' %}</button>
        <button type="reset" class="btn-secondary">{% trans 'Clear' %}</button>
        <a href="{% url 'back' %}" class="btn-secondary">{% trans 'Cancel' %}</a>
    </div>
</form>
```

### Form em Grid (Multiple Columns)

```django
<div class="card">
    <form method="post">
        {% csrf_token %}
        
        <div class="grid gap-4 sm:grid-cols-2">
            <div>
                <label class="mb-2 block text-sm font-medium">{% trans 'First Name' %}</label>
                <input type="text" class="form-input-compact w-full" placeholder="John">
            </div>
            <div>
                <label class="mb-2 block text-sm font-medium">{% trans 'Last Name' %}</label>
                <input type="text" class="form-input-compact w-full" placeholder="Doe">
            </div>
        </div>

        <div class="mt-4">
            <button type="submit" class="btn-primary">{% trans 'Save' %}</button>
        </div>
    </form>
</div>
```

---

## Dropdowns

### Dropdown Básico

```django
<div class="relative">
    <button 
        data-dropdown-toggle="dropdown-menu"
        class="btn-secondary"
    >
        {% trans 'Actions' %} <i class="fas fa-chevron-down ml-2"></i>
    </button>
    
    <div id="dropdown-menu" class="dropdown hidden">
        <a href="{% url 'edit' %}" class="dropdown-item">
            <i class="fas fa-edit mr-2"></i>{% trans 'Edit' %}
        </a>
        <a href="{% url 'duplicate' %}" class="dropdown-item">
            <i class="fas fa-copy mr-2"></i>{% trans 'Duplicate' %}
        </a>
        <div class="dropdown-divider"></div>
        <a href="{% url 'delete' %}" class="dropdown-item text-red-600">
            <i class="fas fa-trash mr-2"></i>{% trans 'Delete' %}
        </a>
    </div>
</div>
```

### Dropdown em Tabela

```django
<td>
    <div class="relative">
        <button 
            data-dropdown-toggle="dropdown-{{ item.pk }}"
            class="inline-flex items-center gap-2 rounded-sm px-3 py-2 text-sm hover:bg-gray-100"
        >
            <i class="fas fa-ellipsis-v"></i>
        </button>
        
        <div id="dropdown-{{ item.pk }}" class="dropdown hidden">
            <a href="{% url 'edit' item.pk %}" class="dropdown-item">Edit</a>
            <a href="{% url 'view' item.pk %}" class="dropdown-item">View</a>
            <a href="{% url 'delete' item.pk %}" class="dropdown-item text-red-600">Delete</a>
        </div>
    </div>
</td>
```

---

## Alerts

### Alert Simples

```django
<!-- Success -->
<div class="alert alert-success">
    <strong>{% trans 'Success!' %}</strong> {% trans 'Your changes have been saved.' %}
</div>

<!-- Warning -->
<div class="alert alert-warning">
    <strong>{% trans 'Warning!' %}</strong> {% trans 'Please review this information.' %}
</div>

<!-- Danger -->
<div class="alert alert-danger">
    <strong>{% trans 'Error!' %}</strong> {% trans 'Something went wrong.' %}
</div>

<!-- Info -->
<div class="alert alert-info">
    <strong>{% trans 'Info:' %}</strong> {% trans 'This is informational.' %}
</div>
```

### Alert com Ícone

```django
<div class="alert alert-success">
    <div class="flex">
        <i class="fas fa-check-circle mt-0.5 mr-3"></i>
        <div>
            <strong>{% trans 'Success!' %}</strong>
            <p class="mt-1 text-sm">{% trans 'The operation completed successfully.' %}</p>
        </div>
    </div>
</div>
```

---

## Padrões Completos

### Página de Lista com Filtro

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Users' %}{% endblock %}

{% block content %}
<div class="w-full">
    <!-- Header -->
    <header class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">{% trans 'Users' %}</h1>
        </div>
        <a href="{% url 'create' %}" class="btn-primary">
            <i class="fas fa-plus mr-2"></i>{% trans 'New User' %}
        </a>
    </header>

    <!-- Filter Form -->
    <form method="get" class="card mb-8">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
                <label class="mb-2 block text-sm font-medium">{% trans 'Search' %}</label>
                <input 
                    type="text" 
                    name="q" 
                    value="{{ request.GET.q }}"
                    class="form-input-compact w-full"
                    placeholder="{% trans 'Name, email...' %}"
                >
            </div>
            <div>
                <label class="mb-2 block text-sm font-medium">{% trans 'Role' %}</label>
                <select name="role" class="form-select-compact w-full">
                    <option value="">{% trans 'All' %}</option>
                    <option value="admin">{% trans 'Admin' %}</option>
                    <option value="user">{% trans 'User' %}</option>
                </select>
            </div>
            <div>
                <label class="mb-2 block text-sm font-medium">{% trans 'Status' %}</label>
                <select name="status" class="form-select-compact w-full">
                    <option value="">{% trans 'All' %}</option>
                    <option value="active">{% trans 'Active' %}</option>
                    <option value="inactive">{% trans 'Inactive' %}</option>
                </select>
            </div>
            <div class="flex items-end">
                <button type="submit" class="btn-primary w-full">{% trans 'Filter' %}</button>
            </div>
        </div>
    </form>

    <!-- Table (Desktop) -->
    <div class="hidden overflow-x-auto rounded-lg border border-gray-200 md:block">
        <table class="table">
            <thead>
                <tr>
                    <th>{% trans 'Name' %}</th>
                    <th>{% trans 'Email' %}</th>
                    <th>{% trans 'Role' %}</th>
                    <th>{% trans 'Status' %}</th>
                    <th>{% trans 'Action' %}</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <th class="font-medium">{{ user.name }}</th>
                    <td>{{ user.email }}</td>
                    <td>{{ user.get_role_display }}</td>
                    <td>
                        <span class="badge badge-{% if user.is_active %}success{% else %}danger{% endif %}">
                            {% if user.is_active %}{% trans 'Active' %}{% else %}{% trans 'Inactive' %}{% endif %}
                        </span>
                    </td>
                    <td>
                        <a href="{% url 'edit' user.pk %}" class="text-blue-600 hover:underline">
                            {% trans 'Edit' %}
                        </a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                        {% trans 'No users found.' %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Cards (Mobile) -->
    <div class="space-y-3 md:hidden">
        {% for user in users %}
        <div class="card">
            <div class="flex items-start justify-between">
                <div>
                    <h3 class="font-semibold">{{ user.name }}</h3>
                    <p class="mt-1 text-sm text-gray-600">{{ user.email }}</p>
                </div>
                <span class="badge badge-{% if user.is_active %}success{% else %}danger{% endif %}">
                    {% if user.is_active %}Active{% else %}Inactive{% endif %}
                </span>
            </div>
            <div class="mt-3 flex gap-2">
                <a href="{% url 'edit' user.pk %}" class="btn-secondary text-sm">Edit</a>
                <a href="{% url 'delete' user.pk %}" class="btn-danger text-sm">Delete</a>
            </div>
        </div>
        {% empty %}
        <div class="card text-center text-gray-500">
            {% trans 'No users found.' %}
        </div>
        {% endfor %}
    </div>

    <!-- Pagination -->
    {% if is_paginated %}
    <nav class="mt-8 flex justify-center gap-2">
        {% if page_obj.has_previous %}
        <a href="?page=1" class="btn-secondary">{% trans 'First' %}</a>
        <a href="?page={{ page_obj.previous_page_number }}" class="btn-secondary">
            {% trans 'Previous' %}
        </a>
        {% endif %}

        <span class="flex items-center px-4">
            {% trans 'Page' %} {{ page_obj.number }} {% trans 'of' %} {{ page_obj.paginator.num_pages }}
        </span>

        {% if page_obj.has_next %}
        <a href="?page={{ page_obj.next_page_number }}" class="btn-secondary">
            {% trans 'Next' %}
        </a>
        <a href="?page={{ page_obj.paginator.num_pages }}" class="btn-secondary">
            {% trans 'Last' %}
        </a>
        {% endif %}
    </nav>
    {% endif %}
</div>
{% endblock %}
```

### Dashboard com KPIs

```django
{% extends 'console/base.html' %}
{% load i18n %}

{% block title %}{% trans 'Dashboard' %}{% endblock %}

{% block content %}
<div class="w-full">
    <!-- Header -->
    <header class="mb-8">
        <p class="text-sm text-gray-600 dark:text-gray-400">{% trans 'Welcome back!' %}</p>
        <h1 class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            {% trans 'Dashboard' %}
        </h1>
    </header>

    <!-- KPI Grid -->
    <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div class="kpi">
            <div>
                <p class="kpi-label">{% trans 'Total Revenue' %}</p>
                <p class="kpi-value">$54,321</p>
                <p class="kpi-hint">{% trans 'This month' %}</p>
            </div>
            <div class="kpi-icon">
                <i class="fas fa-dollar-sign"></i>
            </div>
        </div>

        <div class="kpi">
            <div>
                <p class="kpi-label">{% trans 'Users' %}</p>
                <p class="kpi-value">2,543</p>
                <p class="kpi-hint">{% trans 'Active users' %}</p>
            </div>
            <div class="kpi-icon success">
                <i class="fas fa-users"></i>
            </div>
        </div>

        <div class="kpi">
            <div>
                <p class="kpi-label">{% trans 'Conversions' %}</p>
                <p class="kpi-value">3.2%</p>
                <p class="kpi-hint">↑ 0.5% from last week</p>
            </div>
            <div class="kpi-icon warning">
                <i class="fas fa-chart-bar"></i>
            </div>
        </div>

        <div class="kpi">
            <div>
                <p class="kpi-label">{% trans 'Pending' %}</p>
                <p class="kpi-value">12</p>
                <p class="kpi-hint">{% trans 'Requires action' %}</p>
            </div>
            <div class="kpi-icon danger">
                <i class="fas fa-exclamation-circle"></i>
            </div>
        </div>
    </div>

    <!-- Charts Section -->
    <div class="grid gap-6 lg:grid-cols-2">
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">{% trans 'Revenue Trend' %}</h2>
            </div>
            <div class="card-body">
                <!-- Chart placeholder -->
                <div class="h-64 rounded bg-gray-100 dark:bg-gray-700"></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h2 class="card-title">{% trans 'Recent Activity' %}</h2>
            </div>
            <div class="card-body space-y-3">
                <!-- Activity items -->
                <div class="flex items-start gap-3 border-b pb-3 last:border-0">
                    <i class="fas fa-check-circle text-green-600 mt-0.5"></i>
                    <div>
                        <p class="text-sm font-medium">{% trans 'User registered' %}</p>
                        <p class="text-xs text-gray-500">John Doe - 2 hours ago</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🎨 Cores e Iconografia

### Cores Padrão

| Uso | Classe | Cor |
|-----|--------|-----|
| Sucesso | `badge-success`, `kpi-icon success` | Verde (#10B981) |
| Erro | `badge-danger`, `kpi-icon danger` | Vermelho (#EF4444) |
| Aviso | `badge-warning`, `kpi-icon warning` | Amarelo (#F59E0B) |
| Informação | `badge-info` | Azul (#3B82F6) |
| Primário | `btn-primary`, `kpi-icon` | Azul (#2563EB) |
| Secundário | `btn-secondary` | Cinza (#6B7280) |

### Ícones Recomendados (Font Awesome 6)

```
User: fas fa-user, fas fa-users
Edit: fas fa-edit, fas fa-pen
Delete: fas fa-trash
Search: fas fa-search, fas fa-magnifying-glass
Menu: fas fa-bars, fas fa-ellipsis-v
Arrow: fas fa-arrow-right, fas fa-chevron-right
Check: fas fa-check, fas fa-check-circle
Close: fas fa-times, fas fa-x
Plus: fas fa-plus
Settings: fas fa-cog, fas fa-gear
Home: fas fa-home
Chart: fas fa-chart-bar, fas fa-chart-line
```

---

## 📱 Breakpoints Responsivos

```
sm: 640px  (tablets em portrait)
md: 768px  (tablets em landscape)
lg: 1024px (desktops pequenos)
xl: 1280px (desktops)
2xl: 1536px (telas grandes)
```

### Exemplo de Uso

```django
<!-- Oculto em mobile, visível em desktop (md+) -->
<div class="hidden md:block">
    Desktop content
</div>

<!-- Visível em mobile, oculto em desktop (md+) -->
<div class="md:hidden">
    Mobile content
</div>

<!-- Grid responsivo -->
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <!-- Items -->
</div>
```

---

## ✅ Checklist de Implementação

Ao criar uma nova página, verifique:

- [ ] Header com título e ação principal
- [ ] Badges para status/estados
- [ ] Tabela (desktop) + Cards (mobile)
- [ ] Botões com ícones (Font Awesome)
- [ ] Formulários com labels e placeholders
- [ ] KPIs se for dashboard
- [ ] Dark mode testing
- [ ] Responsividade em mobile/tablet/desktop
- [ ] Espaçamento consistente (gap-4, gap-6)
- [ ] Cores apropriadas para status

---

## 🔗 Referências

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Flowbite Docs](https://flowbite.com/)
- [Font Awesome Icons](https://fontawesome.com/icons)
- [Documentação Flowbite Completa](./FLOWBITE_IMPLEMENTATION.md)

---

**Atualizado**: 2026-07-24  
**Versão**: 1.0  
**Status**: ✅ Pronto para Uso
