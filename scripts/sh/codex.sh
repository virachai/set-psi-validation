#!/usr/bin/env bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ================================
# OpenRouter + Codex setup
# ================================
set -euo pipefail

# -------------------------------------------------------------------------
# Usage information
# -------------------------------------------------------------------------
usage() {
  cat <<'EOF'
❌  No API key provided.
✅  Usage:
   source ./O_codex.sh <API_KEY>
   or set OPENROUTER_API_KEY beforehand
EOF
  return 1
}

# -------------------------------------------------------------------------
# Resolve the API key
# -------------------------------------------------------------------------
# 1️⃣  If an argument is supplied, use it.
# 2️⃣  Else, fall back to the environment variable OPENROUTER_API_KEY.
# 3️⃣  If neither is present, show the usage message and exit.
if [ $# -gt 0 ]; then
    API_KEY="$1"
elif [ -n "${OPENROUTER_API_KEY:-}" ]; then
    API_KEY="${OPENROUTER_API_KEY}"
else
    echo "❌ No API key provided. Please pass it as an argument or set OPENROUTER_API_KEY."
    usage
fi

# Export for any subsequently‑run commands
export OPENROUTER_API_KEY="$API_KEY"

echo "✅ OpenRouter environment variables loaded."

# -------------------------------------------------------------------------
# Optional debug (uncomment if needed)
# -------------------------------------------------------------------------
# echo "DEBUG: OPENROUTER_API_KEY=$OPENROUTER_API_KEY"
