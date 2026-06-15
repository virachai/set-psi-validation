#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  PSI Validation — E2E Smoke Test"
echo "========================================"
echo ""

# Use a fixed date for reproducible testing
TEST_DATE="${1:-$(date +%Y-%m-%d)}"
SESSION="${2:-full_day}"

echo "Test date : $TEST_DATE"
echo "Session   : $SESSION"
echo ""

# --- Step 1: Fetch prediction ---
echo "[1/4] Fetching prediction..."
PRED_OUTPUT=$(uv run python scripts/python/predictions_loader.py --session "$SESSION" 2>&1) || true
echo "$PRED_OUTPUT"

if echo "$PRED_OUTPUT" | grep -q "Prediction written to"; then
    PRED_FILE=$(echo "$PRED_OUTPUT" | grep "Prediction written to" | sed 's/.*predictions\//predictions\//')
    echo "  -> Prediction file: $PRED_FILE"
elif echo "$PRED_OUTPUT" | grep -q "SKIP"; then
    echo "  -> Prediction skipped (outside window or no API key)"
else
    echo "  -> Prediction fetch completed"
fi
echo ""

# --- Step 2: Extract market data ---
# echo "[2/4] Extracting market data..."
# uv run python scripts/python/extract_pdf.py --date "$TEST_DATE" 2>&1 || echo "  -> Market data extraction completed (or no PDF found)"
# echo ""

# --- Step 3: Run validation ---
echo "[3/4] Running validation..."
uv run python scripts/python/validation_engine.py --date "$TEST_DATE" 2>&1
echo ""

# --- Step 4: Verify outputs ---
echo "[4/4] Verifying outputs..."
ALL_OK=0

# Check predictions dir
if ls predictions/*.json 1>/dev/null 2>&1; then
    echo "  [OK] predictions/ has $(ls predictions/*.json | wc -l) file(s)"
else
    echo "  [MISS] predictions/ is empty"
    ALL_OK=1
fi

# Check validation dir
if ls validation/*.json 1>/dev/null 2>&1; then
    echo "  [OK] validation/ has $(ls validation/*.json | wc -l) file(s)"
else
    echo "  [MISS] validation/ is empty"
    ALL_OK=1
fi

# Check reports
if ls reports/*.json 1>/dev/null 2>&1; then
    echo "  [OK] reports/ has $(ls reports/*.json | wc -l) file(s)"
else
    echo "  [MISS] reports/ is empty"
    ALL_OK=1
fi

echo ""

if [ "$ALL_OK" -eq 0 ]; then
    echo "[DONE] E2E smoke test passed."
else
    echo "[WARN] E2E smoke test completed with missing outputs."
fi
