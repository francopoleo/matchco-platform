# Flowbite Implementation - Component Library Guide

**Status**: ✅ IMPLEMENTED  
**Date**: 2026-07-24

---

## Overview

The project now uses **Flowbite** - a Tailwind CSS component library - for consistent, modern UI components with built-in dark mode support and reduced border-radius for a more compact design.

### Key Features
- ✅ Compact badges (reduced padding/spacing)
- ✅ Flowbite-styled tables with hover effects
- ✅ Modern card components
- ✅ Enhanced KPI cards with icons
- ✅ Forms with reduced border-radius (inputs, buttons, dropdowns)
- ✅ Full dark mode support
- ✅ Responsive design (mobile-first)

---

## Project Setup

### CDN Resources Loaded
```html
<!-- Tailwind CSS JIT (Just-in-Time) Compiler -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Flowbite Component Library -->
<script src="https://cdn.jsdelivr.net/npm/flowbite@2.0.0/dist/flowbite.min.js"></script>

<!-- Font Awesome Icons -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
```

### Local CSS Files
- **`cep/static/ui/css/app.css`** - Main component styles (badges, tables, cards, KPIs, forms)
- **`cep/static/ui/css/tailwind.css`** - Tailwind layer utilities

### Local JS Files
- **`cep/static/ui/js/theme.js`** - Dark mode toggle and persistence
- **`cep/static/ui/js/app-shell.js`** - Interactive components (sidebar, menus, dropdowns)

---

## Component Library

### 1. Badges (Compact & Colorful)

**Template Usage**:
```django
<span class="badge badge-{{ tone }}">{{ label }}</span>
```

**Available Tones**:
- `badge-success` - Green (✓ Active, Published)
- `badge-danger` - Red (✗ Inactive, Rejected)
- `badge-warning` - Yellow (! Draft, Pending)
- `badge-info` - Blue (ℹ Information)
- `badge-primary` - Indigo (Primary action)
- `badge-neutral` - Gray (Neutral/Default)

**Example**:
```django
<span class="badge badge-success">Active</span>
<span class="badge badge-warning">Draft</span>
<span class="badge badge-danger">Inactive</span>
```

**CSS Classes** (in app.css):
```css
.badge {
  @apply inline-flex items-center gap-2 rounded-md px-2.5 py-1 text-xs font-semibold;
}

.badge-success {
  @apply bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200;
}
```

---

### 2. Tables (Flowbite Styled)

**Template Usage**:
```django
<table class="table">
    <thead>
        <tr>
            <th scope="col">Column 1</th>
            <th scope="col">Column 2</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.field1 }}</td>
            <td>{{ item.field2 }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

**Features**:
- Alternating row backgrounds (odd/even)
- Hover effect on rows
- Compact padding
- Full dark mode support
- Responsive container with border-radius

**CSS Classes**:
```css
.table {
  @apply w-full text-left text-sm text-gray-700 dark:text-gray-300;
}

.table thead {
  @apply border-b-2 border-gray-300 bg-gray-100 dark:border-gray-600 dark:bg-gray-800;
}

.table tbody tr {
  @apply transition-colors duration-150 hover:bg-gray-50 dark:hover:bg-gray-700;
}
```

---

### 3. Cards (Modern Containers)

**Template Usage**:
```django
<div class="card">
    <div class="card-header">
        <h2 class="card-title">Card Title</h2>
        <p class="card-subtitle">Optional subtitle</p>
    </div>
    <div class="card-body">
        <!-- Content here -->
    </div>
    <div class="card-footer">
        <!-- Footer content -->
    </div>
</div>
```

**Features**:
- Rounded corners (lg)
- Subtle border
- Shadow on hover
- Full dark mode support
- Flexible layout

**CSS Classes**:
```css
.card {
  @apply rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800;
}

.card-header {
  @apply mb-4 border-b border-gray-200 pb-4 dark:border-gray-700;
}

.card-title {
  @apply text-lg font-bold text-gray-900 dark:text-white;
}
```

---

### 4. KPI Cards (Key Performance Indicators)

**Template Usage**:
```django
<div class="kpi">
    <div>
        <p class="kpi-label">Total Users</p>
        <p class="kpi-value">
            1,234
            <span class="kpi-unit">users</span>
        </p>
        <p class="kpi-hint">↑ 12% from last week</p>
    </div>
    <div class="kpi-icon success">
        <i class="fas fa-users"></i>
    </div>
