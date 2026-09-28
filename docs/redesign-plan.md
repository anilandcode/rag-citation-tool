# CiteRAG redesign implementation plan

Date: 2026-09-28. Design authority: [design.md](../design.md).
Baseline: `2e4a019108d5a3b712c5eaa26fc99c73defd0fac`.
Working branch: `design/evidence-lab-redesign`.

## Outcome

Upgrade the complete existing interface using the Evidence Lab design system: warm paper, structured grids, bold typography, monochrome document imagery, and controlled orange highlights. Cover `/`, `/demo`, `/app` and its four tabs, `/v1`, and `/v2`. Preserve working product behavior.

This branch initially contains the plan and design specification only. Implementation and deployment are separate milestones; documentation completion does not mean the site has changed.

## Findings that determine the plan

| Finding | Consequence |
| --- | --- |
| All public pages are static HTML with substantial inline CSS | Extract shared design layers incrementally; avoid a framework migration |
| Current homepage is sage/landscape; old design guide specifies coral | Establish root `design.md` as the new authority and mark old guide historical |
| Demo renders live-shaped citation and Jev data | Preserve field meanings and renderer behavior; use existing fixture suite as regression baseline |
| Workspace Report is a hardcoded sample | Redesign it honestly as a sample, without implying uploaded documents were evaluated |
| Theme selector offers unfinished dark mode | Remove or disable that option in the light-theme release |
| Vercel clean routes and catch-all are already configured | Preserve routes, API proxy, and root-relative assets; no hosting migration |
| `/v1` contains enterprise and testimonial-style material | Label unsupported concept content during the visual/content pass |
| `/v2` includes a mailto audit form | Preserve validation and explicit email-client handoff |

## Phase 0 — Baseline and specification

Completed for planning:

- [x] Read route configuration and enumerate public HTML pages.
- [x] Inspect live homepage, demo, and app tabs.
- [x] Inspect the reference video in the browser.
- [x] Review demo API schema, representative corpus files, and renderer test harness.
- [x] Run existing renderer checks: 56 passed, 0 failed.
- [x] Write the full design system, surface specifications, responsive rules, and state requirements.

Before implementation: capture baseline screenshots at 1440px and 390px for every route and app tab. Preserve the baseline SHA in the implementation PR. Inspect the current branch for concurrent changes and reconcile them before editing.

## Phase 1 — Foundation

Files: proposed `assets/css/tokens.css`, `base.css`, `components.css`, and shared UI helpers.

Tasks:

1. Implement semantic color, type, space, radius, and motion tokens from `design.md`.
2. Build buttons, inputs, status labels, disclosure, metric, document, and evidence patterns.
3. Establish the shared header, footer, skip link, focus behavior, and mobile menu.
4. Add source/evidence styles without changing how responses are parsed.
5. Remove old rules only as each surface migrates; do not append a large override sheet.

Exit gate: a real page demonstrates every core primitive, color contrast has been checked, and keyboard focus is visible. Shared assets load from nested routes.

## Phase 2 — Homepage

Files: `index.html`, proposed `assets/css/marketing.css`, optional original visual assets.

Build the documented section order: header → hero → evidence stage → capabilities → process → product showcase → evaluation → capabilities/limits → offers → FAQ → final CTA → footer.

Use the real sample corpus for illustrative answer content, clearly marked as sample. Replace scenic metaphors with document/evidence explanations. Keep detailed technical material available below the core product story. Preserve genuine creator attribution, contact links, and measured-report provenance; qualify the scope of any reported numbers.

Exit gate: strong reference alignment at desktop, clear hierarchy at mobile, working primary links, accessible FAQ/menu, no invented metrics or product features. Optional generated art is only added if it materially improves the page.

## Phase 3 — Demo and shared answer/evidence UI

Files: `demo.html`, proposed `assets/css/workspace.css`; shared primitives from Phase 1.

Tasks:

1. Implement the desktop three-pane shell and responsive alternatives.
2. Rework empty state, preset prompts, document rows, and composer.
3. Style answers, citations, source excerpts, and verification states consistently.
4. Add accessible evidence disclosure/focus behavior using response data already available.
5. Preserve refusal, offline transcript, engine badges, confidence, and decision cost semantics.
6. Prevent duplicate submissions and announce concise busy/result status without changing backend behavior.

Regression gate: existing renderer suite passes; browser review covers supported answer, mixed support, missing page, refusal, offline preview, long answer, and absent optional telemetry. Use existing fixture payloads for deterministic visual states. Do not spend API credits just to capture screenshots.

## Phase 4 — Workspace

Files: `app.html`, workspace CSS, minimal shared UI helpers.

