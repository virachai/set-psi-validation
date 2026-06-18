#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  PSI Validation — Unified Test Runner"
echo "========================================"
echo ""

MODE="${1:-all}"

# --- Internal E2E Logic ---
run_e2e() {
    TEST_DATE="${2:-$(date +%Y-%m-%d)}"
    SESSION="${3:-full_day}"
    echo "Running E2E Smoke Test..."
    echo "Test date : $TEST_DATE | Session : $SESSION"
    uv run python scripts/python/predictions_loader.py --session "$SESSION"
    uv run python scripts/python/validation_engine.py --date "$TEST_DATE"
    echo "Verifying outputs..."
    ls predictions/*.json >/dev/null 2>&1 && echo "  [OK] predictions/ exists" || echo "  [MISS] predictions/"
    ls validation/*.json >/dev/null 2>&1 && echo "  [OK] validation/ exists" || echo "  [MISS] validation/"
    ls reports/*.json >/dev/null 2>&1 && echo "  [OK] reports/ exists" || echo "  [MISS] reports/"
}

case "$MODE" in
  all|check)
    echo "[1/5] ruff check..."
    uv run ruff check .
    echo "[2/5] black --check..."
    uv run black --check .
    echo "[3/5] mypy..."
    uv run mypy scripts/ tests/
    echo "[4/5] pytest..."
    uv run pytest -q
    echo "[5/5] e2e smoke test..."
    run_e2e "all"
    ;;
  lint)
    uv run ruff check .
    uv run black --check .
    ;;
  test)
    uv run pytest -q
    ;;
  e2e)
    run_e2e "$@"
    ;;
  one)
    shift
    uv run pytest -q -k "$*"
    ;;
  *)
    echo "Usage: $0 {all|lint|test|e2e|one}"
    exit 1
    ;;
esac

echo ""
echo "Done."
