#!/bin/bash

# FMG-1 Local Sync Protocol: Deterministic Symbolic Linking
# Purpose: Synchronize LOCAL .agents/ resources with .claude/ environment
# Standard: Sovereign Infrastructure Managed (Local-First)

# Paths: Source of Truth (Local Project)
# Use absolute paths for reliability in MINGW64
BASE_DIR=$(pwd)
SOURCE_SKILLS="$BASE_DIR/.agents/skills"
SOURCE_RULES="$BASE_DIR/.agents/rules"

# Destinations: Agent Runtime
DEST_SKILLS="$BASE_DIR/.claude/skills"
DEST_RULES="$BASE_DIR/.claude/rules"

LOG_FILE="local_sync.log"

echo "[$(date)] [SYNC_START] Initializing Local System Assembly..." | tee -a "$LOG_FILE"
echo "DEBUG: SOURCE_SKILLS=$SOURCE_SKILLS" | tee -a "$LOG_FILE"
echo "DEBUG: DEST_SKILLS=$DEST_SKILLS" | tee -a "$LOG_FILE"

# Function to create symlink
sync_link() {
    local src="$1"
    local dest="$2"

    if [ ! -d "$(dirname "$dest")" ]; then
        mkdir -p "$(dirname "$dest")"
    fi

    # Remove existing link/dir if exists to ensure deterministic state
    if [ -e "$dest" ]; then
        rm -rf "$dest"
    fi

    # Create symlink
    ln -s "$src" "$dest"

    if [ $? -eq 0 ]; then
        echo "[$(date)] [SYNC_PASS] Linked: $src -> $dest" | tee -a "$LOG_FILE"
    else
        echo "[$(date)] [SYNC_FAIL] Error linking: $src" | tee -a "$LOG_FILE"
        exit 1
    fi
}

# Execution: Sync LOCAL Skills & Rules
sync_link "$SOURCE_SKILLS" "$DEST_SKILLS"
sync_link "$SOURCE_RULES" "$DEST_RULES"

echo "[$(date)] [SYNC_COMPLETE] Local System State Synchronized." | tee -a "$LOG_FILE"