</div>
```

**Features**:
- Large value display (text-3xl font)
- Optional unit label
- Hint text for additional context
- Icon container with color variants
- Minimum height for consistency

**Icon Color Variants**:
- `kpi-icon` (default blue)
- `kpi-icon success` (green)
- `kpi-icon warning` (yellow)
- `kpi-icon danger` (red)

**CSS Classes**:
```css
.kpi {
  @apply card flex min-h-[160px] flex-col justify-between;
}

.kpi-value {
  @apply text-3xl font-bold text-gray-900 dark:text-white;
}

.kpi-icon {
  @apply inline-flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600;
}
```

---

### 5. Form Elements (Reduced Border Radius)

All form inputs have `rounded-sm` (0.25rem) for compact appearance.

**Input Fields**:
```django
<input type="text" placeholder="Enter text" class="form-input-compact">
<select class="form-select-compact">
    <option>Option 1</option>
</select>
<textarea class="form-input-compact"></textarea>
```

**Button Variants**:
```django
<!-- Primary Button -->
<button class="btn-primary">Save</button>

<!-- Secondary Button -->
<button class="btn-secondary">Cancel</button>

<!-- Danger Button -->
<button class="btn-danger">Delete</button>

<!-- Success Button -->
<button class="btn-success">Approve</button>
```

**CSS Classes**:
```css
/* All form inputs auto-styled */
input, select, textarea {
  @apply rounded-sm border border-gray-300 px-3 py-2 text-sm;
  @apply focus:border-blue-500 focus:ring-1 focus:ring-blue-500;
}

.btn-primary {
  @apply rounded-sm bg-blue-600 text-white hover:bg-blue-700;
}
```

---

### 6. Dropdowns (Compact Radius)

**Template Usage**:
```django
<div class="relative">
    <button data-dropdown-toggle="dropdown-menu" class="btn-secondary">
        Menu
    </button>
    <div id="dropdown-menu" class="dropdown hidden">
        <a href="#" class="dropdown-item">Option 1</a>
        <a href="#" class="dropdown-item">Option 2</a>
        <div class="dropdown-divider"></div>
        <a href="#" class="dropdown-item">Option 3</a>
    </div>
</div>
```

**Features**:
- Compact border-radius (rounded-sm)
- Click-outside detection
- Escape key support
- Smooth transitions

---

### 7. Alert Boxes

**Template Usage**:
```django
<div class="alert alert-success">
    <strong>Success!</strong> Your action was completed.
</div>

<div class="alert alert-warning">
    <strong>Warning:</strong> Please review this information.
</div>

<div class="alert alert-danger">
    <strong>Error:</strong> Something went wrong.
</div>
```

**Alert Tones**:
- `alert-success` - Green
- `alert-warning` - Yellow
- `alert-danger` - Red
- `alert-info` - Blue

---

## Color System

### Tailwind Color Palette
All components use Tailwind's default color palette:
- **Gray** - Neutral backgrounds/text
- **Blue** - Primary actions
- **Green** - Success states
- **Yellow** - Warning states
- **Red** - Danger/error states
- **Purple** - Secondary/accent
- **Indigo** - Primary alternatives

### Dark Mode
Dark mode is automatically applied when `dark` class is on `<html>` element.

**Color Adjustments in Dark Mode**:
```css
/* Light Mode -->|<-- Dark Mode */
bg-white          -->|<-- dark:bg-gray-800
text-gray-900     -->|<-- dark:text-white
border-gray-200   -->|<-- dark:border-gray-700
bg-blue-100       -->|<-- dark:bg-blue-900
```

---

## Current Usage in Console

### Dashboard (`console/dashboard.html`)
- ✅ KPI cards with colored icons (blue, purple)
- ✅ Hover effects and focus rings
- ✅ Proper spacing and typography

### Publication List (`console/publication_list.html`)
- ✅ Flowbite-styled table
- ✅ Status badges (success/warning)
- ✅ Mobile card view with badges
- ✅ Responsive layout

### Policy List (`console/policy_list.html`)
- ✅ Flowbite-styled table
- ✅ Active/Inactive badges
- ✅ Mobile card view with badges
- ✅ Full dark mode support

---

## Responsive Breakpoints

All components use Tailwind's responsive modifiers:

```
sm: 640px   (tablets in portrait)
md: 768px   (tablets in landscape)
lg: 1024px  (small desktops)
xl: 1280px  (desktops)
2xl: 1536px (large screens)
```

**Example**:
```django
<div class="block md:hidden">
    <!-- Mobile view (visible on devices < 768px) -->
</div>

<div class="hidden md:block">
    <!-- Desktop view (visible on devices >= 768px) -->
