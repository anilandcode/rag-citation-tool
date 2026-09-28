# CiteRAG olive UI specification

## Scope
The design covers `/`, `/demo`, `/app` (Corpus, Playground, Report, Settings), `/v1`, and `/v2`. This is a visual and content hierarchy change. The existing API, file ingestion, response renderer, evaluation figures, and contact handoff retain their behavior.

## Reference translation
| Reference section | CiteRAG counterpart |
|---|---|
| Deep olive hero, lime glow, geometric lines | Two-line citation promise and live-demo action |
| Three translucent summaries | Four-file sample corpus, hybrid retrieval, claim verification; links are real |
| White segmented product showcase | Three working emphasis buttons around a labelled sample answer/evidence stage |
| Editorial white sections | Ingest/retrieve/verify principles, source explanation, capability tables |
| Dark process band | Connect → Find → Answer → Check with honest refusal |
| Near-black ending | Live demo/audit CTA and project footer |

## Homepage
Keep the centered pale desktop frame and remove it on narrow screens. The header provides Workflow, Verification, Capabilities, Workspace, and Live Demo; the collapsed menu retains a direct demo link. The hero uses white text against olive; summaries keep enough tinted backing to survive the glow. The showcase explains a sample corpus response, never a live metric. Its buttons change the highlighted pane, pressed state, and short live description. On small screens the selected pane moves to the top of the visual stack. Existing detailed tables and measured results remain below the primary story, with their provenance visible. The FAQ and contact actions remain functional.

## Workspace
Demo: documents, conversation, and verification remain a three-column research interface at desktop; stack in that order on mobile. Evidence text and citation links stay solid and readable. Offline transcript must identify itself. App: Corpus upload, queue, and status; Playground question and evidence; sample Report; Settings API address and key. At 901px and above, the four tabs occupy a left rail with up/down keyboard navigation; below that, they return to a horizontal row with left/right navigation. Panels retain accessible associations. Inputs and tables are opaque white with olive actions and semantic evidence status.

## Legacy routes
`/v1` and `/v2` retain their concept notices and functional links/forms. Their heroes pick up the olive gradient and the shared product surfaces, while unsupported claims remain qualified. No reference commerce content is imported.

## Responsive and accessibility
Check 1440, 1024, 768, 390, and 360px widths, plus zoom. Navigation collapses to a labelled menu on mobile. Hero summaries and product panes stack. Dense tables may scroll within their own region; no page-level horizontal overflow. Ensure readable contrast over the glow, visible focus, 44px touch targets where practical, reduced motion, and clear loading/empty/error states. Mobile visual review requires a true narrow viewport; desktop rendering alone cannot establish it.

## Verification
Run `node tests/ui/demo_render_test.js` and `npx @google/design.md lint DESIGN.md`. Review the deployed preview at every route and each app tab. Test homepage anchors, showcase buttons, demo question and citation states, app tabs, upload selection, report sample label, settings, FAQ, v2 contact form, and browser back/forward. Keep production deployment separate from this design PR.
