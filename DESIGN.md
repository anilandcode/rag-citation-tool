---
name: CiteRAG Olive Editorial
version: "alpha"
description: An evidence-first research product with an atmospheric olive homepage and a readable citation workspace.
colors:
  primary: "#263000"
  olive: "#263000"
  oliveMid: "#586B08"
  lime: "#CBE781"
  white: "#FFFFFF"
  warmSurface: "#F6F6F3"
  outerCanvas: "#EFEFF1"
  ink: "#171A13"
  footer: "#111411"
  muted: "#60645B"
  border: "#E2E5DC"
  supported: "#23633D"
  unsupported: "#A32929"
  warning: "#795000"
typography:
  hero: { fontFamily: Inter, fontSize: 7rem, fontWeight: 400, lineHeight: 0.95 }
  section: { fontFamily: Inter, fontSize: 3.75rem, fontWeight: 400, lineHeight: 1.05 }
  page: { fontFamily: Inter, fontSize: 2rem, fontWeight: 500, lineHeight: 1.15 }
  body: { fontFamily: Inter, fontSize: 1rem, fontWeight: 400, lineHeight: 1.6 }
  label: { fontFamily: Inter, fontSize: 0.75rem, fontWeight: 600, lineHeight: 1.4 }
rounded:
  control: 8px
  card: 9px
  stage: 14px
  pill: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  section: 104px
components:
  hero:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.white}"
  hero-glow:
    backgroundColor: "{colors.lime}"
  hero-summary:
    backgroundColor: "{colors.oliveMid}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
  marketing-canvas:
    backgroundColor: "{colors.outerCanvas}"
    textColor: "{colors.ink}"
  supporting-section:
    backgroundColor: "{colors.warmSurface}"
    textColor: "{colors.muted}"
  product-surface:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
  page-footer:
    backgroundColor: "{colors.footer}"
    textColor: "{colors.white}"
  hairline:
    backgroundColor: "{colors.border}"
  primary-action:
    backgroundColor: "{colors.olive}"
    textColor: "{colors.white}"
    rounded: "{rounded.pill}"
  citation-supported:
    textColor: "{colors.supported}"
  citation-unsupported:
    textColor: "{colors.unsupported}"
  data-warning:
    textColor: "{colors.warning}"
---

## Overview
CiteRAG answers questions about documents and shows the source evidence. The public homepage borrows the supplied olive reference's composition: a compact header, deep green geometric hero, controlled lime glow, three glass summaries, generous white sections, a dark olive process band, and near-black ending. The product remains a citation workspace, so its visual center is a labelled sample answer and evidence, not commerce imagery. The demo and app views use solid white document, conversation, form, and verification surfaces. Previous Evidence Lab direction is archived in `docs/design/evidence-lab-archive.md`.

## Colors
Deep olive `#263000` anchors the hero and process band. The lower glow transitions through `#586B08` toward `#CBE781`; text-bearing glass summaries maintain a darker tinted backing. `#FFFFFF` supports content and editable data. Warm `#F6F6F3` separates sections and `#EFEFF1` frames the marketing canvas on wide screens. Ink `#171A13` and muted `#60645B` carry ordinary text; `#E2E5DC` is the hairline divider. The near-black footer is `#111411`. Source support, unsupported claims, and warnings keep their separate semantic colors and explicit words. Green brand accent never substitutes for evidence status.

## Typography
Use the repository's Inter family with system fallback. The hero is regular weight, tight tracked, and deliberately two lines at wide widths; scale it from about 45px mobile to 112px wide desktop. Marketing section headings use 38–60px at 400–500 weight. Workspace page headings use 28–32px. Answers and body text stay 15–16px with comfortable line height; evidence identifiers and short labels use 11–13px. Keep filenames and URLs wrappable. Use tabular figures for any measured values and qualify their provenance.

## Layout
The public homepage is a centered canvas inside a pale gray 26px desktop frame and edge to edge below 760px. The navigation is a compact brand, centered capsule links, and white live-demo action; the mobile menu includes the demo link when the header action is hidden. Three linked hero summaries align in one row, stack on mobile, and describe actual sample corpus and workflow capabilities rather than invented usage. The white product showcase has three functional view buttons, a live explanation for each step, and a labelled sample answer stage. The selected pane comes first on narrow screens. Detailed content follows a white editorial rhythm, olive evidence-path band, capability tables, offer, FAQ, and dark final CTA/footer. The demo uses a three-panel document/conversation/verification layout that becomes a vertical sequence on small screens. The app places Corpus, Playground, Report, and Settings in a compact vertical rail at desktop widths and a horizontal tab row below 901px; the solid data surfaces remain unchanged. `/v1` and `/v2` remain clearly marked earlier concepts in the same palette.

## Elevation & Depth
Atmosphere belongs mainly to the hero: radial gradient, fine SVG grid/diagonal/circle geometry, and three olive-tinted translucent summary cards with blur. The product stage may use a soft shadow and layered white document panes. Ordinary workspace panels, uploads, evidence, tables, inputs, and dialogs stay solid. On browsers without blur support, hero summaries remain readable through their tinted fill. Use whitespace and borders for hierarchy elsewhere.

## Shapes
Action buttons and capsule navigation use full pills. Data cards use 8–9px corners, and the product stage 14px. Document, chat, citation, and verification items have restrained corners and fine borders. Decorative linework stays behind the hero content. Avoid repeated large translucent containers.

## Components
Shared elements: compact navigation, section label, primary/secondary action, hero summary, showcase view buttons, product stage, process path, evidence status, file row, citation tag, answer message, verification detail, upload zone, settings field, report block, FAQ, and footer. Buttons and inputs have visible keyboard focus, 44px touch targets where practical, disabled, busy, error, and recovery states. The sample report must say it does not measure uploaded files; the homepage sample answer and source are labelled. Tabs in the app preserve their existing keyboard behavior. Motion respects reduced-motion preference.

## Do's and Don'ts
Do show real CiteRAG files, answer paths, source names, and only reported evaluation results with linked provenance. Do make supported, unsupported, refusal, and offline states distinct. Do compare rendered spacing, headline wraps, glow contrast, and surface opacity against the supplied screenshot. Don't copy its brand, commerce imagery, testimonials, or growth claims. Don't present sample summaries as live counters. Don't place editable text on glass, obscure evidence with glow, or turn links into decorative dead controls. Keep API requests, demo keys, and response interpretation unchanged during this visual update.

## Stitch Guidance
Use `docs/design/olive-reference.png` for composition only: deep olive hero, lime lower glow, quiet geometric lines, three glass summaries, white editorial showcase, dark olive process band, and black ending. Translate every product image and claim into CiteRAG's own documents, grounded answers, citations, and verification. Use `assets/css/olive.css` for actual values and `docs/design/OLIVE-UX-SPEC.md` for page behavior. The reference is a static desktop image; mobile layouts are intentional adaptations.
