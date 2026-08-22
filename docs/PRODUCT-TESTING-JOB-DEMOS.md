# CiteRAG: Productization + Real Testing + Job-Demo Reports

**Goal:** Turn CiteRAG from a strong engineering portfolio piece into (1) a clear hireable product story and (2) a pack of **real, rerunnable demos + persisted eval reports** you can show in job applications — without fake customers, fake KPIs, or always-on SaaS theater.

**Date:** 2026-08-22  
**Repo:** `rag-citation-tool` (`anilandcode/rag-citation-tool`)  
**Live:** https://rag-citation-tool.vercel.app · `/demo` · `/app` · `/v1`  
**API:** Render FastAPI (`citerag-api.onrender.com` historically cold)

---

## 0. Honest starting point

### What already exists (product bones)
| Layer | Status | Evidence |
|-------|--------|----------|
| Landing | Live CICADA upgrade | `/` meadow hero + production table + anilpervaiz.com credit |
| Demo UI | Live 3-pane | `/demo` |
| Dashboard shell | Live | `/app` |
| Ingest | Code | `src/ingestion/pipeline.py` + `data/demo/*` |
| Hybrid retrieve | Code | vector + BM25 + RRF; Cohere optional — `src/retrieval/pipeline.py` |
| Cite + verify + refuse | Code | `src/generation/pipeline.py` |
| FastAPI | Code | health, seed, query, ingest, evaluate, audit-report — `src/api/main.py` |
| RAGAS harness | Code | faithfulness / relevancy / precision / recall — `src/evaluation/ragas_harness.py` |
| DeepEval gates | Code | `src/evaluation/deepeval_harness.py` |
| Audit report | Code | `src/evaluation/audit_report.py` (`run_audit`) |
| Golden sample | Thin / stale | `tests/eval_datasets/sample_golden.json` (hand-written answers; not demo-corpus-aligned) |
| Unit tests | Partial | `pytest tests/unit/` per README |
| Persisted job-pack reports | **Missing** | No `docs/reports/` timestamped pack |
| Always-hot public API | **Weak** | Render free tier cold starts |

### What “real product” does **not** mean for job season
- Not multi-tenant SaaS with billing in week 1  
- Not fake logos, fake ARR, or invented faithfulness on the landing  
- Not “always free public RAG for the internet” (cost + abuse)

### What it **does** mean for Anil
A **sellable/hireable offer** with proof:
1. **Working case** — CiteRAG demo you can open in a browser  
2. **Measured stack** — RAGAS/DeepEval/audit JSON+MD you ran yourself  
3. **Service offer** — accuracy audit / custom pipeline (mailto already on landing)  
4. **Portfolio narrative** — “I ship production RAG layers, not chat wrappers”

---

## 1. Product definition (lock this story)

### One-liner
**CiteRAG is a citation-grounded RAG stack** (ingest → hybrid retrieve → cite → verify → refuse → evaluate) you can demo live and hire Anil to install or audit on real documents.

### Three SKUs (not a pricing grid)
| SKU | What buyer/interviewer gets | Surface |
|-----|------------------------------|---------|
| **A. Live demo** | Ask sample corpus; see answer + citations + verify pane | `/demo` (+ local uvicorn if cold) |
| **B. Accuracy audit** | Before/after metrics on *their* docs (or public corpus) | CLI/`run_audit` → PDF/MD report |
| **C. Custom pipeline** | Same modules wired to their store/keys/UI | Repo + short engagement |

### Positioning (jobs vs clients)
| Audience | Message | Proof pack |
|----------|---------|------------|
| **Hiring manager / AI eng** | “I built a full production RAG path with eval” | Live URL + `docs/reports/` + architecture + code tour |
| **Agency / SMB lead** | “Broken doc Q&A → measured fix” | Sample audit PDF + 15-min Loom |
| **Portfolio site** | Link from anilpervaiz.com → CiteRAG | Case study page later |

### Explicit non-goals (v1 product)
- User accounts / SSO / multi-tenant isolation  
- GraphRAG / agent loops as the headline  
- Guaranteed always-hot free public API  
- Selling API seats before audit product works

