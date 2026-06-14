#!/usr/bin/env bash

# Gemini Proxy + Claude Code environment setup (DeepSeek Mode)
# This points Anthropic-compatible clients to our local Gemini Proxy using DeepSeek model names

export ANTHROPIC_BASE_URL="http://127.0.0.1:3004"
export ANTHROPIC_API_KEY="sk-ant-gemini-proxy-dummy-token"
export ANTHROPIC_AUTH_TOKEN="sk-ant-gemini-proxy-dummy-token"

# Define the Gemini model fallback chain for the proxy
export API_GEMINI_CHAT_MODEL="models/gemini-3.1-flash-lite-preview,models/gemini-2.5-flash-lite,models/gemini-1.5-flash,models/gemini-3-flash-preview,models/gemini-2.5-flash"

# Map to DeepSeek model names which our proxy will handle by calling Gemini
export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"

export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_EFFORT_LEVEL="max"

echo "✅ Gemini Proxy (DeepSeek Mode) environment variables loaded."
echo "📡 Base URL: $ANTHROPIC_BASE_URL"
echo "🤖 Model: $ANTHROPIC_MODEL (Mapped to Gemini 3.1 Flash Lite)"