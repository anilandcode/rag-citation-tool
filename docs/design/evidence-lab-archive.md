# CiteRAG — Evidence Lab design system

Status: proposed implementation specification. This planning change does not redesign or deploy the live pages.
Date: 2026-09-28 (Asia/Karachi).
Audited baseline: `2e4a019108d5a3b712c5eaa26fc99c73defd0fac`.
Implementation sequence: [docs/redesign-plan.md](docs/redesign-plan.md).

## 1. Brief and scope

Upgrade every existing public page and workspace view into one coherent, polished interface. Preserve CiteRAG's identity, citation-grounded answers, existing API contracts, demo behavior, and audit contact flow. The work is visual design, information hierarchy, responsive layout, and accessible interaction polish. It is not a backend rewrite or a new SaaS business model.

“Google Labs standard” is the user's quality direction: experimental, clear, purposeful, fast, and carefully finished. This is an original CiteRAG system, not an official Google specification, extracted Google token set, or claim of affiliation.

### Evidence reviewed

- Repository: <https://github.com/anilandcode/rag-citation-tool>.
- Live homepage, demo, and all four app tabs inspected in the browser.
- User reference video opened, played, and scrubbed in the browser: <https://cdn.dribbble.com/userupload/48910934/file/7e37dc6cfdccaa9004c5a3eedf683998.mp4>. Media duration reported as approximately 69 seconds.
- Reference frames show HERON AI branding, architectural drawings, a warm paper canvas, fine construction lines, bold uppercase headings, orange callouts, a product dashboard, a geometric CTA illustration, and a structured footer with an oversized outlined wordmark.
- Exact font names, color values, timing curves, and spacing are not recoverable from visual inspection. All numerical tokens below are proposed values, not measured reference tokens.
- Repository contains no `AGENTS.md` at this baseline. Its previous `docs/design-inventra.md` describes a coral design that differs from the current sage/landscape homepage. This document supersedes that guide for the new redesign; the older guide remains historical context.

## 2. Art direction

**Concept: a laboratory for evidence.** Documents become the visual architecture. A claim, its source, and its verification occupy aligned cells on a precise, quiet canvas.

| Reference characteristic | CiteRAG translation |
| --- | --- |
| Off-white architectural presentation | Warm paper surfaces with black text and restrained grid lines |
| Orange annotations on drawings | Source markers, active navigation, focused actions, claim callouts |
| Bold editorial headings | Short, confident headings with generous whitespace |
| Monochrome structural rendering | Original document-stack illustration or real product composition |
| Thin grid and registration marks | Section boundaries, numbered stages, small decorative crosshairs |
| Product windows inside the showcase | Real, accessible HTML preview of answer and evidence |
| Structured footer and outline lettering | Useful footer navigation with a subtle CiteRAG wordmark treatment |

Do not reproduce HERON's logo, architecture product copy, screenshots, customer claims, or monitor enclosure. The desktop monitor and outer mountains belong to the presentation video, not to the site's page layout. Keep CiteRAG useful at normal browser size.

### Visual priorities

1. Evidence and primary action are immediately legible.
2. Typography and grid establish character before decoration.
3. Orange occupies roughly 5–10% of a typical screen; status colors retain separate meanings.
4. App surfaces are calmer and denser than marketing sections.
5. Every apparent control has working behavior. Every displayed metric has a source or sample label.

## 3. Complete surface inventory

| Route/view | Current implementation | Redesign responsibility |
| --- | --- | --- |
| `/` | `index.html`; sage sheet, landscape scenes, marketing tables | New editorial homepage, product-led hero, clear capability and offer sections |
| `/demo` | `demo.html`; documents/chat/verification | Shared lab shell, clear starting action, improved answer/evidence hierarchy |
| `/app` → Corpus | `app.html`; upload and index counts | Accessible upload zone, file queue, status and recovery states |
| `/app` → Playground | Same file; three-pane query interface | Same answer/evidence vocabulary as demo, corpus-specific empty states |
| `/app` → Report | Same file; static sample report | Deliberately labeled sample report with readable comparisons |
| `/app` → Settings | Same file; API URL/key and unfinished theme control | Proper form labels, grouping, save feedback, clear connection state |
| `/v1` | `v1/index.html`; original marketing concept | Restyle all sections with shared tokens; mark as legacy concept; clarify unshipped claims |
| `/v2` | `v2/index.html`; editorial audit page and mailto form | Restyle using shared system; retain audit form and validation |

