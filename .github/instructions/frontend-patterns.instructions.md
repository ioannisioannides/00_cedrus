---
applyTo: "templates/**,static/js/**"
---

# Frontend Patterns — IBM Carbon Design System + Django Templates

## Key Rules

1. **No inline `<script>` blocks** — all JavaScript goes in `static/js/` external files
2. Pass Django template variables to JS via `data-*` attributes on HTML elements
3. Use IBM Carbon Web Components (CDN) for UI elements
4. All pages extend `templates/base.html`

## Data Attribute Pattern (for template variables in JS)

```html
{# In Django template — pass context to external JS via data attributes #}
<div hidden
     data-my-component
     data-user-id="{{ user.pk }}"
     data-org-id="{{ organization.pk }}"
     data-audit-status="{{ audit.status }}"></div>
```

```javascript
// In static/js/cedrus-*.js — read data attributes
(function () {
    'use strict';
    function init() {
        const container = document.querySelector('[data-my-component]');
        if (!container) return;
        const userId = container.dataset.userId;
        const orgId = container.dataset.orgId;
        // ... use values
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
```

## IBM Carbon Components (CDN)

Components are loaded as Web Components via CDN modules in `base.html`. Use them as HTML elements:

```html
<bx-btn kind="primary" type="submit">Save</bx-btn>
<bx-modal id="confirm-modal">
  <bx-modal-header>
    <bx-modal-heading>Confirm Action</bx-modal-heading>
  </bx-modal-header>
  <bx-modal-body>Are you sure?</bx-modal-body>
  <bx-modal-footer>
    <bx-btn kind="secondary" data-modal-close>Cancel</bx-btn>
    <bx-btn kind="danger">Confirm</bx-btn>
  </bx-modal-footer>
</bx-modal>
```

## Template Inheritance

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Audit Detail — {{ audit.title }}{% endblock %}

{% block content %}
<div class="bx--grid">
  <div class="bx--row">
    <div class="bx--col-lg-12">
      <!-- content here -->
    </div>
  </div>
</div>
{% endblock %}
```

## Static Files

- `static/js/cedrus-app.js` — Main application JS (event handlers, UI)
- `static/js/cedrus-forms.js` — Form enhancements, date validation, confirmation modals
- `static/js/cedrus-a11y.js` — Accessibility utilities, ARIA announcements

## CSRF for AJAX Requests

```javascript
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
});
```
