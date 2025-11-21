# Cedrus Brand Quick Reference

**Quick lookup guide for the Cedrus design system**

---

## 🎨 Primary Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Cedar 500** | `#248C64` | Primary buttons, links, active states |
| **Cedar 600** | `#1D7050` | Hover states on primary |
| **Cedar 700** | `#16543C` | Pressed/active states |

## 🏛️ Neutral Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Stone 900** | `#42423A` | Headings, primary text |
| **Stone 800** | `#616159` | Body text |
| **Stone 700** | `#808078` | Secondary text, icons |
| **Stone 200** | `#E7E7E4` | Borders, dividers |
| **Stone 100** | `#F5F5F3` | Card backgrounds |
| **Stone 50** | `#FAFAF9` | Page background |

## 🌊 Secondary Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Sea 500** | `#1973BE` | Secondary buttons, info |
| **Terracotta 500** | `#E68264` | Warnings (sparingly) |

## ✅ Semantic Colors

- **Success**: `#248C64` (Cedar 500)
- **Error**: `#C85A5A`
- **Warning**: `#D4A574`
- **Info**: `#1973BE` (Sea 500)

## 📝 Typography

**Font**: Inter  
**Body**: 16px (1rem), 400 weight, 1.6 line-height  
**H1**: 48px (3rem), 700 weight  
**H2**: 38px (2.375rem), 700 weight  
**H3**: 30px (1.875rem), 600 weight

## 📏 Spacing (8px Grid)

- **XS**: 8px (0.5rem)
- **SM**: 16px (1rem) ← Default
- **MD**: 24px (1.5rem)
- **LG**: 32px (2rem)
- **XL**: 48px (3rem)

## 🔘 Buttons

**Primary**

- Background: `#248C64`
- Text: White
- Padding: `12px 24px`
- Height: `44px`
- Border-radius: `6px`

**Secondary**

- Background: Transparent
- Text: `#248C64`
- Border: `1.5px solid #248C64`

## 📦 Cards

- Background: White
- Border: `1px solid #E7E7E4`
- Border-radius: `8px`
- Padding: `24px`
- Shadow: `0 1px 3px rgba(66, 66, 58, 0.1)`

## 📋 Forms

**Input**

- Height: `44px`
- Border: `1.5px solid #D9D9D5`
- Border-radius: `6px`
- Padding: `10px 12px`
- Focus: Border `#248C64` + outline

## 🎯 CSS Variables

Import `cedrus-brand.css` and use:

```css
color: var(--cedar-500);
background: var(--stone-50);
padding: var(--spacing-4);
font-size: var(--font-size-body);
```

## ♿ Accessibility

- **Minimum contrast**: 4.5:1 for normal text
- **Touch targets**: Minimum 44px × 44px
- **Focus**: 2px solid `#248C64` outline
- **Never rely on color alone** - use icons/text

## 📱 Breakpoints

- Mobile: `< 768px`
- Tablet: `768px - 1023px`
- Desktop: `≥ 1024px`

---

**Full details**: See `BRAND_GUIDELINES.md`
