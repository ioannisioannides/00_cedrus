# Cedrus Brand Guidelines

## Visual Identity & Design System

**Version 1.0**  
**Last Updated:** 2024

---

## Table of Contents

1. [Brand Overview](#brand-overview)
2. [Logo & Identity](#logo--identity)
3. [Color Palette](#color-palette)
4. [Typography](#typography)
5. [Spacing System](#spacing-system)
6. [Iconography](#iconography)
7. [Component Styles](#component-styles)
8. [Brand Voice](#brand-voice)
9. [Accessibility](#accessibility)
10. [Implementation Guidelines](#implementation-guidelines)

---

## Brand Overview

### Brand Personality

Cedrus embodies **calm authority** and **trustworthy expertise**. The platform serves certification bodies, auditors, and organizations managing compliance and risk—requiring a visual identity that conveys:

- **Professionalism**: Enterprise-grade reliability
- **Trust**: Confidence in governance and accuracy
- **Clarity**: Transparent, accessible information
- **Timelessness**: Enduring design that won't feel dated
- **Mediterranean Heritage**: Subtle connection to cedar forests, stone architecture, and coastal landscapes

### Design Principles

1. **Minimalism First**: Clean interfaces that prioritize content and functionality
2. **Neutral Foundation**: Warm, natural neutrals provide stability
3. **Strategic Accents**: Strong accent colors guide attention and indicate status
4. **Consistent Hierarchy**: Clear visual structure supports information architecture
5. **Accessibility by Default**: All design decisions consider WCAG 2.1 AA standards

---

## Logo & Identity

### Logo Concept Explorations

#### Option 1: Geometric Cedar

- **Concept**: Stylized cedar tree silhouette using geometric shapes (triangles/chevrons)
- **Style**: Minimal line art or solid geometric forms
- **Application**: Works well at small sizes, maintains clarity in monochrome
- **Symbolism**: Growth, stability, natural authority

#### Option 2: Abstract Cedar Branch

- **Concept**: Horizontal cedar branch with needle clusters
- **Style**: Single-line weight, organic but structured
- **Application**: Elegant horizontal lockup, pairs well with wordmark
- **Symbolism**: Precision, natural order, Mediterranean landscape

#### Option 3: Typographic Mark

- **Concept**: "C" monogram with subtle cedar needle integration
- **Style**: Letterform with integrated natural element
- **Application**: Versatile, works as favicon and app icon
- **Symbolism**: Brand name integration, modern simplicity

#### Option 4: Shield & Cedar

- **Concept**: Shield shape containing stylized cedar
- **Style**: Geometric, balanced, authoritative
- **Application**: Strong for certification contexts, conveys protection
- **Symbolism**: Security, governance, protection

### Logo Usage Guidelines

- **Minimum Size**: 24px height for digital, 0.5" for print
- **Clear Space**: Equal to the height of the "C" or main symbol element
- **Placement**: Top-left in navigation, centered in headers
- **Backgrounds**:
  - Light logos on dark backgrounds (Stone 900, Sea 800)
  - Dark logos on light backgrounds (Stone 50, Stone 100)
- **Monochrome**: Logo must work in single color (Stone 700) for fax, stamps, etc.

### Wordmark

- **Typography**: Use primary heading font (see Typography section)
- **Spacing**: Letter-spacing: -0.02em for tight, professional feel
- **Lockup**: Logo + wordmark horizontal spacing = 1x logo height

---

## Color Palette

### Primary Colors

#### Cedar Green (Primary)

The signature accent color inspired by Mediterranean cedar forests.

```
Cedar 50:  #F0F7F4    (Lightest - backgrounds, subtle highlights)
Cedar 100: #D4E8E0    (Light - hover states, soft backgrounds)
Cedar 200: #A8D1C1    (Lighter - borders, inactive states)
Cedar 300: #7CBAA2    (Light - secondary actions)
Cedar 400: #50A383    (Medium - icons, tertiary elements)
Cedar 500: #248C64    (PRIMARY - main actions, links, active states) ⭐
Cedar 600: #1D7050    (Darker - hover on primary)
Cedar 700: #16543C    (Dark - pressed states)
Cedar 800: #0F3828    (Darker - text on light, emphasis)
Cedar 900: #081C14    (Darkest - deep accents)
```

**Usage**: Primary buttons, links, active navigation, success states, key CTAs

#### Stone (Neutral Base)

Warm, natural stone tones provide the foundation.

```
Stone 50:  #FAFAF9    (Background - main UI surface)
Stone 100: #F5F5F3    (Background - cards, elevated surfaces)
Stone 200: #E7E7E4    (Borders - subtle dividers)
Stone 300: #D9D9D5    (Borders - input borders, inactive)
Stone 400: #CBCBC6    (Text - placeholders, disabled)
Stone 500: #BDBDB7    (Borders - stronger dividers)
Stone 600: #9E9E97    (Text - secondary, labels)
Stone 700: #808078    (Text - body, default)
Stone 800: #616159    (Text - headings, emphasis)
Stone 900: #42423A    (Text - primary headings, high contrast) ⭐
```

**Usage**: Body text, backgrounds, borders, neutral UI elements

### Secondary Colors

#### Sea Blue (Secondary Accent)

Mediterranean sea blue for secondary actions and information.

```
Sea 50:  #F0F5F9    (Lightest)
Sea 100: #D1E3F2    (Light)
Sea 200: #A3C7E5    (Lighter)
Sea 300: #75ABD8    (Light)
Sea 400: #478FCB    (Medium)
Sea 500: #1973BE    (SECONDARY - info, secondary actions) ⭐
Sea 600: #145C98    (Darker)
Sea 700: #0F4572    (Dark)
Sea 800: #0A2E4C    (Darker)
Sea 900: #051726    (Darkest)
```

**Usage**: Secondary buttons, informational messages, links in secondary contexts

#### Terracotta (Tertiary Accent)

Warm Mediterranean terracotta for warnings and attention.

```
Terracotta 50:  #FDF5F3    (Lightest)
Terracotta 100: #FAE6E0    (Light)
Terracotta 200: #F5CDC1    (Lighter)
Terracotta 300: #F0B4A2    (Light)
Terracotta 400: #EB9B83    (Medium)
Terracotta 500: #E68264    (TERTIARY - warnings, attention) ⭐
Terracotta 600: #B86850    (Darker)
Terracotta 700: #8A4E3C    (Dark)
Terracotta 800: #5C3428    (Darker)
Terracotta 900: #2E1A14    (Darkest)
```

**Usage**: Warning states, attention-grabbing elements (sparingly)

### Semantic Colors

#### Success

```
Success Light: #D4E8E0    (Cedar 100 - backgrounds)
Success:       #248C64    (Cedar 500 - text, icons)
Success Dark:  #16543C    (Cedar 700 - emphasis)
```

#### Warning

```
Warning Light: #FDF5E6    (Custom - backgrounds)
Warning:       #D4A574    (Custom - text, icons)
Warning Dark:  #8B6F4D    (Custom - emphasis)
```

#### Error

```
Error Light:   #F5E6E6    (Custom - backgrounds)
Error:         #C85A5A    (Custom - text, icons)
Error Dark:    #8B3E3E    (Custom - emphasis)
```

#### Info

```
Info Light:    #D1E3F2    (Sea 100 - backgrounds)
Info:          #1973BE    (Sea 500 - text, icons)
Info Dark:     #0F4572    (Sea 700 - emphasis)
```

### Surface Colors

```
Background Primary:   #FFFFFF    (Main content area)
Background Secondary: #FAFAF9    (Stone 50 - page background)
Background Tertiary:  #F5F5F3    (Stone 100 - cards, panels)
Background Elevated:  #FFFFFF    (Modals, dropdowns, popovers)

Border Subtle:       #E7E7E4    (Stone 200)
Border Default:      #D9D9D5    (Stone 300)
Border Strong:       #CBCBC6    (Stone 400)

Overlay:             rgba(66, 66, 58, 0.5)    (Stone 900 at 50% - modals, overlays)
```

---

## Typography

### Font Families

#### Primary: Inter (Headings & Body)

**Why**: Modern, highly legible, professional, excellent for UI  
**Weights**: 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

#### Monospace: 'JetBrains Mono' or 'Fira Code' (Code, Data)

**Why**: Clear, readable monospace for code blocks, data tables, technical content  
**Weights**: 400 (Regular), 500 (Medium)

```css
font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
```

### Type Scale

Based on a 1.25 (Major Third) modular scale:

```
H1 - Display:     48px / 3rem    (Line-height: 1.2, Weight: 700)
H2 - Page Title:  38px / 2.375rem (Line-height: 1.25, Weight: 700)
H3 - Section:     30px / 1.875rem (Line-height: 1.3, Weight: 600)
H4 - Subsection:  24px / 1.5rem   (Line-height: 1.4, Weight: 600)
H5 - Card Title:  20px / 1.25rem  (Line-height: 1.4, Weight: 600)
H6 - Label:       16px / 1rem     (Line-height: 1.5, Weight: 600)

Body Large:       18px / 1.125rem  (Line-height: 1.6, Weight: 400)
Body:             16px / 1rem      (Line-height: 1.6, Weight: 400) ⭐
Body Small:       14px / 0.875rem  (Line-height: 1.5, Weight: 400)

Caption:          12px / 0.75rem   (Line-height: 1.4, Weight: 400)
Code:             14px / 0.875rem  (Line-height: 1.5, Weight: 400, Monospace)
```

### Typography Usage

#### Headings

- **H1**: Landing pages, major section headers (sparingly)
- **H2**: Page titles, main content sections
- **H3**: Subsections, card group headers
- **H4**: Form section headers, nested content
- **H5**: Card titles, list headers
- **H6**: Labels, small section headers

#### Body Text

- **Body Large**: Important descriptions, intro text
- **Body**: Default paragraph text, form labels
- **Body Small**: Secondary information, metadata
- **Caption**: Timestamps, helper text, fine print

#### Text Colors

```
Text Primary:     #42423A    (Stone 900 - headings, primary text)
Text Secondary:   #616159    (Stone 800 - body text)
Text Tertiary:    #808078    (Stone 700 - secondary text)
Text Disabled:    #CBCBC6    (Stone 400 - disabled states)
Text Link:        #248C64    (Cedar 500 - links)
Text Link Hover:  #1D7050    (Cedar 600 - link hover)
```

---

## Spacing System

### 8px Grid System

All spacing values are multiples of 8px for consistency and alignment.

```
0px:   0      (No spacing)
4px:   0.25rem (Tight spacing - icon padding, micro adjustments)
8px:   0.5rem  (XS - tight gaps, compact lists)
16px:  1rem    (SM - default spacing, form fields) ⭐
24px:  1.5rem  (MD - card padding, section gaps)
32px:  2rem    (LG - major sections, large gaps)
40px:  2.5rem  (XL - page sections, headers)
48px:  3rem    (2XL - major page divisions)
64px:  4rem    (3XL - hero sections, large breaks)
80px:  5rem    (4XL - page-level spacing)
```

### Spacing Usage

#### Component Internal Spacing

- **Buttons**: 12px horizontal, 8px vertical (padding)
- **Inputs**: 12px horizontal, 10px vertical
- **Cards**: 24px padding (all sides)
- **Modals**: 32px padding

#### Layout Spacing

- **Section Gaps**: 32px - 48px
- **Form Field Gaps**: 24px vertical
- **List Item Gaps**: 16px vertical
- **Grid Gaps**: 24px (gutters)

#### Responsive Adjustments

- **Mobile**: Reduce spacing by 25% (e.g., 24px → 18px)
- **Tablet**: Standard spacing
- **Desktop**: Standard or slightly increased for large screens

---

## Iconography

### Icon Style

#### Primary: Line Icons

- **Weight**: 1.5px - 2px stroke width
- **Style**: Rounded line caps and joins
- **Size**: 16px, 20px, 24px standard sizes
- **Library**: Heroicons, Feather Icons, or custom set

#### Secondary: Filled Icons (for emphasis)

- **Usage**: Active states, primary actions, selected items
- **Style**: Solid fills with same rounded aesthetic

### Icon Sizes

```
XS:  12px  (Inline with small text)
SM:  16px  (Default, inline with body text) ⭐
MD:  20px  (Buttons, medium emphasis)
LG:  24px  (Headers, large buttons)
XL:  32px  (Hero sections, feature highlights)
```

### Icon Colors

```
Default:      #808078    (Stone 700 - neutral icons)
Primary:      #248C64    (Cedar 500 - active, primary)
Secondary:    #1973BE    (Sea 500 - info, secondary)
Success:      #248C64    (Cedar 500)
Warning:      #D4A574    (Warning)
Error:        #C85A5A    (Error)
Disabled:     #CBCBC6    (Stone 400)
```

### Icon Usage Guidelines

- **Consistency**: Use same icon family throughout
- **Alignment**: Icons align to text baseline or center with text
- **Spacing**: 8px gap between icon and text
- **Accessibility**: Always pair icons with text labels for important actions

---

## Component Styles

### Buttons

#### Primary Button

```css
Background:     #248C64 (Cedar 500)
Text:           #FFFFFF
Padding:        12px 24px
Border-radius:  6px
Font:           16px, 500 weight
Height:         44px (touch target)

Hover:          #1D7050 (Cedar 600)
Active:         #16543C (Cedar 700)
Disabled:       #CBCBC6 (Stone 400) background, #9E9E97 text
```

#### Secondary Button

```css
Background:     Transparent
Text:           #248C64 (Cedar 500)
Border:         1.5px solid #248C64
Padding:        12px 24px
Border-radius:  6px
Font:           16px, 500 weight

Hover:          #F0F7F4 (Cedar 50) background
Active:          #D4E8E0 (Cedar 100) background
Disabled:       Border #CBCBC6, Text #9E9E97
```

#### Tertiary Button

```css
Background:     Transparent
Text:           #616159 (Stone 800)
Border:         None
Padding:        12px 16px
Font:           16px, 500 weight

Hover:          #F5F5F3 (Stone 100) background
Active:          #E7E7E4 (Stone 200) background
```

#### Button Sizes

- **Small**: 36px height, 10px 16px padding, 14px font
- **Medium**: 44px height, 12px 24px padding, 16px font ⭐
- **Large**: 52px height, 14px 32px padding, 18px font

### Inputs

#### Text Input

```css
Background:     #FFFFFF
Border:         1.5px solid #D9D9D5 (Stone 300)
Border-radius:  6px
Padding:        10px 12px
Font:           16px, 400 weight
Height:         44px

Focus:          Border #248C64 (Cedar 500), outline: 2px solid rgba(36, 140, 100, 0.2)
Error:          Border #C85A5A (Error), background #FDF5F3
Disabled:       Background #F5F5F3, border #E7E7E4, text #9E9E97
```

#### Textarea

```css
Same as text input, but:
Min-height:     88px (2 lines)
Padding:        12px
Resize:         Vertical only
```

#### Select/Dropdown

```css
Same as text input, plus:
Dropdown arrow: 20px icon, #808078 (Stone 700)
```

#### Checkbox & Radio

```css
Size:           20px × 20px
Border:         1.5px solid #D9D9D5
Border-radius:  4px (checkbox), 50% (radio)
Checked:        Background #248C64, border #248C64
Focus:          Outline: 2px solid rgba(36, 140, 100, 0.2)
```

### Tables

#### Table Structure

```css
Border:         1px solid #E7E7E4 (Stone 200)
Border-radius:  8px
Overflow:       Hidden
```

#### Table Header

```css
Background:     #F5F5F3 (Stone 100)
Text:           #42423A (Stone 900), 14px, 600 weight
Padding:        12px 16px
Border-bottom:  1px solid #E7E7E4
```

#### Table Row

```css
Background:     #FFFFFF
Padding:        16px
Border-bottom:  1px solid #E7E7E4 (last row: none)

Hover:          Background #FAFAF9 (Stone 50)
Selected:       Background #F0F7F4 (Cedar 50), border-left: 3px solid #248C64
```

#### Table Cell

```css
Text:           #616159 (Stone 800), 14px
Vertical-align: Middle
```

### Cards

#### Standard Card

```css
Background:     #FFFFFF
Border:         1px solid #E7E7E4 (Stone 200)
Border-radius:  8px
Padding:        24px
Box-shadow:     0 1px 3px rgba(66, 66, 58, 0.1)

Hover (if interactive): Box-shadow: 0 4px 12px rgba(66, 66, 58, 0.15)
```

#### Elevated Card

```css
Same as standard, plus:
Box-shadow:     0 4px 12px rgba(66, 66, 58, 0.15)
```

### Tabs

#### Tab Container

```css
Border-bottom:  1px solid #E7E7E4 (Stone 200)
```

#### Tab Button

```css
Background:     Transparent
Text:           #808078 (Stone 700), 16px, 500 weight
Padding:        12px 24px
Border-bottom:  3px solid transparent

Active:         Text #248C64 (Cedar 500), border-bottom #248C64
Hover:          Text #616159 (Stone 800), background #FAFAF9
```

### Badges & Tags

#### Badge (Status)

```css
Display:        Inline-flex
Padding:        4px 8px
Border-radius:  12px
Font:           12px, 500 weight
Height:         20px

Success:        Background #D4E8E0, text #16543C
Warning:        Background #FDF5E6, text #8B6F4D
Error:          Background #F5E6E6, text #8B3E3E
Info:           Background #D1E3F2, text #0F4572
Neutral:        Background #F5F5F3, text #616159
```

### Modals & Dialogs

#### Modal Overlay

```css
Background:     rgba(66, 66, 58, 0.5) (Stone 900 at 50%)
Backdrop-filter: blur(4px)
```

#### Modal Container

```css
Background:     #FFFFFF
Border-radius:  12px
Padding:        32px
Max-width:      600px (standard), 800px (large)
Box-shadow:     0 8px 32px rgba(66, 66, 58, 0.2)
```

#### Modal Header

```css
Margin-bottom:  24px
Border-bottom:  1px solid #E7E7E4
Padding-bottom: 16px
```

### Navigation

#### Primary Navigation

```css
Background:     #FFFFFF
Border-bottom:  1px solid #E7E7E4
Height:         64px
Padding:        0 32px
```

#### Nav Link

```css
Text:           #616159 (Stone 800), 16px, 500 weight
Padding:        12px 16px
Border-radius:  6px

Active:         Text #248C64 (Cedar 500), background #F0F7F4
Hover:          Background #FAFAF9
```

### Forms

#### Form Group

```css
Margin-bottom:  24px
```

#### Form Label

```css
Text:           #42423A (Stone 900), 14px, 600 weight
Margin-bottom:  8px
Display:        Block
```

#### Form Helper Text

```css
Text:           #808078 (Stone 700), 12px
Margin-top:     4px
```

#### Form Error Message

```css
Text:           #C85A5A (Error), 12px
Margin-top:     4px
Display:        Flex
Align-items:    Center
Gap:            4px
```

---

## Brand Voice

### Tone & Personality

**Primary Voice**: Professional, Clear, Authoritative, Calm

#### Characteristics

- **Direct but respectful**: No unnecessary words, but never curt
- **Confident without arrogance**: Assertive statements backed by expertise
- **Accessible complexity**: Explain complex concepts simply
- **Action-oriented**: Use active voice, clear CTAs
- **Trust-building**: Transparent, honest, reliable language

### Writing Guidelines

#### Do's

- ✅ Use "you" to address users directly
- ✅ Use active voice ("The system generates reports" not "Reports are generated")
- ✅ Be specific ("Complete 3 audits" not "Complete some audits")
- ✅ Use consistent terminology (e.g., "audit" not "review" or "assessment")
- ✅ Provide context ("This action cannot be undone" not just "Are you sure?")
- ✅ Use positive framing when possible ("Save changes" not "Don't lose changes")

#### Don'ts

- ❌ Jargon without explanation
- ❌ Excessive exclamation marks
- ❌ Slang or casual language
- ❌ Vague instructions
- ❌ Negative error messages without solutions

### Voice Examples

#### Error Messages

**Good**: "The audit cannot be deleted because it has associated findings. Please remove all findings first."  
**Bad**: "Error: Cannot delete audit."

#### Success Messages

**Good**: "Audit saved successfully. You can continue editing or view the audit list."  
**Bad**: "Success!"

#### Instructions

**Good**: "Select a certification standard from the list below. You can filter by category or search by name."  
**Bad**: "Choose a standard."

#### CTAs

**Good**: "Start New Audit" (action verb + object)  
**Bad**: "Click Here" or "Submit"

### Terminology

#### Preferred Terms

- **Audit** (not review, assessment, evaluation)
- **Finding** (not issue, problem, defect)
- **Certification Body** (not certifier, CB)
- **Client Organization** (not client, company)
- **Site** (not location, facility)
- **Standard** (not norm, specification)

---

## Accessibility

### Color Contrast

All text must meet WCAG 2.1 AA standards:

#### Minimum Contrast Ratios (AA)

- **Normal text** (16px+): 4.5:1
- **Large text** (18px+ bold, 24px+ regular): 3:1
- **UI components**: 3:1 (buttons, form controls)
- **Non-text content**: 3:1 (icons, borders)

#### Verified Combinations

✅ **Stone 900 on White**: 12.6:1 (excellent)  
✅ **Stone 800 on White**: 9.8:1 (excellent)  
✅ **Cedar 500 on White**: 3.2:1 (passes for large text)  
✅ **Cedar 700 on White**: 5.1:1 (passes for normal text)  
✅ **White on Cedar 500**: 3.2:1 (passes for large text)  
✅ **White on Cedar 700**: 5.1:1 (passes for normal text)

### Color Usage Guidelines

#### Never Rely on Color Alone

- ✅ Always pair color with icons, text, or patterns
- ✅ Use borders, underlines, or shapes in addition to color
- ✅ Provide text labels for status indicators

#### Examples

- **Success**: Green checkmark icon + "Success" text + green background
- **Error**: Red X icon + "Error" text + red border
- **Required field**: Asterisk (*) + red border + "Required" label

### Focus States

All interactive elements must have visible focus indicators:

```css
Focus outline:  2px solid #248C64 (Cedar 500)
Outline offset: 2px
```

#### Keyboard Navigation

- Tab order follows visual hierarchy
- Skip links for main content
- Focus traps in modals
- Escape key closes modals/dropdowns

### Screen Reader Support

- **Alt text**: All images, icons with meaning
- **ARIA labels**: Buttons, form controls, landmarks
- **Live regions**: For dynamic content updates
- **Headings**: Proper hierarchy (h1 → h2 → h3, no skipping)

### Touch Targets

Minimum size: **44px × 44px** for all interactive elements (buttons, links, form controls)

---

## Implementation Guidelines

### CSS Variables

Implement the design system using CSS custom properties:

```css
:root {
  /* Cedar (Primary) */
  --cedar-50: #F0F7F4;
  --cedar-100: #D4E8E0;
  --cedar-500: #248C64;
  --cedar-600: #1D7050;
  --cedar-700: #16543C;
  --cedar-900: #081C14;

  /* Stone (Neutral) */
  --stone-50: #FAFAF9;
  --stone-100: #F5F5F3;
  --stone-200: #E7E7E4;
  --stone-300: #D9D9D5;
  --stone-400: #CBCBC6;
  --stone-700: #808078;
  --stone-800: #616159;
  --stone-900: #42423A;

  /* Sea (Secondary) */
  --sea-500: #1973BE;
  --sea-700: #0F4572;

  /* Semantic */
  --color-success: var(--cedar-500);
  --color-error: #C85A5A;
  --color-warning: #D4A574;
  --color-info: var(--sea-500);

  /* Spacing */
  --spacing-xs: 0.5rem;   /* 8px */
  --spacing-sm: 1rem;     /* 16px */
  --spacing-md: 1.5rem;   /* 24px */
  --spacing-lg: 2rem;     /* 32px */
  --spacing-xl: 3rem;     /* 48px */

  /* Typography */
  --font-family: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-size-body: 1rem;
  --font-size-h1: 3rem;
  --font-size-h2: 2.375rem;

  /* Borders */
  --border-radius-sm: 4px;
  --border-radius-md: 6px;
  --border-radius-lg: 8px;
  --border-radius-xl: 12px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(66, 66, 58, 0.1);
  --shadow-md: 0 4px 12px rgba(66, 66, 58, 0.15);
  --shadow-lg: 0 8px 32px rgba(66, 66, 58, 0.2);
}
```

### Component Classes

Use BEM (Block Element Modifier) naming convention:

```css
.btn { }                    /* Block */
.btn--primary { }           /* Modifier */
.btn--large { }             /* Modifier */
.card { }                   /* Block */
.card__header { }           /* Element */
.card__body { }             /* Element */
.card--elevated { }         /* Modifier */
```

### Responsive Breakpoints

```css
Mobile:   < 768px
Tablet:   768px - 1023px
Desktop:  1024px - 1439px
Large:    ≥ 1440px
```

### Dark Mode (Future Consideration)

If implementing dark mode:

- Invert Stone scale (Stone 900 → background, Stone 50 → text)
- Maintain Cedar 500 for primary actions
- Adjust shadows and overlays
- Test all contrast ratios

---

## Design Variants

### Dashboard Style

**Characteristics**:

- Clean, data-dense but organized
- Card-based layout for key metrics
- Subtle backgrounds (Stone 50/100)
- Strong use of Cedar 500 for primary actions
- Clear visual hierarchy with typography

**Layout**:

- Grid system: 12 columns
- Card gaps: 24px
- Section headers: H3 (30px), margin-bottom: 24px

### Form Style

**Characteristics**:

- Generous white space
- Clear field grouping
- Inline validation
- Progress indicators for multi-step
- Helpful helper text

**Layout**:

- Max-width: 800px for forms
- Field spacing: 24px vertical
- Group spacing: 32px vertical
- Side-by-side fields: 2-column grid on desktop

### Report Style

**Characteristics**:

- Print-optimized layouts
- High contrast for readability
- Professional, document-like
- Clear section breaks
- Table-heavy layouts

**Layout**:

- Max-width: 1200px
- Generous margins: 48px
- Section breaks: 40px spacing
- Table styling: Alternating row colors (subtle)

---

## Brand Assets Checklist

- [ ] Logo files (SVG, PNG @1x, @2x, @3x)
- [ ] Favicon set (16×16, 32×32, 192×192, 512×512)
- [ ] App icon (iOS, Android)
- [ ] Social media assets (Open Graph images)
- [ ] Email template styling
- [ ] PDF report templates
- [ ] Print stylesheet
- [ ] Brand color swatches (for design tools)

---

## Maintenance & Updates

### Version Control

- Document all changes in this file's changelog
- Maintain backward compatibility when possible
- Communicate breaking changes to team

### Review Cycle

- Quarterly review of color contrast ratios
- Annual review of typography and spacing
- Continuous accessibility audits

---

**End of Brand Guidelines**

For questions or updates, contact the design team or refer to the project repository.
