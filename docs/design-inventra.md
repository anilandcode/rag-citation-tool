# CiteRAG Design System - Inventra Rhythm Clone

**Source:** Inventra / Reevo-style SaaS landing (user screenshot 2026-08-15)  
**Product:** CiteRAG (citation-grounded RAG)  
**Mode:** Clone **layout + materials + section rhythm**. Original copy, product chrome, and brand mark.  
**Previous system:** archived as `design-cicada.md` (sage/forest CICADA language).  
**Dials:** VARIANCE 5 / MOTION 4 / DENSITY 5 (calm B2B SaaS, conversion-heavy).

**Reading this as:** B2B product landing for technical buyers who need measurable RAG accuracy, with a light neutral shell + single coral brand theater, sans-only type, product UI on color stages (not landscape photography).

---

## 1. Color tokens

| Token | Hex | Usage |
|---|---|---|
| `--bg` | `#F7F7F5` | Page canvas (soft off-white) |
| `--surface` | `#FFFFFF` | Cards, nav, logo strip, FAQ, pricing |
| `--surface-muted` | `#F3F3F1` | Nested mock panels, soft fills |
| `--ink` | `#141414` | Headlines, strong body |
| `--ink-2` | `#3A3A3C` | Secondary body |
| `--muted` | `#6B6B70` | Eyebrows, helpers, footer links |
| `--border` | `#E8E8E6` | Card outlines, dividers |
| `--border-strong` | `#DCDCD8` | Logo bar cells |
| `--brand` | `#F04A2B` | Primary CTA fill, accents, step markers, carousel controls |
| `--brand-deep` | `#C43A22` | Brand panel gradient low |
| `--brand-mid` | `#E85A3A` | Brand panel mid |
| `--brand-wash` | `#FCEDE8` | Soft peach wells, "Popular" pill bg |
| `--on-brand` | `#FFFFFF` | Text/icons on brand fills |
| `--success` | `#1F9D55` | Positive deltas in product UI only |
| `--danger` | `#D1453B` | Negative deltas / flags in product UI only |
| `--glass` | `rgba(255,255,255,0.88)` | Floating product cards on red stages |
| `--nav-dark` | `#1C1A17` | Dark pill in nav (Book / Demo) - high contrast, not brand red |

**Rules**
- One accent: coral. No purple, no sage canvas, no forest hero.
- Theme lock: **light only** for this clone (matches reference).
- Brand red stages carry product UI. White cards carry marketing copy.
- Do not invent fake green KPI numbers as company claims. Sample metrics must be labeled demo/sample.

---

## 2. Typography

**Stack (sans only - no display serif for this clone)**
- UI / marketing: **Satoshi** (Fontshare) or **Geist** fallback
- Mono for product chrome labels only: **JetBrains Mono** or system mono, 11-12px

| Role | Size (desktop) | Weight | LH | Notes |
|---|---|---|---|---|
| Logo | 18-20px | 600-700 | 1 | Wordmark + mark |
| Nav link | 14-15px | 400-500 | 1 | Muted ink |
| Eyebrow | 11-12px | 500-600 | 1.2 | Coral leading dot + short label |
| Hero H1 | 48-56px | 700 | 1.05-1.1 | Max 3 lines, period OK, tight tracking -0.02em |
| Section H2 | 36-44px | 700 | 1.1 | Often centered |
| Subhead | 16-18px | 400 | 1.55 | Muted, max ~36-40ch |
| Card title | 16-18px | 600 | 1.3 | |
| Stat numeral | 28-32px | 700 | 1 | Inside cards only |
| Body | 14-15px | 400 | 1.55 | |
| Button | 14-15px | 600 | 1 | Optional trailing `→` |
| Footer label | 11-12px | 600 | 1.2 | Slight tracking |
| Footer link | 13-14px | 400 | 1.4 | Muted |

**Banned for this system:** Newsreader/serif italics, Inter-as-default if Satoshi loads, gradient text, em dashes.

---

## 3. Spacing, radius, shadow

