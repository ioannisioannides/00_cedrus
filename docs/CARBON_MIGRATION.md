# Carbon Design System Migration Guide

## Overview

Cedrus is migrating from Bootstrap 5 + custom CSS to **IBM Carbon Design System** (Apache-2.0 license).

- **Repository:** https://github.com/carbon-design-system/carbon
- **Storybook:** https://web-components.carbondesignsystem.com/
- **Tracking Issue:** #64

## Current Setup

Carbon Web Components are loaded via CDN in `templates/base.html`. No npm/build step required.

### Files Added
- `static/css/carbon-cedrus.css` - Brand customization mapping Cedrus colors to Carbon tokens
- `templates/components/carbon/button.html` - Button helper template
- `templates/components/carbon/notification.html` - Notification helper template

## Using Carbon Components

### 1. Buttons

**Before (Bootstrap):**
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-danger">Delete</button>
<a href="/path" class="btn btn-secondary">Link</a>
```

**After (Carbon):**
```html
<cds-button kind="primary">Primary</cds-button>
<cds-button kind="danger">Delete</cds-button>
<cds-button kind="secondary" href="/path">Link</cds-button>
```

**Or use the template helper:**
```django
{% include "components/carbon/button.html" with label="Submit" kind="primary" type="submit" %}
```

### 2. Form Inputs

**Before (Bootstrap):**
```html
<div class="mb-3">
    <label for="name" class="form-label">Name</label>
    <input type="text" class="form-control" id="name" required>
    <div class="invalid-feedback">Name is required</div>
</div>
```

**After (Carbon):**
```html
<cds-text-input 
    label="Name" 
    name="name"
    required
    invalid-text="Name is required">
</cds-text-input>
```

### 3. Select/Dropdown

**Before (Bootstrap):**
```html
<select class="form-select" name="status">
    <option value="draft">Draft</option>
    <option value="active">Active</option>
</select>
```

**After (Carbon):**
```html
<cds-dropdown name="status" title-text="Status" label="Select status">
    <cds-dropdown-item value="draft">Draft</cds-dropdown-item>
    <cds-dropdown-item value="active">Active</cds-dropdown-item>
</cds-dropdown>
```

### 4. Notifications (Toast)

**Before (Cedrus):**
```html
<div class="cedrus-toast cedrus-toast-success">
    <div class="cedrus-toast-body">Saved successfully</div>
</div>
```

**After (Carbon):**
```html
<cds-toast-notification 
    kind="success" 
    title="Success"
    subtitle="Saved successfully"
    open>
</cds-toast-notification>
```

### 5. Modal

**Before (Bootstrap):**
```html
<div class="modal fade" id="myModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Title</h5>
            </div>
            <div class="modal-body">Content</div>
            <div class="modal-footer">
                <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button class="btn btn-primary">Save</button>
            </div>
        </div>
    </div>
</div>
```

**After (Carbon):**
```html
<cds-modal id="myModal">
    <cds-modal-header>
        <cds-modal-heading>Title</cds-modal-heading>
    </cds-modal-header>
    <cds-modal-body>Content</cds-modal-body>
    <cds-modal-footer>
        <cds-modal-footer-button kind="secondary" data-modal-close>Cancel</cds-modal-footer-button>
        <cds-modal-footer-button kind="primary">Save</cds-modal-footer-button>
    </cds-modal-footer>
</cds-modal>
```

### 6. Breadcrumbs

**Before (Bootstrap):**
```html
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/">Home</a></li>
        <li class="breadcrumb-item active">Current</li>
    </ol>
</nav>
```

**After (Carbon):**
```html
<cds-breadcrumb>
    <cds-breadcrumb-item href="/">Home</cds-breadcrumb-item>
    <cds-breadcrumb-item is-current-page>Current</cds-breadcrumb-item>
</cds-breadcrumb>
```

### 7. Tabs

**Before (Bootstrap):**
```html
<ul class="nav nav-tabs">
    <li class="nav-item">
        <button class="nav-link active" data-bs-toggle="tab">Tab 1</button>
    </li>
</ul>
```

**After (Carbon):**
```html
<cds-tabs value="tab1">
    <cds-tab id="tab1" value="tab1">Tab 1</cds-tab>
    <cds-tab id="tab2" value="tab2">Tab 2</cds-tab>
</cds-tabs>
<cds-tab-panel value="tab1">Content 1</cds-tab-panel>
<cds-tab-panel value="tab2">Content 2</cds-tab-panel>
```

### 8. Loading/Spinner

**Before (Bootstrap):**
```html
<div class="spinner-border" role="status">
    <span class="visually-hidden">Loading...</span>
</div>
```

**After (Carbon):**
```html
<cds-loading></cds-loading>
<!-- Or inline: -->
<cds-inline-loading status="active">Loading...</cds-inline-loading>
```

### 9. Toggle/Switch

**Before (Bootstrap):**
```html
<div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" id="toggle1">
    <label class="form-check-label" for="toggle1">Enable</label>
</div>
```

**After (Carbon):**
```html
<cds-toggle label-text="Enable" name="enable"></cds-toggle>
```

### 10. Data Tables

**Before (Bootstrap):**
```html
<table class="table">
    <thead><tr><th>Name</th><th>Status</th></tr></thead>
    <tbody><tr><td>Item</td><td>Active</td></tr></tbody>
</table>
```

**After (Carbon):**
```html
<cds-table>
    <cds-table-head>
        <cds-table-header-row>
            <cds-table-header-cell>Name</cds-table-header-cell>
            <cds-table-header-cell>Status</cds-table-header-cell>
        </cds-table-header-row>
    </cds-table-head>
    <cds-table-body>
        <cds-table-row>
            <cds-table-cell>Item</cds-table-cell>
            <cds-table-cell>Active</cds-table-cell>
        </cds-table-row>
    </cds-table-body>
</cds-table>
```

## Comparison: Bootstrap vs Carbon

| Aspect | Bootstrap | Carbon |
|--------|-----------|--------|
| License | MIT | Apache-2.0 |
| Components | Class-based | Web Components |
| Theming | SCSS variables | CSS custom properties |
| Accessibility | Good | Excellent (IBM standards) |
| Bundle size | ~25KB CSS | Per-component loading |
| Learning curve | Low | Medium |
| Enterprise usage | High | Very High (IBM ecosystem) |

## Migration Strategy

1. **Phase 1 (Current):** Carbon CDN loaded alongside Bootstrap - both available
2. **Phase 2:** Convert new features to Carbon, refactor high-traffic pages
3. **Phase 3:** Complete migration, remove Bootstrap
4. **Phase 4:** Remove legacy cedrus-ui.css, optimize bundle

## Theme Support

Carbon supports 4 themes:
- `white` - Light theme (default)
- `g10` - Gray 10 (light gray)
- `g90` - Gray 90 (dark)
- `g100` - Gray 100 (darkest)

The theme is applied via data attribute:
```html
<html data-carbon-theme="g10">
```

Or dynamically:
```javascript
document.documentElement.dataset.carbonTheme = 'g90';
```

## Resources

- [Carbon Storybook](https://web-components.carbondesignsystem.com/)
- [Carbon GitHub](https://github.com/carbon-design-system/carbon)
- [CDN Documentation](https://carbondesignsystem.com/developing/frameworks/web-components/#using-cdn)
- [Form Handling](https://github.com/carbon-design-system/carbon/blob/main/packages/web-components/docs/form.md)
- [Custom Styling](https://github.com/carbon-design-system/carbon/blob/main/packages/web-components/docs/styling.md)
