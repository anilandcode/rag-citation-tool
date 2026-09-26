# CiteRAG enterprise scale matrix

What it takes to move this pipeline from a small team to a regulated org, what the
repo does **today**, and the honest gap at each tier. Every "in repo today" claim
below points at real code. Nothing here is a projected roadmap dressed as shipped.

Canonical evidence: `docs/reports/2026-09-26_131644_live/` (live hosted run).

---

## 1. The architecture in one line

```
create  -> LLM        writes the answer + citations        (Command Code muse-spark)
decide  -> Jev        gates, scores, verifies claims       (TypeSafe System One)
execute -> code       retrieval, fusion, math, HTTP        (deterministic)
```

The split is the product. A frontier model should write prose. It should not be
asked "reply ONLY yes or no" once per claim — on a reasoning model that is roughly
a thousand hidden tokens per boolean, and it is one call per item instead of one
call per batch.

---

## 2. Tier matrix

| Tier | Shape | Corpus | In repo today | Gap to close |
|------|-------|--------|---------------|--------------|
| **1 — Small team** | single process, shared key | ~1k docs | Memory vector store + BM25 fused with RRF (`src/retrieval/pipeline.py`); demo key auth; local ONNX embeddings (`EMBED_PROVIDER=local`, no network) | — (this is the live demo) |
| **2 — Department** | index outlives process | ~50k docs | Pinecone store implemented behind `use_pinecone` + `pinecone_api_key` (`_create_pinecone_store()`); chunking + metadata already carry `source`/`page`/`section`/`indexed_at` | Needs a provisioned Pinecone index; keys are still one shared secret, not per-team |
| **3 — Company** | multi-replica, multi-team | ~500k docs | `verify_api_key` (ingest/admin) vs `verify_demo_key` (read) split; sliding-window rate limit; Langfuse traces per query; structured logs with per-query decision records | Rate limiter is **in-memory** (`_rate_limit_buckets`), so limits are per-instance and do not survive >1 replica — needs Redis or equivalent |
| **4 — Regulated org** | identity, tenancy, residency | 1M+ docs | Per-query decision audit trail: `engine`, `decision_cost`, `decision_id`, `decision_route`, `min_confidence` per claim | **Not built:** SSO/SAML, multi-tenancy, RBAC, data residency, encryption at rest. These are custom work, not features |

### Honesty note on tier 4
`data/demo/pricing.md` mentions "SSO/SAML · audit logs · data residency" — that is
**sample corpus content** used to test citation grounding. It is not a feature list.
No SSO, SAML, multi-tenancy or RBAC exists in `src/`. Do not claim otherwise.

---

## 3. The decision layer (why this scales economically)

### Before
`verify_citations()` issued **one full LLM chat call per citation**:

> "Is the claim supported? Reply 'yes' or 'no'."

With muse-spark (a reasoning model) each of those cost ~1,000 hidden reasoning
tokens to emit one word. 61 claims → 61 frontier calls.

### After
All claims go into **one batched decision call**, returning a calibrated
probability per claim instead of a bare boolean (`src/decisions/jev.py`,
`_verify_with_jev()` in `src/generation/pipeline.py`).

Plus a pre-generation gate (`src/decisions/gates.py`) that scores the query
*before* any frontier token is spent:

| Question | Type | Used for |
|----------|------|----------|
| `answerable` | noul | tripwire: is generation worth it at all? |
| `route` | choice | hybrid / vector_only / keyword_only |
| `complexity` | score | 0 = single fact → 3 = multi-hop |

### Measured (live, 17 questions, 61 claims)
| Metric | Value |
|--------|-------|
| Total decision spend | **$0.001863** (verify $0.000690 + gate $0.001172) |
| Verification accuracy | **1.0** |
| HTTP pass rate | **17/17** |
| Refusal recall | **3/3** |
| Engine split | `jev` 14 / `none` 3 (refusals carry no claims) |
| Claim confidence | min 0.920 · mean 0.963 · max 0.990 |

Gate separation had **zero overlap**:

```
unanswerable :  refuse-unrelated 0.01   refuse-password 0.02   refuse-phone 0.03
answerable   :  0.88 … 0.98  (all 14 others)
```

Unsupervised structure the gate found on its own:
- `multi-price-refund` — the only genuinely multi-document question — routed
  `hybrid`, complexity **2.0** ("needs synthesis across documents"). It was never
  told which questions were multi-hop.
- Exact-token questions (`terms-age`, `pricing-*`) → `keyword_only`
- Prose questions (refund policy) → `vector_only`
- A fabricated claim contradicted by its own source scored **0.01** — a real
  negative control, not a model that says 0.99 to everything.

---

## 4. Safety properties (these are the enterprise requirements)

1. **Fail-open.** No key, no network, changed API shape → `available()` False →
   the original LLM/heuristic path runs untouched. `ask()` never raises. A decision
   layer must never become a new failure mode on the query path.
2. **No blind retries.** A timed-out decision may already be billed and the
   endpoint documents no idempotency key, so a timeout returns not-ok and stops
   instead of failing over to a second route and paying twice.
3. **Precision-first short-circuit.** Generation is skipped only at
   `answerable ≤ 0.02`. A false refusal costs far more trust than a wasted call.
   The floor is configurable and must be calibrated on a labelled set, not on
   three samples.
4. **Confidence is surfaced, not consumed internally.** The API returns per-claim
   `confidence`, the `engine` that produced the verdict, `decision_cost`,
   `decision_id`, `decision_route` and `min_confidence` — so a caller applies its
   own threshold and a silent fallback is visible in the response.
5. **Refusals report `engine: "none"`.** No claims means nothing was judged;
   reporting `"llm"` there would overstate how much verification happened.
6. **Nothing irreversible is auto-executed.** Probabilities are calibrated across
   groups of predictions, not correctness guarantees for one answer.

---

## 5. Cost model at scale

Decision cost is roughly linear in claims, not in documents:

| Volume | Claims verified | Decision spend (at measured rate) |
|--------|-----------------|-----------------------------------|
| 17 queries | 61 | $0.0019 |
| 1,000 queries | ~3,600 | ~$0.11 |
| 100,000 queries | ~360,000 | ~$11 |

Measured rate: ~$0.00003 per query for verification. Generation cost (the frontier
model writing the answer) dominates and is unchanged — the decision layer does not
make generation cheaper, it stops *decisions* from being billed at generation rates.

Embeddings are **$0 and rate-limit-free** at any tier: they run in-container as
ONNX (`fastembed`, `BAAI/bge-small-en-v1.5`, 384-dim, ~2.6 s cold load). That
removes a third-party dependency and the 429 waves that used to stall ingestion.

---

## 6. Upgrade path (ordered by effort, not by glamour)

1. **Redis-backed rate limiter** — smallest change that unblocks >1 replica.
   Swap `_rate_limit_buckets` for a shared store; keep the same dependency shape.
2. **Provision Pinecone** — flip `use_pinecone` on with a real index; the code path
   exists and is untested against a live cluster, so treat it as integration work.
3. **Per-team API keys** — replace the single `API_KEY` secret with a key table
   carrying team, quota and scope; `verify_api_key` already returns the caller
   identity, so the seam is in place.
4. **RAGAS/DeepEval gate in CI** — harnesses exist in `src/evaluation/`; wire them
   to a threshold that fails a deploy rather than a human reading a report.
5. **SSO/SAML + RBAC** — genuine custom build, not a config flag. Quote it as such.

---

## 7. Reproduce

```bash
# live-only policy: no local Docker as job evidence
curl -sS https://artsineed--citerag-api-api.modal.run/health     # indexed:true
python3 scripts/run_live_eval.py --base https://artsineed--citerag-api-api.modal.run --skip-seed
# -> docs/reports/<ts>_live/{meta,metrics,pipeline_stats}.json, queries.jsonl, REPORT.md
```

Check the response body, not just the status code:
`verification.engine == "jev"`, per-claim `confidence` populated and discriminating,
`decision_cost` present and tiny, `gate.answerable_probability` low on refusals.
A 200 with `engine: "llm"` means the decision layer silently fell back.
