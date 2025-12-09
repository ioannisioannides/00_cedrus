# Cedrus Design System: "Apex Horizon"

**Version 2.0 (The "Envy" Update)**
**Philosophy:** "Governance at the Speed of Light"

---

## 1. The Vision
We are not building a "compliance tool." We are building the **operating system for truth**.
Multinationals are jealous because their tools are clunky, grey, and bureaucratic. Cedrus is sharp, fast, and beautiful. It feels like a high-performance sports car, not a filing cabinet.

**Core Attributes:**
*   **Kinetic:** The interface feels alive. It reacts instantly.
*   **Lucid:** Complex data is rendered with absolute clarity.
*   **Premium:** Every pixel is intentional. No default browser styles.
*   **Dark Mode Native:** The default state is a deep, sophisticated dark mode (easier on the eyes for long audit sessions), with a "Paper" light mode for formal reporting.

---

## 2. Color System: "Void & Photon"

We move away from "earthy" tones to a high-contrast, digital-first palette.

### The Canvas (Backgrounds)
*   **Void 900 (Main BG):** `#09090B` (Almost black, slightly warm)
*   **Void 800 (Surface):** `#18181B` (Card background)
*   **Void 700 (Border):** `#27272A` (Subtle separation)

### The Signal (Accents)
*   **Photon Blue (Primary):** `#3B82F6` -> `#60A5FA` (Gradient) - *Action, Focus*
*   **Cyber Teal (Success):** `#10B981` - *Compliance, Pass*
*   **Plasma Orange (Warning):** `#F59E0B` - *Risk, Attention*
*   **Crimson Laser (Critical):** `#EF4444` - *Non-conformance, Danger*

### The Text
*   **Primary:** `#FAFAFA` (White, softened)
*   **Secondary:** `#A1A1AA` (Muted grey for metadata)
*   **Tertiary:** `#52525B` (Subtle labels)

---

## 3. Typography: "Swiss Engineering"

We use a pairing that suggests absolute precision.

*   **UI Font:** **Inter** (or *Geist Sans*). Variable weight. Tight tracking (-0.02em) for headings to feel "locked in."
*   **Data/Code Font:** **JetBrains Mono** or **Geist Mono**. Used for IDs, audit codes, timestamps, and financial figures.

**Hierarchy:**
*   **Display:** 48px/1.1, Bold, Tracking -0.04em (Hero headers)
*   **H1:** 32px/1.2, SemiBold, Tracking -0.03em
*   **H2:** 24px/1.3, Medium, Tracking -0.02em
*   **Body:** 16px/1.5, Regular
*   **Caption:** 12px/1.5, Medium, Uppercase, Wide Tracking (Labels)

---

## 4. The "Bento" Grid Layout

Everything lives in cards.
*   **Gap:** 16px or 24px fixed.
*   **Radius:** `12px` (Smooth, modern).
*   **Borders:** 1px solid `Void 700`.
*   **Shadows:** None by default. `0 4px 20px rgba(0,0,0,0.5)` on hover/lift.

---

## 5. Glassmorphism & Depth

We use subtle transparency to create hierarchy without clutter.
*   **Overlays/Modals:** `rgba(9, 9, 11, 0.7)` with `backdrop-filter: blur(12px)`.
*   **Sticky Headers:** Semi-transparent to let content scroll "under" the controls.

---

## 6. Micro-Interactions

*   **Buttons:** Scale down 98% on click. Glow on hover.
*   **Transitions:** All state changes (hover, focus, modal open) happen over `200ms cubic-bezier(0.16, 1, 0.3, 1)` (The "Apple" ease).
*   **Loading:** No spinners. Skeleton screens with a shimmering "flux" effect.

---

## 7. Data Visualization

Charts are not boring Excel exports. They are HUDs (Heads-Up Displays).
*   **Lines:** Thin, glowing strokes (2px width + 4px blur shadow).
*   **Areas:** Gradients fading to transparent.
*   **Tooltips:** Dark glass, instant appearance.

---

## 8. Implementation Notes (Tailwind/CSS Variables)

```css
:root {
  --bg-app: #09090B;
  --bg-card: #18181B;
  --border-subtle: #27272A;
  --text-primary: #FAFAFA;
  --text-muted: #A1A1AA;
  --accent-glow: 0 0 20px rgba(59, 130, 246, 0.5);
}
```
