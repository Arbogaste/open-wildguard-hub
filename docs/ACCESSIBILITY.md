# Accessibility Standard & Checklist (WCAG 2.1)

> **The standard is W3C WCAG.** This document is the project's accessibility reference: what the rule
> is, why it matters, and exactly how to satisfy it in our HTML pages. Goal = **AA conformance, no
> regression**, written so a volunteer can apply it without an a11y degree.
>
> Authoritative sources (read these for depth):
> - W3C — Web Content Accessibility Guidelines (WCAG) 2.1: https://www.w3.org/TR/WCAG21/
> - W3C WAI — standards/guidelines overview: https://www.w3.org/WAI/standards-guidelines/wcag/
> - EU — accessibility standard (EN 301 549, which adopts WCAG): https://digital-strategy.ec.europa.eu/en/policies/latest-changes-accessibility-standard
> - Material Design — Accessibility (usability + writing): https://m2.material.io/design/usability/accessibility.html
> - Inclusion beyond compliance (UX mindset): https://medium.com/design-bootcamp/embracing-accessibility-in-ux-design-beyond-compliance-to-inclusion-d60a5bb2b091
> - India UXDT — Understanding UX / Accessibility: https://www.uxdt.nic.in/guidelines/understanding-ux/accessibility/

---

## 1. The frame: POUR + conformance levels

WCAG is organized under four principles. If content fails any one, someone is locked out.

| Principle | Plain meaning | Fails when… |
|-----------|---------------|-------------|
| **Perceivable** | Users can sense the content (sight, sound, touch) | image has no alt; text contrast too low; video has no captions |
| **Operable** | Users can drive the UI (keyboard, not just mouse) | control unreachable by Tab; time limit can't be extended |
| **Understandable** | Content + behavior is predictable | jargon-only labels; errors with no guidance; layout jumps |
| **Robust** | Works across browsers + assistive tech | broken/invalid HTML; custom widget with no ARIA roles |

**Conformance levels:** **A** (must), **AA** (the real-world target, and what EN 301 549 / most laws
require), **AAA** (aspirational, not required site-wide). **We target AA.**