</div>
```

---

## Using Icons with Components

Font Awesome icons can be used in components:

```django
<!-- In badges -->
<span class="badge badge-success">
    <i class="fas fa-check"></i> Published
</span>

<!-- In KPI cards -->
<div class="kpi-icon success">
    <i class="fas fa-star"></i>
</div>

<!-- In buttons -->
<button class="btn-primary">
    <i class="fas fa-save"></i> Save
</button>
```

---

## Customization Guide

### Adding Custom Badge Tone
Edit `cep/static/ui/css/app.css`:

```css
@layer components {
    .badge-custom {
        @apply bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200;
    }
}
```

Then use:
```django
<span class="badge badge-custom">Custom Badge</span>
```

### Changing Button Colors
Edit `cep/static/ui/css/app.css`:

```css
.btn-custom {
    @apply rounded-sm bg-gradient-to-r from-pink-500 to-red-500 text-white hover:from-pink-600 hover:to-red-600;
}
```

### Extending KPI Icon Colors
```css
.kpi-icon.custom {
    @apply bg-pink-100 text-pink-600 dark:bg-pink-900 dark:text-pink-200;
}
```

---

## Migration Guide

### From Old Styling to Flowbite

**Before**:
```django
<div class="console-kpi-card">
    <p class="console-kpi-label">Total</p>
    <p class="console-kpi-value">100</p>
</div>
```

**After**:
```django
<div class="kpi">
    <div>
        <p class="kpi-label">Total</p>
        <p class="kpi-value">100</p>
    </div>
    <div class="kpi-icon">
        <i class="fas fa-chart-bar"></i>
    </div>
</div>
```

---

## Performance Notes

1. **Tailwind JIT** - Only CSS for used classes is generated (no bloat)
2. **Flowbite JS** - Minimal size (~15KB gzipped)
3. **Font Awesome** - Loaded from CDN, cached efficiently
4. **Dark Mode** - Uses CSS class toggle (no flash)

---

## Accessibility Features

- ✅ Semantic HTML (`<button>`, `<table>`, `<th>`, etc.)
- ✅ ARIA attributes for dropdowns and menus
- ✅ Focus states on all interactive elements
- ✅ High contrast colors (WCAG AA compliant)
- ✅ Keyboard navigation support
- ✅ Screen reader friendly

---

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari 14+, Chrome Android 90+)

---

## Common Patterns

### Status Column with Badges
```django
<td>
    <span class="badge badge-{% if item.is_active %}success{% else %}danger{% endif %}">
        {% if item.is_active %}Active{% else %}Inactive{% endif %}
    </span>
</td>
```

### Centered KPI Grid
```django
<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
    {% for kpi in kpis %}
    <div class="kpi">
        <div>
            <p class="kpi-label">{{ kpi.label }}</p>
            <p class="kpi-value">{{ kpi.value }}</p>
        </div>
        <div class="kpi-icon">
            <i class="{{ kpi.icon }}"></i>
        </div>
    </div>
    {% endfor %}
</div>
```

### Action Buttons in Tables
```django
<td>
    <a href="{% url 'edit' item.pk %}" class="btn-secondary">Edit</a>
    <button class="btn-danger">Delete</button>
</td>
```

---

## Troubleshooting

### Styles Not Applying
1. Clear browser cache (Ctrl+Shift+Delete)
2. Refresh page (Ctrl+F5)
3. Check that base.html includes CDN resources
4. Verify class names match exactly

### Dark Mode Not Working
1. Ensure `dark` class is on `<html>` element
2. Check `theme.js` is loaded
3. Verify browser supports localStorage

### Icons Not Showing
1. Check Font Awesome CSS is loaded
2. Verify icon class names (e.g., `fas fa-check`)
3. Clear browser cache

---

## Next Steps

1. **Review Console Pages** - Test dashboard, publications, policies
2. **User Feedback** - Gather feedback on styling
3. **Additional Pages** - Apply Flowbite to other console pages
4. **Customization** - Adjust colors/spacing per brand guidelines
5. **Documentation** - Update team docs with component usage

---

## Resources

- [Tailwind CSS](https://tailwindcss.com/docs)
- [Flowbite](https://flowbite.com/docs/getting-started/introduction/)
- [Font Awesome Icons](https://fontawesome.com/icons)
- [Dark Mode Guide](https://tailwindcss.com/docs/dark-mode)

---

**Status**: Ready for Testing  
**Implemented by**: Claude Code  
**Last Updated**: 2026-07-24
