#!/usr/bin/env bash
set -u

REPO_DIR="/home/remzi/projects/hiring-radar"
CLI_BIN="$REPO_DIR/.venv/bin/hiring-radar"
CONFIG_PATH="$REPO_DIR/config/companies.local.yml"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/crawl.log"
LOCK_DIR="$LOG_DIR/crawl.lockdir"

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "=== $(date -Is) skipped: crawl already running ===" >> "$LOG_FILE"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== $(date -Is) crawl start ===" >> "$LOG_FILE"

cd "$REPO_DIR" || {
  echo "=== $(date -Is) error: failed to cd into $REPO_DIR ===" >> "$LOG_FILE"
  exit 1
}

if "$CLI_BIN" crawl --config-path "$CONFIG_PATH" >> "$LOG_FILE" 2>&1; then
  echo "=== $(date -Is) crawl end status=0 ===" >> "$LOG_FILE"
  exit 0
else
  status=$?
  echo "=== $(date -Is) crawl end status=$status ===" >> "$LOG_FILE"
  exit "$status"
fi