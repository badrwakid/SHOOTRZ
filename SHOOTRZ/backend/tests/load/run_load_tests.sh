#!/usr/bin/env bash
set -euo pipefail

HOST="${SHOOTRZ_HOST:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-backend/outputs/load}"
mkdir -p "$OUT_DIR"

export SHOOTRZ_DISABLE_RATE_LIMIT=1

echo "[1/3] Starting backend (4 workers)..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4 >/tmp/shootrz-load.log 2>&1 &
SERVER_PID=$!
trap "kill ${SERVER_PID} || true" EXIT

echo "[2/3] Waiting for /health..."
for i in $(seq 1 30); do
  if curl -fsS "${HOST}/health" >/dev/null; then
    break
  fi
  sleep 1
done

echo "[3/3] Running Locust scenarios..."
LOCUST_REPORT_PATH="$OUT_DIR/load_report_50u.json" \
locust -f backend/tests/load/locustfile.py \
  --headless -u 50 -r 5 -t 60s \
  --host "$HOST" \
  --csv "$OUT_DIR/50u" \
  --logfile "$OUT_DIR/50u.log"

LOCUST_REPORT_PATH="$OUT_DIR/load_report_100u.json" \
locust -f backend/tests/load/locustfile.py \
  --headless -u 100 -r 10 -t 60s \
  --host "$HOST" \
  --csv "$OUT_DIR/100u" \
  --logfile "$OUT_DIR/100u.log"

echo "Load reports written to $OUT_DIR"
