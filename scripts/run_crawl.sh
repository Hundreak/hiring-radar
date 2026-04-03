#!/usr/bin/env bash
set -u

REPO_DIR="/home/remzi/projects/hiring-radar"
CLI_BIN="$REPO_DIR/.venv/bin/hiring-radar"
CONFIG_PATH="$REPO_DIR/config/companies.local.yml"
ENV_PATH="$REPO_DIR/.env"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/crawl.log"
LOCK_DIR="$LOG_DIR/crawl.lockdir"
WINDOW_HOURS=6

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "=== $(date -Is) skipped: crawl-and-notify already running ===" >> "$LOG_FILE"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== $(date -Is) crawl-and-notify start ===" >> "$LOG_FILE"

cd "$REPO_DIR" || {
  echo "=== $(date -Is) error: failed to cd into $REPO_DIR ===" >> "$LOG_FILE"
  exit 1
}

if [ ! -f "$ENV_PATH" ]; then
  echo "=== $(date -Is) error: missing env file at $ENV_PATH ===" >> "$LOG_FILE"
  exit 1
fi

if [ ! -f "$CONFIG_PATH" ]; then
  echo "=== $(date -Is) error: missing config file at $CONFIG_PATH ===" >> "$LOG_FILE"
  exit 1
fi

if "$CLI_BIN" crawl-and-notify \
  --config-path "$CONFIG_PATH" \
  --env-path "$ENV_PATH" \
  --window-hours "$WINDOW_HOURS" >> "$LOG_FILE" 2>&1; then
  echo "=== $(date -Is) crawl-and-notify end status=0 ===" >> "$LOG_FILE"
  exit 0
else
  status=$?
  echo "=== $(date -Is) crawl-and-notify end status=$status ===" >> "$LOG_FILE"
  exit "$status"
fi