### Product surfaces map
```
/                 → marketing + offer + production baseline table
/demo             → interactive proof (primary job demo)
/app              → operator view (upload/playground/report UI)
API (local/Render)→ /health /demo/seed /query /ingest /evaluate /audit-report
docs/reports/     → timestamped artifacts (NEW — job pack)
/v1               → frozen CICADA original (design history)
```

---

## 2. Reliability layer (so demos don’t fail mid-interview)

Cold Render is the #1 job-demo risk. Fix reliability **before** more landing polish.

### Priority order
1. **Local gold path (must work offline from network cold)**  
   - Documented one-command: venv + `uvicorn` + open `/demo` pointed at `localhost:8000`  
   - Script: `scripts/demo_local.sh` (optional build)  
2. **Health preflight**  
   - Before any call/screen-share: `curl /health` → `indexed: true`  
   - If false → `POST /demo/seed`  
3. **Hosted warm path**  
   - Keep Render for public links  
   - Options (pick one when building):  
     a. Paid always-on tiny instance, or  
     b. Cron ping `/health` every 10m (partial), or  
     c. Honest UI: “API waking up — 30–60s” + local fallback instructions  
4. **Offline demo mode (already partially there)**  
   - Keep labeled offline answers only if live fails; never pretend they are live metrics  
5. **Cost control**  
   - `gpt-4o-mini` default for demo  
   - Cap concurrent public queries (rate_limit already)  
   - Eval runs local-only with API key, not public

### Demo SOP (print this for interviews)
```
T-10 min: start local API OR wake Render (/health)
T-5 min: open /demo, seed if needed, run refund question
T-0: share screen — show cite + verify + one refusal
Backup: docs/reports/<latest>/ with screenshots if API dies
```

---

## 3. Complete real testing plan

Goal: exercise the **real pipelines**, not only `compileall`.

### 3.1 Test pyramid

| Level | What | Command / path | Persist? |
|-------|------|----------------|----------|
| L0 Unit | citation parse, refuse detect, metadata | `pytest tests/unit/ -v` | CI log |
| L1 Integration smoke | import API, health, seed, one query | local uvicorn + curl | `docs/reports/.../smoke.json` |
| L2 Pipeline E2E | ingest demo → hybrid → generate → verify | scripted Python | JSON + MD |
| L3 RAGAS | 10–20 golden Qs on demo corpus | `run_ragas_evaluation` / CLI eval | metrics JSON |
| L4 DeepEval gate | single/multi with thresholds | `evaluate_single_response` | pass/fail JSON |
| L5 Audit | `run_audit` full loop | CLI or `/audit-report` | audit JSON + HTML/MD |
| L6 Optional A/B | vector-only vs hybrid (same golden) | custom script | comparison table |
| L7 Optional Cohere | with/without `COHERE_API_KEY` | same golden | note in report |

### 3.2 Fix the golden dataset first (blocking)

`tests/eval_datasets/sample_golden.json` is **not job-ready**:
- Answers/contexts are synthetic  
- Sources say `policy.pdf` while demo corpus is `refund-policy.md` etc.  
- Includes password-reset Qs not in demo docs (good for **refusal** cases if labeled)

**Create instead:**
```
tests/eval_datasets/demo_corpus_golden.json
  - 12–20 questions grounded ONLY in data/demo/*
  - types: factual, keyword/ID, multi-hop-lite, out-of-corpus refusal
  - fields: question, ground_truth, expected_source (optional), expect_refusal (bool)

tests/eval_datasets/demo_corpus_adversarial.json
  - near-miss questions, wrong entity names, empty-context traps
```

### 3.3 E2E script (to build) — single source of truth

`scripts/run_full_eval.py` (planned):
1. Load env (`OPENAI_API_KEY`, optional Cohere)  
2. `run_ingestion("data/demo")`  
3. `build_full_retrieval_pipeline`  
4. For each golden item: query → answer, contexts, citations, verification  
5. Write per-question rows to `docs/reports/<ts>/queries.jsonl`  
6. Call RAGAS → `metrics.json`  
7. Call DeepEval on subset → `gates.json`  
8. Emit `REPORT.md` (human) + `report.html` (optional)  
9. Print summary faithfulness / citation accuracy / refuse rate  

