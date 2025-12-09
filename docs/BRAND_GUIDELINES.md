# Cedrus Design System: "Apex Horizon" (IBM Plex Edition)

**Version 2.1 (The "Accessibility" Update)**
**Philosophy:** "Man & Machine"

---

## 1. The Vision
We are building the **operating system for truth**.
Multinationals are jealous because their tools are clunky, grey, and bureaucratic. Cedrus is sharp, fast, and beautiful. It feels like a high-performance cockpit.

**Core Attributes:**
*   **Functional:** Design is a tool, not decoration.
*   **Accessible:** WCAG 2.1 AAA Compliance is mandatory. High contrast is non-negotiable.
*   **Engineered:** Every pixel is calculated.

---

## 2. Color System: "Void & Photon" (AAA Tuned)

We use a high-contrast palette inspired by the IBM Carbon Design System.

### Dark Mode (Default)
*   **Void 950 (Main BG):** `#09090B` (Deep Obsidian)
*   **Void 900 (Card BG):** `#161616` (Carbon Gray 100)
*   **Text Primary:** `#F4F4F4` (Contrast ~16:1)
*   **Action:** `#0F62FE` (IBM Blue 60)

### Light Mode (Auto-Switch)
*   **Background:** `#F4F4F4`
*   **Card BG:** `#FFFFFF`
*   **Text Primary:** `#161616` (Contrast ~19:1)

---

## 3. Typography: "Man & Machine"

We use **IBM Plex**, a typeface designed to capture the relationship between mankind and machine.

*   **UI Font:** **IBM Plex Sans**. Grotesque, neutral, yet friendly. It replaces Open Sans/Inter to provide a more "engineered" feel.
*   **Data/Code Font:** **IBM Plex Mono**. A monospaced font with excellent legibility for audit codes and financial data.

**Hierarchy:**
*   **H1:** 36px/1.25, Regular (Light weights for large text)
*   **Body:** 16px/1.5, Regular
*   **Labels:** 12px/1.5, Regular

---

## 4. The Grid Layout

*   **Gap:** 16px or 24px fixed.
*   **Radius:** `4px` (Sharp, precise).
*   **Borders:** Explicit 1px borders for high contrast separation.

---

## 5. Accessibility Standards

*   **Contrast:** All text must meet WCAG AAA (7:1) for normal text.
*   **Focus:** High-visibility focus rings (`2px solid #FFFFFF` in dark mode).
*   **Motion:** Respect `prefers-reduced-motion`.

---

## 6. Implementation Notes

```css
:root {
  --font-ui: 'IBM Plex Sans', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
  --action-primary: #0F62FE;
}
```
