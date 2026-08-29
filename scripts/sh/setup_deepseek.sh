#!/usr/bin/env bash

# ================================
# DeepSeek + Claude Code setup
# ================================

# Get API key from first argument or fallback to existing env
API_KEY="${1:-$ANTHROPIC_AUTH_TOKEN}"

# Validate API key
if [ -z "$API_KEY" ]; then
  echo "❌ Usage:"
  echo "   source ./setup_deepseek.sh <API_KEY>"
  echo "   or set ANTHROPIC_AUTH_TOKEN beforehand"
  return 1 2>/dev/null || exit 1
fi

# Export environment variables
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$API_KEY"

export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_MODEL="deepseek-v4-flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"

export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_EFFORT_LEVEL="max"

echo "✅ DeepSeek environment variables loaded."

# Optional debug (uncomment if needed)
# echo "DEBUG: ANTHROPIC_AUTH_TOKEN=$ANTHROPIC_AUTH_TOKEN"