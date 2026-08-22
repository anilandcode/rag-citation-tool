#!/usr/bin/env bash
# Static + rewrite smoke (no secrets). From repo root: bash scripts/smoke_hosted.sh
set -euo pipefail
LANDING="${LANDING:-https://rag-citation-tool.vercel.app}"
API="${API:-https://citerag-api.onrender.com}"

echo "== frontend =="
for path in / /demo /app /v1; do
  code=$(curl -sS -o /dev/null -m 20 -w "%{http_code}" "${LANDING}${path}" || echo err)
  echo "  ${path} -> ${code}"
done

echo "== api =="
code=$(curl -sS -o /tmp/citerag_h.txt -m 45 -w "%{http_code}" "${API}/health" || echo err)
echo "  ${API}/health -> ${code}"
head -c 200 /tmp/citerag_h.txt 2>/dev/null; echo

code=$(curl -sS -o /tmp/citerag_vh.txt -m 45 -w "%{http_code}" "${LANDING}/api/health" || echo err)
echo "  ${LANDING}/api/health -> ${code}"
head -c 200 /tmp/citerag_vh.txt 2>/dev/null; echo