| Token | Value |
|---|---|
| `--container` | `min(1160px, calc(100% - 48px))` |
| `--section-y` | 80-96px |
| `--nav-h` | 64-72px |
| `--gap-card` | 16-24px |
| `--pad-card` | 20-28px |
| `--radius-btn` | 8-10px (rounded rect, not full pill) |
| `--radius-card` | 12-16px |
| `--radius-panel` | 16-20px (large red stages) |
| `--radius-chip` | 999px or 6-8px small |
| `--shadow-card` | `0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.06)` |
| `--shadow-float` | `0 12px 40px rgba(0,0,0,0.18)` (glass UI on red) |
| `--ease` | `cubic-bezier(0.32, 0.72, 0, 1)` |

Most surfaces = **flat + 1px border**. Shadow only lifts product glass and key cards.

---

## 4. Page structure (clone map)

Max width ~1160-1200. Light canvas. Section order matches reference rhythm:

| # | Block | Layout | CiteRAG content |
|---|---|---|---|
| 0 | Nav | Logo L · links C · Login-style secondary + dark primary R | CiteRAG · Product · How it works · Pricing? · Demo · **Start demo** / **Book audit** |
| 1 | Hero | 45/55 split: copy L, **brand red stage + glass product UI** R | H1 value prop + 2 CTAs + CiteRAG verify window |
| 2 | Value strip | Centered short claim + 3 micro icons | One line: measure answers before you ship |
| 3 | Logo / tools bar | 5 equal bordered cells | Tools only: LlamaIndex · FastAPI · Hybrid · RAGAS · Vercel (not fake customers) |
| 4 | Problem metrics | Eyebrow + H2 + **3 metric cards** | Hallucination / wrong cite / no score (honest framing, no fake %) |
| 5 | Platform stage | Full **red rounded panel**, copy L / UI R | Hybrid retrieve + verify path |
| 6 | Features intro | Centered H2 + sub | What CiteRAG does |
| 7 | Feature bento | 2 large cards w/ UI + 4 icon features | Retrieve, Verify, Refuse, Report |
| 8 | Pricing or offer | 3 cards OR single audit offer if no SaaS tiers | Free demo · Accuracy audit · Custom pipeline |
| 9 | Process | Full red split: copy L, **01 02 03** R | Audit · Fix · Leave |
| 10 | Social | 3 quote cards only if real; else omit or single founder note | Prefer omit over fake |
| 11 | FAQ | 2-col: title L, accordion R | Demo, data, pricing, API |
| 12 | Bottom CTA | Full red band, headline L, dual buttons R | Start demo + Book audit |
| 13 | Footer | 4 cols + legal bar | Product · Demo · Company · Contact |

---

## 5. Components

### Nav
- White bar, hairline bottom border
- Left: monogram mark in coral or ink + **CiteRAG**
- Center links muted
- Right: light secondary pill + **dark** primary pill (reference uses dark for nav demo, coral for in-page primary)

### Buttons
- **Primary brand:** `--brand` fill, white text, radius 8-10, optional `→`
- **Secondary:** white/light gray, ink text, 1px border
- **Dark:** `--nav-dark` fill (nav + high-contrast)
- Height 40-44px, font 600

### Eyebrow
- Coral disc (6-7px) + short label, 11-12px, medium weight
- Max ~1 per 3 sections (do not spam)

### Hero
- Left: eyebrow → H1 (2-3 lines) → sub ≤20 words → dual CTAs
- Right: large red textured/grain panel (`--brand-mid` → `--brand-deep`), radius 16-20
- Floating white glass card: CiteRAG product (docs list + answer + verify 2/2)
- **No lifestyle photo.** Brand color stage + UI (reference pattern)

### Metric cards (3-up)
- White, border, radius 12-16, icon well in peach, title, short body
- Avoid fake precision stats unless labeled SAMPLE

### Red platform panel
- Full-bleed inside container, padding 32-40
- Left white text on red; right glass UI stack

### Feature cards
- 2 large white cards with nested muted mock charts/UI
- 4-up icon row: tinted well + title + one line

### Process steps
- Red panel; right column rows `01` `02` `03` with hairline dividers in lighter red

### FAQ
- Accordion chevrons; one open by default optional