**Beyond compliance:** AA is the floor, not the goal. Accessibility *is* usability — captions help in
noisy fields, high contrast helps in sunlight, keyboard support helps power users. Design for the
range of human ability, permanent and situational (a ranger with one hand on a radio is "temporarily
one-handed"). Compliance is the checkbox; **inclusion is the intent.**

---

## 2. The AA checklist (apply to every page)

Grouped by principle. ★ = the ones our pages most often get wrong.

### Perceivable
- [ ] ★ **1.1.1 Non-text content (A):** every `<img>` has `alt`. Decorative? `alt=""` +
      `aria-hidden="true"` (we use this on Font Awesome icons).
- [ ] **1.2.x Media (A/AA):** video has captions; audio has a transcript.
- [ ] ★ **1.3.1 Info & relationships (A):** use real semantics — `<header> <nav> <main> <footer>`,
      `<h1>`→`<h2>`→`<h3>` in order (no skipping), `<ul>`/`<ol>` for lists, `<table>` for tabular data
      with `<th>`. Don't fake structure with `<div>`+CSS.
- [ ] **1.3.5 Input purpose (AA):** inputs use correct `type` + `autocomplete` where relevant.
- [ ] ★ **1.4.3 Contrast (AA):** text ≥ **4.5:1** vs background (≥ **3:1** for large/bold ≥24px or
      ≥18.66px bold). UI components & focus indicators ≥ 3:1 (1.4.11).
- [ ] ★ **1.4.4 Resize text (AA):** readable at 200% zoom, no loss of content. Use relative units.
- [ ] **1.4.10 Reflow (AA):** no horizontal scroll at 320px width / 400% zoom — content reflows.
- [ ] **1.4.12 Text spacing (AA):** layout survives increased line/letter/word spacing.

### Operable
- [ ] ★ **2.1.1 Keyboard (A):** everything works with Tab/Shift+Tab/Enter/Space/arrows. No
      mouse-only controls.
- [ ] **2.1.2 No keyboard trap (A):** focus can always leave a component.
- [ ] ★ **2.4.1 Bypass blocks (A):** a "Skip to content" link as the first focusable element.
- [ ] **2.4.2 Page titled (A):** unique, descriptive `<title>`.
- [ ] ★ **2.4.3 Focus order (A):** Tab order follows visual/reading order.
- [ ] **2.4.4 Link purpose (A):** link text makes sense alone (not "click here").
- [ ] ★ **2.4.7 Focus visible (AA):** a clear focus ring (`:focus-visible`). Never `outline:none`
      without a replacement.
- [ ] **2.5.3 Label in name (A):** the accessible name contains the visible label text.
- [ ] **2.5.5 Target size:** tap targets comfortably ≥ 44×44 px (AAA in 2.1; treat as a mobile must).
- [ ] **2.3.1 Three flashes (A):** nothing flashes > 3×/sec.
- [ ] **2.2.x Timing:** no surprise time limits; respect `prefers-reduced-motion` for animation.

### Understandable
- [ ] ★ **3.1.1 Language of page (A):** `<html lang="…">` set correctly (it/en per page).
- [ ] **3.2.1 / 3.2.2 On focus/input (A):** focusing or typing doesn't trigger an unexpected context
      change (no auto-navigation, no surprise popups).
- [ ] **3.2.3 Consistent navigation (AA):** nav in the same place across pages.
- [ ] ★ **3.3.1 Error identification (A):** errors are described in text, not color alone.
- [ ] **3.3.2 Labels/instructions (A):** every input has a visible `<label>` (or `aria-label`).
- [ ] **Writing (Material):** plain language, short sentences, action-first labels. Don't rely on
      color/shape alone to convey meaning (1.4.1) — pair with text/icons.

### Robust
- [ ] ★ **4.1.2 Name, role, value (A):** custom widgets (tabs, dialogs, toggles) expose proper roles
      and states. Our tabs use `role="tab"`/`role="tablist"`/`aria-selected`/`aria-controls`.
- [ ] **4.1.3 Status messages (AA):** dynamic updates announced via `aria-live` / `role="status"`
      without moving focus.
- [ ] **Valid HTML:** no duplicate `id`, properly nested/closed tags.

---

## 3. Copy-paste patterns we use

```html
<!-- Skip link (first focusable element) -->
<a class="skip" href="#content">Skip to content</a>
<style>.skip{position:absolute;left:-999px}.skip:focus{left:0}</style>

<!-- Visible focus, never remove without replacing -->
<style>a:focus-visible,button:focus-visible{outline:3px solid #00ff66;outline-offset:2px}</style>

<!-- Decorative icon: hide from screen readers -->
<i class="fa-solid fa-book-open" aria-hidden="true"></i> Read README

<!-- Icon-only button: give it a name -->
<button aria-label="Close dialog"><i class="fa fa-xmark" aria-hidden="true"></i></button>

<!-- Accessible tab (pattern already in index.html) -->
<button role="tab" aria-selected="true" aria-controls="panel-1" id="tab-1">Overview</button>
<div role="tabpanel" aria-labelledby="tab-1" id="panel-1"> … </div>

<!-- Live region for async updates (e.g. "Lead found") -->
<div role="status" aria-live="polite"></div>

<!-- Respect reduced motion -->
<style>@media (prefers-reduced-motion:reduce){*{animation:none!important;scroll-behavior:auto}}</style>
```

---

## 4. How to test (cheap → thorough)

1. **Keyboard only:** unplug the mouse. Tab through the whole page. Can you reach + use everything?
   Is the focus ring always visible? Can you escape every popup?
2. **Zoom:** browser zoom to 200% and 400%. Anything cut off or overlapping? (1.4.4 / 1.4.10)
3. **Contrast:** check text colors with any contrast checker (WebAIM) — target ≥ 4.5:1.
4. **Automated scan:** run **axe DevTools** or **Lighthouse** (Chrome DevTools → Accessibility).
   Fix every "serious"/"critical". (Automated tools catch ~30–40% — keyboard + screen reader catch
   the rest.)
5. **Screen reader pass:** NVDA (Win, free) / VoiceOver (Mac, ⌘F5). Does each control announce a
   sensible name + role + state?
6. **Mobile:** real phone or device emulation. Tap targets ≥ 44px, no horizontal scroll, no hover-only
   actions.

---

## 5. "No regression" rule

Before shipping any HTML change: run the keyboard pass + Lighthouse a11y score, and **do not let the
score drop**. New interactive elements ship *with* their semantics (label, role, focus style), not as
a follow-up. A feature that isn't accessible isn't done.

---

## 6. Current status of our pages (self-audit)

| Item | index.html | scriptplay.html | readme.html |
|------|:---:|:---:|:---:|
| `lang` set | ✅ it | ✅ en | ✅ en |
| Unique `<title>` + meta description | ✅ | ✅ | ✅ |
| Semantic landmarks (`main`/`footer`/`nav`) | ✅ | partial | ✅ |
| Skip link | ⬜ add | ⬜ add | ✅ |
| Visible focus (`:focus-visible`) | ✅ | ✅ | ✅ |
| Accessible tabs (role/aria) | ✅ | ✅ | n/a |
| Icons `aria-hidden` | partial | partial | ✅ |
| Reduced-motion respected | ⬜ check | ⬜ check | ✅ |
| Reflow at 320px | ✅ (media queries) | ✅ | ✅ |

**Next a11y tasks:** add a skip link to `index.html` + `scriptplay.html`; sweep remaining icons for
`aria-hidden`; add `@media (prefers-reduced-motion)`; run Lighthouse and record the baseline score.