**Never hand-edit metrics in REPORT.md.** Regenerate or label as sample.

### 3.4 What “complete” means for v1 job pack
- [ ] L0 unit green  
- [ ] L2 E2E on demo corpus (≥10 Qs)  
- [ ] L3 RAGAS numbers from that run  
- [ ] At least 1 intentional **refusal** success  
- [ ] At least 1 **citation verified** path  
- [ ] Screenshots of `/demo` for the same questions  
- [ ] README link to latest report folder  
- [ ] Known limits section (cold start, in-memory index, sequential verify latency)

### 3.5 What not to claim
- Do not put RAGAS numbers on the landing unless they match the latest report folder and are dated  
- Do not claim Pinecone/Cohere “in production” unless that run used them  
- Do not claim multi-tenant security audit

---

## 4. Keep the reports (job application pack)

### Folder contract
```
docs/reports/
  README.md                          # how to read / how to regenerate
  2026-08-22_demo-corpus/
    meta.json                        # git sha, models, keys present (bool only), duration
    metrics.json                     # RAGAS four metrics
    gates.json                       # DeepEval pass/fail
    queries.jsonl                    # one line per Q
    audit.json                       # run_audit shape if used
    REPORT.md                        # narrative for humans
    screenshots/
      demo-refund.png
      demo-refusal.png
      app-health.png
    loom.txt                         # optional link
  latest -> 2026-08-22_demo-corpus   # symlink or copy pointer file
```

### `meta.json` schema (minimal)
```json
{
  "timestamp": "2026-08-22T16:00:00+05:00",
  "git_sha": "c0ec581",
  "corpus": "data/demo",
  "llm_model": "gpt-4o-mini",
  "embed_model": "...",
  "cohere_rerank": false,
  "pinecone": false,
  "n_questions": 15,
  "command": "python scripts/run_full_eval.py --golden tests/eval_datasets/demo_corpus_golden.json"
}
```

### Interview one-pager (generate from REPORT.md)
`docs/JOB_DEMO.md` (planned short file):
- Links: live demo, GitHub, latest report  
- Architecture 6 bullets  
- “How to reproduce in 10 minutes”  
- Two screenshots  
- Contact: hello@anilpervaiz.com · anilpervaiz.com

### Portfolio usage
| Application artifact | Source |
|----------------------|--------|
| Resume bullet | “Built citation-grounded RAG (hybrid+RRF, verify, RAGAS); live demo + measured report” |
| Portfolio case | Landing + `/demo` + report MD |
| Take-home appendix | Link `docs/reports/latest/REPORT.md` |
| Screen share | `/demo` local first |

---

## 5. Productization roadmap (build order)

Do **not** start with another landing redesign. Order is reliability → measure → package → light product polish.

### Phase 0 — Stabilize demos (1–2 days)
- [ ] Confirm local uvicorn path end-to-end on this machine  
- [ ] Fix `/demo` API base config if needed (`assets/config.js`)  
- [ ] Wake/fix Render or document “local only” for interviews  
- [ ] Update `docs/demo-checklist.md` with pass/fail last-run date  
- [ ] Capture 3 screenshots into a draft report folder

### Phase 1 — Golden + eval runner (2–4 days)
- [ ] Author `demo_corpus_golden.json` from real `data/demo` files  
- [ ] Implement `scripts/run_full_eval.py`  
- [ ] Write first real `docs/reports/<date>/` pack  
- [ ] Wire `python -m src.cli eval` to golden path if missing  
- [ ] Add unit tests for citation extract + refuse on fixed strings

### Phase 2 — Job pack + narrative (1–2 days)
- [ ] `docs/JOB_DEMO.md`  
- [ ] `docs/reports/README.md`  
- [ ] Link report from README + optional landing “Sample measured report” (only if real)  
- [ ] 3–5 min Loom: problem → hybrid → cite → verify → metrics  
- [ ] anilpervaiz.com case blurb (manual)

