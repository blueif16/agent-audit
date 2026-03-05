# Accessibility Fix PR: Example Domain

**Page:** https://example.com
**Priority Score:** 8/10

---

## Critical: Non-text Content (1.1.1)

**Detected by:** vision
**Element index:** 0

**Description:** Image missing alt text - The logo image at the top of the page does not have alternative text, making it inaccessible to screen reader users.

**Remediation hint:** Add appropriate alt attribute describing the image content or function.

**Before:**
```html
<img src="logo.png" class="header-logo">
```

**After:**
```html
<img src="logo.png" class="header-logo" alt="Example Domain Logo">
```

---

## Critical: Name, Role, Value (4.1.2)

**Detected by:** axe-core
**Element index:** 5

**Description:** Form input does not have an accessible name - The search input lacks a label or aria-label.

**Remediation hint:** Add a label element or aria-label attribute.

**Before:**
```html
<input type="search" placeholder="Search...">
```

**After:**
```html
<label for="search-input">Search</label>
<input type="search" id="search-input" placeholder="Search...">
```

**Or with aria-label:**
```html
<input type="search" placeholder="Search..." aria-label="Search website">
```

---

## Minor: Focus Visible (2.4.7)

**Detected by:** axe-core
**Element index:** 10

**Description:** Focus indicator not visible - The custom button styles remove the default focus outline without providing an alternative.

**Remediation hint:** Ensure focusable elements have a visible focus indicator.

**Before:**
```css
button.primary {
  outline: none;
  background: blue;
  color: white;
}
```

**After:**
```css
button.primary {
  outline: none;
  background: blue;
  color: white;
}

button.primary:focus {
  outline: 3px solid #ffcc00;
  outline-offset: 2px;
}
```

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Serious  | 0 |
| Moderate | 0 |
| Minor    | 1 |

Total violations: 3
