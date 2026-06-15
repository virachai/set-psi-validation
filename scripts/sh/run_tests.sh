#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  PSI Validation — Test Runner"
echo "========================================"
echo ""

MODE="${1:-all}"

case "$MODE" in
  all|check)
    echo "[1/5] ruff check..."
    uv run ruff check .
    echo ""
    echo "[2/5] black --check..."
    uv run black --check .
    echo ""
    echo "[3/5] mypy..."
    uv run mypy scripts/ tests/
    echo ""
    echo "[4/5] pytest..."
    uv run pytest -q
    echo ""
    echo "[5/5] e2e smoke test..."
    bash scripts/sh/e2e_test.sh
    ;;
  lint)
    echo "Running lint..."
    uv run ruff check .
    uv run black --check .
    ;;
  test)
    shift 2>/dev/null || true
    uv run pytest -q "$@"
    ;;
  one)
    shift
    if [ $# -eq 0 ]; then
      echo "Usage: $0 one <test_name_pattern>"
      echo "   eg: $0 one test_capture_market"
      exit 1
    fi
    uv run pytest -q -k "$*"
    ;;
  *)
    echo "Usage: $0 {all|lint|test|one}"
    echo ""
    echo "  all/check — ruff + black + mypy + pytest (default)"
    echo "  lint      — ruff + black only"
    echo "  test      — pytest only"
    echo "  one       — run single test by name pattern"
    exit 1
    ;;
esac

echo ""
echo "Done."