No new login, billing, organizations, document viewer service, analytics dashboard, or report-generation API is implied. The app tabs remain views within `/app`; adding deep links is optional and must not alter API behavior. Preserve existing routes and meaningful anchors.

## 4. Design tokens

### Color

| Token | Value | Use |
| --- | --- | --- |
| `--canvas` | `#F6F5F0` | Global warm paper background |
| `--surface` | `#FFFFFF` | Inputs and elevated content |
| `--surface-subtle` | `#EEEDE7` | Nested panels and hover fills |
| `--ink` | `#20231F` | Headings and body text |
| `--ink-secondary` | `#51564D` | Supporting copy |
| `--ink-muted` | `#666B62` | Metadata, never disabled by color alone |
| `--line` | `#D8DAD2` | Decorative grids and panel dividers |
| `--line-control` | `#858B7F` | Essential input/control outlines |
| `--accent` | `#F4511E` | Orange annotation fill with dark text |
| `--accent-strong` | `#B8320C` | Orange text links; white-text orange buttons if needed |
| `--accent-wash` | `#FFF0E8` | Active row and citation background |
| `--inverse` | `#FAFAF7` | Text on ink backgrounds |
| `--success` / `--success-wash` | `#23633D` / `#EAF4EC` | Supported evidence |
| `--warning` / `--warning-wash` | `#795000` / `#FFF3D6` | Uncertainty, sample data, offline mode |
| `--danger` / `--danger-wash` | `#A32929` / `#FDECEC` | Unsupported claim or failed action |
| `--focus` | `#245BC1` | Consistent keyboard focus ring |

Use ink text on bright orange; white text on ink for the default primary button. Reserve orange for emphasis, not every button. Do not use pale divider color as the sole boundary of an essential input. Validate final pairings at WCAG AA: 4.5:1 for normal text, 3:1 for large text and essential graphical/control boundaries. Decorative construction lines are exempt from carrying information.

### Typography

Use existing **Inter** to avoid an unnecessary font migration; `system-ui, sans-serif` fallback. Use `ui-monospace, SFMono-Regular, Consolas, monospace` for source identifiers and small technical labels. No proprietary Google font dependency.

| Role | Desktop | Mobile | Weight / line height |
| --- | --- | --- | --- |
| Hero | 72–88px fluid | 40–48px fluid | 600–650 / 0.98–1.06 |
| Section title | 40–48px | 30–36px | 600 / 1.1 |
| App page title | 28–32px | 24–28px | 600 / 1.2 |
| Card title | 20–24px | 20px | 600 / 1.25 |
| Lead paragraph | 18px | 17px | 400 / 1.6 |
| Body and answers | 16px | 16px | 400 / 1.6 |
| UI label/button | 14px | 14–16px | 500–600 / 1.4 |
| Source metadata | 12–13px | 12–13px | 400–500 / 1.5 |

Hero tracking: `-0.045em`; headings: `-0.025em`; body: normal. Uppercase is for short display headlines or short labels only, never answer paragraphs. Keep prose near 60–72 characters per line. Source filenames wrap with `overflow-wrap:anywhere`; long names must not widen the page. Input text remains at least 16px on mobile.

### Space, shape, and elevation

- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 96, 128px.
- Marketing max width: 1280px; side gutters: 48px large, 32px medium, 20px small.
- App max width: 1600px with 24px desktop and 16px mobile gutters; app content may fill the viewport.
- Section padding: 96px desktop, 64px tablet, 48px mobile.
- Marketing grid: 12 columns; tablet: 8; mobile: 4. Align section borders to the same container edges.
- Radii: 0px for editorial grid cells, 4px for chips, 8px for inputs/buttons, 12px for modal/panel surfaces. Avoid the current large rounded outer sheet.
- Border: 1px. Active tab underline: 2px. Focus ring: 3px with 3px offset.
- Shadows: none on ordinary grid cells; floating evidence preview `0 12px 36px rgb(32 35 31 / 10%)`; small popover `0 4px 16px rgb(32 35 31 / 12%)`.
- Icon size: 18–20px, consistent 1.5–2px stroke; use one inline SVG family. Decorative icons are hidden from assistive technology. Replace emoji placeholders in product UI.

### Responsive composition

| Width | Marketing | Demo/playground |
| --- | --- | --- |
| ≥1200px | Full editorial grid, split hero | Sources 240px / answer flexible ≥400px / evidence 320px |
| 900–1199px | Smaller split layouts | Sources in disclosure; answer + evidence columns |
| 600–899px | Primarily stacked | Answer first; sources and evidence in labeled expandable sections |
| <600px | One column, 20px gutters | One document flow; compact source disclosure, answer, evidence; no hidden essential data |

Use content-driven overrides where a layout becomes cramped. Test at 360, 390, 768, 1024, and 1440px, and at 200% zoom. The composer must not cover answer text, evidence controls, or the mobile keyboard area. Prefer a flexible viewport shell using `min-height` and `100dvh` enhancement over fixed panel heights.

## 5. Shared components and interaction rules

| Component | Anatomy | Required behavior |
| --- | --- | --- |
| Site header | CiteRAG mark/name, Product, How it works, Evidence, Demo, primary CTA | Current page indicated; mobile menu button exposes expanded state and closes on Escape |
| App header | Brand, Demo/Workspace label, connection status, navigation links | Connection status contains words, not only a dot |
| Primary button | Ink fill, white label, optional arrow | 44px minimum target, hover/focus/pressed/loading/disabled states |
| Secondary button | Paper or white surface, visible outline | Same target and keyboard treatment as primary |
| Text link | Underline or other non-color distinction in prose | Descriptive destination; visible focus |
| Section header | Small index, title, optional brief lead | Correct heading hierarchy; numbering decorative |
| Document row | File icon, filename, indexed status | Selection style only when selection actually works |
| Citation control | Source filename, optional real page, evidence marker | Keyboard action reveals/focuses matching evidence; never invent page numbers |
| Evidence card | Verdict label/icon, source, claim, source excerpt, optional confidence | Supported/unsupported/unknown distinguishable without color; disclosure for long evidence |
| Metric tile | Label, value, units, provenance | Unknown is an em dash with explanation; sample badge above sample values |
| Status banner | Icon, message, recovery action | `role=status` for routine updates; alert for actionable failure |
| FAQ | Native `details` / `summary` | Keyboard and touch support with no custom focus trap |
| Tabs | Corpus, Playground, Report, Settings | Tab/tabpanel associations, roving tabindex, arrow keys, Home/End, selected state |
| Form field | Visible label, input, helper, inline error | `for`/`id`, `aria-describedby`, meaningful input type, retained input on error |

### Truthful evidence display

Preserve values and meaning from the existing response schema: `answer`, `citations`, `verification`, optional `gate`, optional `evaluation`. In verification retain `supported`, `source_text`, nullable `confidence`, `engine`, `decision_cost`, and route metadata when provided.

- Support confidence is not overall model accuracy. Label it “Claim support confidence.”
- A refusal is a neutral, useful result: “No supported answer found in these documents.” It is not a red system failure or a 0% accuracy score.
- Missing verification is “Not verified,” never automatically green.
- Render page labels only for actual page values; preserve existing handling of `N/A`, null, and empty values.
- Gate route, complexity, engine, and cost belong in a collapsed “Decision details” section. Keep them available to technical users without crowding the answer.
- A source excerpt is available in `verification.details[].source_text`; a full document viewer is not assumed.
- Keep the explicit offline transcript label and explain that it is pre-recorded. Never make it look like a live response.
- Sample pricing and subscription statements in `data/demo/` are fictional demo corpus content, not actual commercial offers.

