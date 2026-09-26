# CiteRAG LIVE evaluation report

**Generated:** 2026-09-26T13:20:29.953885+00:00  
**Git:** `c0ec581`  
**API base:** `https://artsineed--citerag-api-api.modal.run`  
**Duration:** 225.57s  
**Mode:** hosted only (no local Docker)

## Health (after wake)

```json
{
  "status": "ok",
  "indexed": true,
  "chunks": 4,
  "documents": 4,
  "sources": [
    "README_DEMO.md",
    "pricing.md",
    "refund-policy.md",
    "terms-2026.md"
  ],
  "version": "0.2.0"
}
```

## Pipeline stats

| Metric | Value |
|--------|------:|
| HTTP 200 answers | 17 / 17 |
| With ≥1 citation | 14 |
| Refusal OK | 3 |
| Refusal miss | 0 |
| Mean API verify accuracy | 1.0 (n=17) |

## Samples

### refund-annual (HTTP 200)
**Q:** What is the refund policy for annual subscriptions?

**A:** Annual subscriptions can be refunded within 30 days of the initial purchase date [Source: refund-policy.md, Page N/A]. After 30 days, no refunds are available for the remaining months of the subscription term [Source: refund-policy.md, Page N/A]. Refunds are processed to the original payment method within 5–10 business days [Source: refund-policy.md, Page N/A]. If the card used for purchase has been cancelled or replaced, the refund will be issued as account credit [Source: refund-policy.md, Pag

- refusal=False cites=4

### refund-monthly (HTTP 200)
**Q:** Are monthly plans refundable?

**A:** No, monthly plans are non-refundable [Source: refund-policy.md, Page N/A]. You may cancel at any time, and your access continues until the end of the current billing period [Source: refund-policy.md, Page N/A].

- refusal=False cites=2

### refund-process-time (HTTP 200)
**Q:** How long do refunds take to process to the original payment method?

**A:** Refunds are processed to the original payment method within 5–10 business days [Source: refund-policy.md, Page N/A].

- refusal=False cites=1

### refund-request-contact (HTTP 200)
**Q:** How do I request a refund and what email should I use?

**A:** To request a refund, contact **billing@citerag.com** [Source: refund-policy.md, Page N/A] or use the Billing tab in your account dashboard [Source: refund-policy.md, Page N/A].

Include your invoice ID [Source: refund-policy.md, Page N/A]. Requests are processed within 2 business days [Source: refund-policy.md, Page N/A].

- refusal=False cites=4

### refund-enterprise (HTTP 200)
**Q:** Do enterprise agreements follow the same 30-day refund policy?

**A:** No, custom enterprise agreements have their own refund terms negotiated at contract signing [Source: refund-policy.md, Page N/A], while the 30-day refund window applies to annual subscriptions [Source: refund-policy.md, Page N/A].

- refusal=False cites=2


## Reproduce

```bash
python scripts/run_live_eval.py
# or
CITERAG_API_BASE=https://<your-render>.onrender.com python scripts/run_live_eval.py
```

## Notes

- This pack is **live traffic** against the public demo API.
- RAGAS full four-metric suite is optional server-side (`POST /evaluate` + API_KEY).
- Free Render may cold-start; script waits up to `--wake-seconds`.