| View | Implementation | Acceptance |
| --- | --- | --- |
| Corpus | Upload zone, queue rows, status cards, indexing/error/success feedback | Keyboard file selection and removal work; unknown counts are not zero; queue survives failure |
| Playground | Reuse answer/evidence patterns; clear no-corpus state | Existing query request/response contract preserved; evidence readable on mobile |
| Report | Sample provenance above values, clear baseline/optimized comparison | No live-data implication and no decorative nonfunctional actions |
| Settings | Associated labels, masked key, hints, save/connection feedback | Save behavior and storage policy preserved; unfinished theme option cannot mislead |
| Tabs | Tablist/tabpanel association and keyboard navigation | Arrow keys, Home/End, focus and selected state agree |

Exit gate: all tabs work, tab changes preserve expected session state, and the app looks consistent with the demo. Validate ingest only with harmless test documents against an appropriate test environment, not by altering the shared production corpus during visual review.

## Phase 5 — Legacy routes and final consistency

Files: `v1/index.html`, `v2/index.html`, `docs/design-inventra.md` historical notice.

- Restyle all sections, navigation, buttons, cards, imagery treatment, FAQ, and footers.
- Add clear previous-concept context without breaking routes.
- Retain `/v2` form fields, limits, validation, and mailto encoding. Never auto-send email.
- Resolve legacy unsupported claims and placeholders rather than presenting them as shipped capabilities.
- Check every image and root-relative link at both nested routes.
- Keep meaningful existing anchors; preserve archived visual files in Git.

Exit gate: no page remains on an unrelated palette or component vocabulary. Every existing public route is included in review screenshots.

## Phase 6 — Verification and delivery

### Required matrix

| Area | Check |
| --- | --- |
| Routes | `/`, `/demo`, `/app`, `/v1`, `/v2`, direct HTML compatibility where applicable |
| Viewports | 360, 390, 768, 1024, 1440px; 200% zoom |
| App views | Corpus, Playground, Report, Settings |
| Evidence states | Supported, unsupported, refusal, absent source page, absent confidence/gate |
| Async states | Loading, connection failure, ingest failure, offline transcript, recovery |
| Keyboard | Skip link, header/menu, tabs, upload, remove file, composer, citations, FAQ, settings |
| Readability | Contrast, long filename, multiline answer, focus visibility, no clipped content |
| Motion | Reduced motion enabled; no essential content gated behind animation |
| Integrity | API paths/headers, config loading, storage, escaped answer/source content unchanged |
| Browser quality | No new runtime errors, broken images, missing styles, or page-level overflow |

Run `node tests/ui/demo_render_test.js` after demo changes and at the final gate. This is a DOM-stub renderer test, not a browser layout test. Use browser screenshots and actual keyboard interactions to cover the remaining risks. Run backend tests only if backend-related code actually changes.

Measure Lighthouse/accessibility/performance on an available preview with the API state documented. Aim for LCP ≤2.5s, CLS ≤0.1, and INP ≤200ms as field targets; a single local run cannot establish field performance. Reserve image geometry, avoid new large animation libraries, and keep decorative assets within the stated budget.

Deliver a reviewable implementation PR with desktop/mobile screenshots, exact test results, all changed routes, and any remaining limitations. Keep production deployment as an explicit delivery step after implementation is ready; a pushed branch or successful test is not evidence that the public Vercel URL changed.

## Suggested commit sequence

1. `docs: define Evidence Lab design system and redesign plan` — this planning change.
2. `style: add shared CiteRAG design foundations`.
3. `feat(ui): redesign homepage around citation evidence`.
4. `feat(ui): redesign demo answer and verification experience`.
5. `feat(ui): unify workspace views and interaction states`.
6. `style: align legacy pages and audit form`.
7. `fix(ui): complete responsive accessibility and visual QA`.

Each implementation commit should leave its touched routes usable. Keep backend and deployment configuration changes out of styling commits.

## Risk controls and rollback

- Inline renderer coupling: preserve DOM IDs/functions; update fixture harness only if script organization changes.
- CSS collision: migrate to shared semantic classes with explicit page modifiers; remove conflicting migrated rules.
- Misleading data: sample badges precede sample metrics; refusal and unknown states never imply measured failure/success.
- Mobile density: collapse supporting panels before shrinking text or tap targets.
- Legacy claims: label concept material and retain only supported factual claims as current product promises.
- Concurrent work: recheck main before implementation merge and resolve changed files deliberately.
- Rollback: revert the redesign commits or restore the prior deployment. Do not force-reset shared history or delete the older assets.

## Completion tracker

| Milestone | Current status |
| --- | --- |
| Repository/reference audit | Complete, with documented browser coverage limits |
| Design system and implementation plan | Complete |
| Shared component implementation | Not started |
| Homepage redesign | Not started |
| Demo redesign | Not started |
| Workspace redesign | Not started |
| Legacy route redesign | Not started |
| Full visual/accessibility QA | Not started |
| Production release | Not started |