## 6. Homepage structure and content

The page should establish what CiteRAG does, show evidence, and offer two useful next actions. Keep the technical detail available further down the page.

| Order | Section | Layout and content |
| --- | --- | --- |
| 1 | Header | Thin bordered navigation; CiteRAG left; primary “Try the demo” right |
| 2 | Hero | Eyebrow “Citation-grounded AI”; headline “ANSWERS, WITH EVIDENCE.”; lead “Ask your documents. Inspect the sources. See which claims are supported.”; primary “Try the demo”; secondary “Explore the workspace” |
| 3 | Evidence stage | Wide document/answer/source composition, readable HTML text, orange annotation linking claim to source; label “Sample answer” |
| 4 | Capability strip | Four compact cells: Hybrid retrieval / Source citations / Claim verification / Honest refusal |
| 5 | How it works | Three numbered columns: Connect documents / Ask a question / Inspect the evidence |
| 6 | Product showcase | Answer and source excerpt side by side; title “Follow every claim to its source.”; second state shows a clear refusal |
| 7 | Evaluation and decisions | Real report context or explicitly sample metrics; concise provenance; link to relevant repository report |
| 8 | Capabilities and limits | Existing production/scale tables reorganized into shipped / configurable / custom-work labels; keep precise details in disclosures |
| 9 | Work with CiteRAG | Free public demo, accuracy audit, custom pipeline; no invented subscription tiers |
| 10 | FAQ | Two-column introduction and accessible accordion; explain demo data, verification, deployment dependencies, and audit process |
| 11 | Final CTA | “PUT YOUR ANSWERS TO THE TEST.”; Try the demo / Book an audit; restrained document illustration |
| 12 | Footer | Product / Resources / Contact, existing real links, optional outlined CiteRAG lettering |

Primary links: `/demo`; workspace link: `/app`; audit link: existing `mailto:hello@anilpervaiz.com?subject=CiteRAG%20audit`. Preserve the existing creator attribution and repository destination. Legacy routes move to the footer as labeled previous concepts.

Hero source example: `refund-policy.md`, with the actual 30-day refund statement from the demo corpus. Omit an invented PDF page. The composition can show “Source excerpt” rather than simulated verification percentages. Marketing illustrations must not look like live telemetry.

Use original CSS/SVG linework for the document illustration first. A monochrome raster artwork can add atmosphere later, but the illustration is not required to understand or operate the product.

## 7. Demo specification

Header: CiteRAG / Live demo, text-based API status, “Open workspace,” “Back to site.” Below it, a small introduction: “Ask a question. Check the evidence.”

Desktop columns:

1. **Sources:** indexed files, sample loader when necessary, five existing preset questions. Use document rows with clear filename wrapping.
2. **Answer:** focused empty state and suggestions, readable conversation history, composer anchored within the column, labeled send button.
3. **Evidence:** verification summary, source cards, source excerpt disclosure, decision details.

State matrix:

| State | Visible treatment | Action |
| --- | --- | --- |
| Checking connection | Neutral label “Checking connection” | Avoid flashing an error before health resolves |
| No sample docs | Short explanation and Load sample documents button | Existing seed action only on user request |
| Ready, no question | Useful sample prompt and blank evidence description | Preset or user input |
| Asking | Busy text, disabled duplicate submit, preserved question | No simulated stage percentages |
| Answer with support | Answer and inline citations; supported evidence cards | Inspect source excerpt |
| Mixed support | Explicit supported/unsupported labels | Inspect each claim |
| Refusal | Neutral refusal explanation and source scope | Ask a different question |
| API unavailable | Non-blocking banner with recovery information | Existing offline transcript link |
| Offline transcript | Persistent “Offline preview” label | Retry live connection without implying fresh output |
| Empty/malformed fields | Safe fallbacks and neutral status | Never fabricate metrics or sources |