### Phase 3 — Product hardening (optional, after pack exists)
- [ ] Persist index option (Pinecone) for multi-session demo  
- [ ] `/app` report tab loads last `docs/reports` or API audit  
- [ ] Before/after audit: vector-only baseline vs hybrid (true delta)  
- [ ] CI: unit + compileall on push; eval manual/nightly (cost)  
- [ ] Rate limits + abuse notes for public demo key

### Phase 4 — Offer ops (only if selling audits)
- [ ] Intake form (typeform/email template)  
- [ ] NDA + data handling one-pager  
- [ ] Fixed audit checklist + price band  
- [ ] Delivery template = `generate_audit_report` HTML

---

## 6. Suggested interview demo script (5 minutes)

1. **Landing (30s)** — production baseline table; “built by anilpervaiz.com”  
2. **Architecture (45s)** — hybrid + cite + verify + RAGAS (point at repo modules)  
3. **Live `/demo` (2 min)**  
   - Q: annual refund → cite `refund-policy` + verified  
   - Q: something not in corpus → refuse  
4. **Report (1 min)** — open `docs/reports/latest/REPORT.md` metrics  
5. **Close (30s)** — “Same path for a client audit or your team’s stack”

Backup if API cold: skip step 3 live; use screenshots + local terminal curl log in report.

---

## 7. Success criteria (definition of done for “real product + real demos”)

You can honestly say yes to all:
1. Stranger can open `/demo` **or** follow 10-min local setup and get a cited answer  
2. You have a **git-tracked** report folder with RAGAS numbers from a command you can rerun  
3. Resume/portfolio links resolve (landing, demo, GitHub, report)  
4. You can explain failure modes (cold start, no rerank, in-memory) without flinching  
5. Offer path works: mailto audit + clear SKU A/B/C  
6. No fake social proof on the site

---

## 8. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Render cold mid-interview | Local-first SOP + screenshots pack |
| OpenAI cost during eval | mini model; golden ≤20 Qs; no public `/evaluate` |
| Golden drift vs corpus | Golden and `data/demo` versioned together |
| Over-claiming “production SaaS” | Language: production **stack** / working case |
| Drive FS slow for git | Commit from clone if needed; keep reports small (web jpgs) |
| Eval flaky LLM judges | Seed, temperature notes in meta; multiple runs average optional |

---

## 9. Immediate next actions (when you say “build”)

1. Author real golden set from `data/demo/{refund-policy,terms-2026,pricing}.md`  
2. Add `scripts/run_full_eval.py` + `docs/reports/` contract  
3. Run once; commit report pack  
4. Write `docs/JOB_DEMO.md`  
5. Only then: optional always-on API or `/app` report viewer  

**Do not** start another visual redesign until Phase 1 report exists.

---

## 10. Files likely to change (when implementing)

| Path | Action |
|------|--------|
| `tests/eval_datasets/demo_corpus_golden.json` | create |
| `scripts/run_full_eval.py` | create |
| `docs/reports/**` | create (artifacts) |
| `docs/JOB_DEMO.md` | create |
| `docs/demo-checklist.md` | update last-run |
| `README.md` | link job pack + regenerate |
| `src/cli.py` | eval path polish |
| `tests/unit/*` | citation/refuse coverage |
| `.github/workflows/ci.yml` | optional later |
| Landing | only if linking real report (optional) |

---

## 11. Open questions (for you)

1. **Hosted API budget:** keep free Render (cold OK + local backup) or pay for always-on for applications?  
2. **Public report:** commit metrics to public GitHub, or private gist + public screenshots only?  
3. **Primary job target:** AI eng / fullstack / freelance audit clients? (tunes narrative weight)  
4. **Corpus:** stay on synthetic demo docs, or add one anonymized real-ish PDF set?

Defaults if you don’t answer: free Render + local backup, **public** reports in repo (stronger for jobs), AI eng narrative, demo corpus only.

---

## 12. Bottom line

CiteRAG is already a **real stack**. What’s missing for “product + job demos” is not another brand: it’s **reliability SOP**, a **corpus-true golden set**, a **one-command eval that writes `docs/reports/`**, and a **short job narrative** that points at those artifacts.

Landing and offer copy can stay. Measure and package next.
