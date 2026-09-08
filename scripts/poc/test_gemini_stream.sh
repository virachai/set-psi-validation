#!/bin/bash
set -e -E

# 1. API Key: from Argument 1 ($1) or Environment Variable ($GEMINI_API_KEY)
API_KEY="${1:-$GEMINI_API_KEY}"

if [ -z "$API_KEY" ]; then
    echo "Error: GEMINI_API_KEY not found"
    echo "Usage:"
    echo "  1) Via Argument:  ./test_gemini_stream.sh <YOUR_API_KEY> [MODEL] [INPUT_PROMPT]"
    echo "  2) Via Env Var:   export GEMINI_API_KEY='your_key' && ./test_gemini_stream.sh"
    exit 1
fi

MODEL_ID="${2:-gemini-3.1-flash-lite}"
GENERATE_CONTENT_API="streamGenerateContent"
INPUT_TEXT="${3:-Hi}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUEST_FILE="${SCRIPT_DIR}/request_stream.json"

python -c "
import json, sys

prompt = sys.argv[1]
output_file = sys.argv[2]

payload = {
    'contents': [
        {
            'role': 'user',
            'parts': [
                {'text': prompt}
            ]
        }
    ]
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
" "$INPUT_TEXT" "$REQUEST_FILE"

echo "=========================================="
echo "Model: $MODEL_ID"
echo "Request File: $REQUEST_FILE"
echo "Calling Gemini streamGenerateContent API..."
echo "=========================================="

curl -s -S \
  -X POST \
  -H "Content-Type: application/json; charset=utf-8" \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${API_KEY}" \
  -d @"$REQUEST_FILE"

echo -e "\n\nDone!"
