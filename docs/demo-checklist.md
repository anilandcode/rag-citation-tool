# Demo Checklist — CiteRAG v0.1

Manual verification steps for the live demo and dashboard.

---

## Marketing Landing (`/`)

- [ ] Page loads without JS errors
- [ ] Hero headline + subhead render with accent color on second line
- [ ] Nav links scroll to correct sections
- [ ] "Get Accuracy Audit" CTA links to `/demo`
- [ ] "Open App" button links to `/app`
- [ ] 3-pane hero mockup renders dark UI with documents/chat/verification
- [ ] Feature trio cards (01, 02, 03) visible
- [ ] Accordion items expand/collapse on click (How It Works, Citation Verification)
- [ ] Before/after audit report card shows baseline 0.72 → optimized 0.94
- [ ] Security badge grid renders 2×2
- [ ] Testimonial cards show colors (teal, green, gold, rose, slate)
- [ ] FAQ accordion items expand/collapse (single-open)
- [ ] Blog cards render 3 articles
- [ ] Footer renders 5 columns
- [ ] Mobile: hamburger menu works
- [ ] Mobile: layout stacks to single column

---

## Live Demo (`/demo`)

- [ ] Page loads and shows health check indicator (green/red dot)
- [ ] Offline banner appears when API unreachable (red dot shows)
- [ ] Offline canned transcript shows when banner link clicked
- [ ] "Load Sample Docs" button calls `POST /demo/seed`
- [ ] After seed: 3 documents appear in left panel
- [ ] After seed: seed button changes to "✓ 3 docs loaded"
- [ ] Preset question "What is the refund policy for annual subscriptions?" produces:
  - [ ] Answer in chat panel with inline citation tags
  - [ ] Verification panel shows ✓/✗ rows per citation
  - [ ] Citation accuracy score displayed (e.g., "2/2")
- [ ] Preset question "Who owns the documents I upload to CiteRAG?" produces:
  - [ ] Answer citing `terms-2026.md`
- [ ] Preset question "What is the cell phone number of the head of billing?" produces:
  - [ ] Honest refusal response
  - [ ] Verification panel shows "Honest Refusal" label
- [ ] Custom question via text input works
- [ ] Mobile: panes stack vertically

---

## Dashboard (`/app`)

### Corpus Tab
- [ ] Upload zone visible with dashed border
- [ ] Drag-and-drop files adds them to file list
- [ ] File removal works (× button)
- [ ] "Upload to Index" calls `POST /ingest`
- [ ] After ingest: document/chunk counts update
- [ ] API health dot shows green when online

### Playground Tab
- [ ] Document list shows indexed docs
- [ ] Sending a question shows answer with citations
- [ ] Verification panel shows per-citation ✓/✗
- [ ] Refusal questions show "Honest Refusal"
- [ ] API offline shows error message in chat

### Report Tab
- [ ] Before/after audit card renders with sample metrics
- [ ] Improvement list shows 4 items
- [ ] "Sample report" watermark visible

### Settings Tab
- [ ] API URL field pre-filled from localStorage
- [ ] API Key field pre-filled from sessionStorage
- [ ] Save button persists values
- [ ] "Settings saved" confirmation appears

---

## Backend (API)

- [ ] `python3 -c "import src.api.main"` succeeds (no NameError)
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl -X POST http://localhost:8000/demo/seed -H "X-API-Key: demo-public-key"` returns ingest response
- [ ] Query returns answer with citations and verification object
- [ ] Refusal question sets `verification.is_refusal: true`
- [ ] CORS headers present on responses
- [ ] `POST /ingest` with invalid key returns 401
- [ ] Upload filename sanitization prevents path traversal

---

## General

- [ ] No dead `#` links on landing page CTAs
- [ ] No raw Python tracebacks in any UI
- [ ] No secrets committed to git
- [ ] README has correct local run instructions