### Footer
- White; 4 columns; bottom legal row

---

## 6. Product UI chrome (on red stages)

Dark-free **white glass** panels (reference is light UI on red):
- Card bg white ~88-95% opacity feel (solid white OK if blur weak)
- Title 13-14px semibold
- Rows 12-13px muted
- Status chips: green "verified", coral "flagged"
- Sample content only from demo corpus (refund-policy, terms-2026)

Do **not** generate fake browser OS chrome with Inventra branding.

---

## 7. Imagery strategy

| Asset | How |
|---|---|
| Red stage texture | CSS gradient + optional subtle noise PNG (no people) |
| Product UI | Real HTML components (preferred) or honest screenshot of `/demo` |
| Charts in feature cards | Simple CSS/SVG bars - CiteRAG themed (faithfulness, citation rate) |
| Avatars / customer logos | **Omit** unless real |
| OG image | Composite: red panel + CiteRAG wordmark + one UI card |

Image model optional for abstract grain/noise only. Primary "visual" is **brand stage + product UI**, matching the reference.

---

## 8. Motion

- Intensity 4: soft hover on buttons (`scale 0.98` active), accordion, optional fade-up on sections once
- No marquee, no scroll hijack, no magnetic cursors
- Honor `prefers-reduced-motion`

---

## 9. Content voice (CiteRAG)

**Hero draft**
- Eyebrow: `Citation-grounded RAG`
- H1: `Know which answers you can defend.`
- Sub: `Hybrid retrieve, verify every claim, refuse when the docs do not say.`
- CTAs: `Start demo` · `Book an audit`

**Do not claim:** SSO live, 18k users, invented % lifts. Demo metrics labeled sample.

---

## 10. Clone vs do-not-clone

| Clone | Do not clone |
|---|---|
| Section order and grids | Inventra / Reevo name, logo, copy |
| Coral + light neutral tokens | Their chart data and customer quotes |
| Red stage + glass UI pattern | Fake retail inventory metaphors |
| Nav / pricing / FAQ / CTA band structure | Their exact radii if they fight a11y |
| Sans-only hierarchy | Purple AI gradients, sage CICADA sheet |

---

## 11. Stack constraints (this repo)

- Static HTML/CSS on Vercel (current CiteRAG site)
- Keep `/demo` `/app` `/v1` `/v2` routes
- Homepage replace only after snapshot if needed
- Form: mailto `hello@anilpervaiz.com` (no auto-send)

---

## 12. CSS variable starter

```css
:root {
  --bg: #F7F7F5;
  --surface: #FFFFFF;
  --surface-muted: #F3F3F1;
  --ink: #141414;
  --ink-2: #3A3A3C;
  --muted: #6B6B70;
  --border: #E8E8E6;
  --brand: #F04A2B;
  --brand-deep: #C43A22;
  --brand-mid: #E85A3A;
  --brand-wash: #FCEDE8;
  --on-brand: #FFFFFF;
  --nav-dark: #1C1A17;
  --success: #1F9D55;
  --radius-btn: 10px;
  --radius-card: 14px;
  --radius-panel: 18px;
  --container: min(1160px, calc(100% - 48px));
  --nav-h: 68px;
  --section-y: 88px;
  --shadow-card: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06);
  --shadow-float: 0 12px 40px rgba(0,0,0,.18);
  --ease: cubic-bezier(0.32, 0.72, 0, 1);
  --font: "Satoshi", system-ui, sans-serif;
}
```

---

## 13. Acceptance checklist

- [ ] Light canvas + coral only accent
- [ ] Hero split with red stage + CiteRAG glass UI
- [ ] No fake customers / quotes / invented SaaS metrics
- [ ] Start demo → `/demo`; Book audit → real mailto form
- [ ] Tools bar, not logo wall of fake brands
- [ ] Process 01-03 on red panel
- [ ] FAQ + bottom red CTA band + 4-col footer
- [ ] Zero em dashes; zero Inter-default if Satoshi loads
- [ ] Mobile: single column; nav collapses
- [ ] `/v1` CICADA and `/v2` experimental remain reachable