Keyboard: Enter submits, Shift+Enter inserts a line break. Do not intercept composition/IME Enter. Provide a visible label for the textarea. Async updates use a concise live status region; avoid re-announcing the entire conversation on each change.

## 8. Workspace specification

### Corpus

- Page title “Your document corpus”; brief explanation of supported file types.
- Two-column desktop layout: upload/queue at left, index summary at right. Stack on mobile.
- Upload zone includes a real labeled file input/button, drag-over state, file type hint, queued file rows, file sizes, and accessible remove controls.
- No guessed file-size limit. Show only limits enforced by the existing service.
- Use the existing ingest action and its response fields. Loading text is “Indexing documents…” with no invented progress percentage.
- Index summary distinguishes unknown values from zero. Do not fabricate document lists from sample filenames when real source data is absent.
- Success has a clear route into Playground. Failure retains the queue for retry and points to connection settings where appropriate.

### Playground

Reuse demo answer/evidence patterns, but use the user's indexed corpus and existing query call. With no corpus, present “Add documents to start asking questions” and a button that selects Corpus. Preserve query history while changing visual tabs during the session. Do not add persistence or fabricated saved chats.

### Report

The current view is a hardcoded sample. Put “Sample report” above the title and repeat sample context adjacent to the baseline/optimized values. Use aligned 0.72 and 0.94 sample faithfulness values, neutral comparison labels, readable metric descriptions, and the existing improvements list. Do not imply these are measured on the user's upload. Do not add working-looking Generate/Export buttons without implemented behavior. Connecting a real report endpoint is separate scope.

### Settings

Use a narrow form (maximum 640px): Connection heading, API base URL, masked API key, helper text, Save settings, current connection status. Keep the API key in session storage as implemented; never display it in status output. Label inputs properly. Indicate saving success with a status region, and distinguish “Saved” from “Connected.” Remove or disable the misleading selectable “Dark (coming soon)” option; this design release is light-theme only. Do not promise theme persistence that does not exist.

## 9. Older routes

The user requested all pages, so `/v1` and `/v2` are explicit work items, not forgotten leftovers.

- `/v1`: apply shared tokens, typography, grid, buttons, FAQ, footer, and mobile navigation. Preserve its useful section content. Add a small “Previous concept” banner with a current-site link. Mark unshipped enterprise features as conceptual, and remove or explicitly label unsupported testimonials/metrics. Keep legacy anchor destinations valid.
- `/v2`: preserve its audit-led editorial structure; align visual styles, image treatment, form, buttons, FAQ, and footer. Keep the name/email/company/problem fields and existing mail-client handoff. Clearly say that submission opens the user's email app and sends nothing automatically.
- Preserve version images as repository history. Do not delete them as part of visual cleanup.
- A route must not show a half-migrated mix of green, coral, and new orange styles.

## 10. Motion and assets

Motion should clarify relationships: a selected citation brings its evidence into view; a disclosure reveals detail; a button acknowledges input.

| Motion | Duration | Rule |
| --- | --- | --- |
| Color/border hover | 120–160ms | No geometry shift |
| Panel/disclosure | 180–240ms | Use opacity or small translation; preserve keyboard focus |
| Marketing entrance | 300–420ms | Optional, once only, 8–12px maximum movement |
| Hero annotation | 400–600ms | Optional one-time emphasis; never continuous required reading motion |

Ease: `cubic-bezier(.2,.7,.2,1)`. Honor reduced motion: remove translation, entrance effects, smooth scrolling, and decorative animation. Content must remain visible when JavaScript is absent. No scroll hijacking, cursor replacement, mandatory WebGL, or autoplay background video.

Asset plan:

- `assets/design/`: optional original document-stack art and optimized derivatives.
- UI icons, annotations, and exact diagrams: SVG/HTML/CSS, not generated raster text.
- If image generation is useful: monochrome paper/document architecture, warm white background, soft graphite shading, one orange annotation area, no lettering, no logos. Add readable labels in HTML.
- Decorative image: empty alt; informative image: concise descriptive alt. Always supply dimensions/aspect ratio. Use responsive AVIF/WebP where practical; lazy-load below-fold art. Do not lazy-load the LCP image.
- Target optional hero image ≤250KB at typical desktop delivery size; target marketing initial transfer ≤700KB excluding cache effects. These are budgets, not current measured results.

## 11. Implementation organization

Keep the static HTML architecture. Shared CSS provides consistency without requiring a framework migration.

```text
assets/css/tokens.css       semantic tokens and typography
assets/css/base.css         reset, focus, accessibility, core elements
assets/css/components.css   buttons, fields, tabs, status, source/evidence cards
assets/css/marketing.css    homepage and legacy editorial layouts
assets/css/workspace.css    demo and app layouts
assets/js/ui.js             small navigation/tab/disclosure helpers if needed
assets/design/              original optional visual assets
index.html                 homepage markup and content
demo.html                  demo markup and existing rendering logic
app.html                   workspace markup and existing API behavior
v1/index.html              previous concept, restyled
v2/index.html              audit page, restyled
```

Use root-relative shared asset paths so `/v1` and `/v2` resolve them correctly. Remove migrated conflicting inline styles rather than accumulating high-specificity overrides. Keep `assets/config.js`, API destinations, auth headers, escaping, and backend files unchanged unless a separately justified frontend compatibility fix is necessary.

Preserve demo renderer function names and DOM anchors used by `tests/ui/demo_render_test.js`. That harness currently extracts the largest inline script; moving that script requires adapting the harness as part of the same implementation change. Prefer retaining renderer placement during the first visual pass.

## 12. Acceptance criteria

- [ ] All five routes and four workspace tabs follow this system.
- [ ] Desktop hero visibly reflects the reference's grid, paper, monochrome, and annotation vocabulary.
- [ ] Primary task is obvious on the homepage, demo, and every app tab.
- [ ] Every section has correct heading structure and every control has an accessible name.
- [ ] No horizontal page overflow at target widths; long sources and answers wrap correctly.
- [ ] Menus, tabs, upload, citation evidence, and forms are keyboard operable.
- [ ] Focus remains visible, including sticky header/composer conditions.
- [ ] Reduced-motion and no-JavaScript marketing content remain usable.
- [ ] Citation values, source excerpts, refusal states, and optional decision telemetry remain truthful.
- [ ] Sample report and offline transcript are unmistakably labeled.
- [ ] No backend/API/auth/storage contract changes hidden inside the redesign.
- [ ] Existing 56 demo renderer assertions pass after changes, with targeted browser checks added for layout/interaction risks.
- [ ] Screenshots cover all routes, app tabs, representative mobile layouts, and loading/error/refusal states.
- [ ] Real browser console and network checks show no new missing assets or runtime exceptions.
- [ ] Performance and contrast targets are measured on the implementation, not claimed from this document.

## 13. Sources and verification limits

- Reference video and repository links above are primary design/task inputs.
- Google Labs positioning: <https://labs.google/about>; used only to interpret an experimental product direction.
- Semantic and responsive accessibility: <https://web.dev/learn/design/accessibility>.
- Navigation and focus: <https://web.dev/articles/website-navigation>.
- Motion: <https://web.dev/learn/accessibility/motion>.
- The modern-web-guidance skill was consulted. Its CLI was unavailable from the local offline package cache, so its guides were not retrieved; verify applicable guidance again before implementation when package access is available.
- Browser review covered desktop homepage, demo initial/ready layout, and app tabs. This is not a complete functional or mobile audit. Legacy pages were inspected in source. No uploads, settings changes, paid query runs, or seed operations were performed for this planning review.
- Baseline validation: `node tests/ui/demo_render_test.js` → 56 passed, 0 failed. This validates recorded-payload rendering, not current live backend correctness or visual accessibility.
