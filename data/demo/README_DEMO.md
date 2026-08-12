# CiteRAG Demo — Sample Questions

Try these questions against the demo corpus. The first two should produce citation-grounded answers. The third should trigger an honest refusal.

## 1. Refund policy
**Question:** "What is the refund policy for annual subscriptions?"
**Expected:** Cites `refund-policy.md`, mentions 30-day window, original payment method.

## 2. Data ownership
**Question:** "Who owns the documents I upload to CiteRAG?"
**Expected:** Cites `terms-2026.md` Section 2, confirms full ownership and no training on documents.

## 3. Refusal test
**Question:** "What is the cell phone number of the head of billing?"
**Expected:** "I don't have enough information" — honest refusal.

## 4. Multi-source
**Question:** "How much does CiteRAG cost and can I get a refund?"
**Expected:** Cites both `pricing.md` and `refund-policy.md` — multi-source answer.

## 5. Outdated document edge case
**Question:** "When were the terms of service last updated?"
**Expected:** Cites `terms-2026.md` Section 6, notes June 2026 date.
