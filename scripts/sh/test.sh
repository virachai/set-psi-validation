#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  PSI Validation — Test Runner"
echo "========================================"
echo ""

MODE="${1:-all}"

case "$MODE" in
  all)
    echo "[1/2] Running Python lint + format check..."
    uv run ruff check scripts/ tests/
    uv run black --check scripts/ tests/

    echo ""
    echo "[2/2] Running all tests..."
    uv run pytest tests/ -v --tb=short
    ;;
  lint)
    echo "Running lint..."
    uv run ruff check scripts/ tests/
    uv run black --check scripts/ tests/
    ;;
  test)
    echo "Running tests..."
    shift 2>/dev/null || true
    uv run pytest tests/ -v --tb=short "$@"
    ;;
  fast)
    echo "Running tests (fast mode — no lint)..."
    shift 2>/dev/null || true
    uv run pytest tests/ -v --tb=short -q "$@"
    ;;
  one)
    shift
    if [ $# -eq 0 ]; then
      echo "Usage: ./scripts/sh/test.sh one <test_name_pattern>"
      echo "   eg: ./scripts/sh/test.sh one test_capture_market"
      exit 1
    fi
    echo "Running: $*"
    uv run pytest tests/ -v --tb=short -k "$*"
    ;;
  *)
    echo "Usage: $0 {all|lint|test|fast|one}"
    echo ""
    echo "  all    — lint + full tests (default)"
    echo "  lint   — ruff + black only"
    echo "  test   — full pytest suite"
    echo "  fast   — pytest only (no lint, quiet mode)"
    echo "  one    — run single test by name pattern"
    exit 1
    ;;
esac

echo ""
echo "Done."
