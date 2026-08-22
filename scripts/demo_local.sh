#!/usr/bin/env bash
# CiteRAG local demo — API on :8000, static UI on :8080
# Usage: from repo root: bash scripts/demo_local.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements-api.txt

if [[ ! -f .env ]]; then
  echo "No .env — copy .env.example and set OPENAI_API_KEY"
  cp -n .env.example .env || true
fi

# Load .env into environment (simple KEY=VAL lines)
set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ -z "${OPENAI_API_KEY:-}" || "${OPENAI_API_KEY}" == "sk-..." ]]; then
  echo "ERROR: set OPENAI_API_KEY in .env before demo"
  exit 1
fi

export DEMO_AUTO_SEED="${DEMO_AUTO_SEED:-true}"
export ALLOW_NO_RERANK="${ALLOW_NO_RERANK:-true}"
export DEMO_API_KEY="${DEMO_API_KEY:-demo-public-key}"

echo "Starting API on http://127.0.0.1:8000 ..."
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
cleanup() { kill "$API_PID" 2>/dev/null || true; kill "$UI_PID" 2>/dev/null || true; }
trap cleanup EXIT

# Wait for health
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

HEALTH=$(curl -sf http://127.0.0.1:8000/health || echo '{}')
echo "health: $HEALTH"

INDEXED=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('indexed', False))" <<<"$HEALTH" 2>/dev/null || echo False)
if [[ "$INDEXED" != "True" && "$INDEXED" != "true" ]]; then
  echo "Seeding demo corpus..."
  curl -sf -X POST http://127.0.0.1:8000/demo/seed \
    -H "X-API-Key: ${DEMO_API_KEY}" | python3 -m json.tool || true
fi

echo "Starting static UI on http://127.0.0.1:8080 ..."
python3 -m http.server 8080 --bind 127.0.0.1 &
UI_PID=$!

echo ""
echo "Open:  http://127.0.0.1:8080/demo"
echo "API:   http://127.0.0.1:8000/health"
echo "Ctrl+C to stop."
wait
