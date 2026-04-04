#!/usr/bin/env bash
set -Eeuo pipefail

readonly REPO_DIR="/home/remzi/projects/hiring-radar"
readonly CLI_BIN="$REPO_DIR/.venv/bin/hiring-radar"
readonly CONFIG_PATH="$REPO_DIR/config/companies.local.yml"
readonly ENV_PATH="$REPO_DIR/.env"
readonly LOG_DIR="$REPO_DIR/logs"
readonly LOG_FILE="$LOG_DIR/crawl.log"
readonly LOCK_DIR="$LOG_DIR/crawl.lockdir"
readonly LEGACY_LOCK_FILE="$LOG_DIR/crawl.lock"
readonly WINDOW_HOURS=6
readonly MAX_LOG_SIZE_BYTES=1048576
readonly MAX_ROTATED_LOGS=5

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

rotate_logs_if_needed() {
  if [ ! -f "$LOG_FILE" ]; then
    return 0
  fi

  local size
  size=$(wc -c < "$LOG_FILE")

  if [ "$size" -lt "$MAX_LOG_SIZE_BYTES" ]; then
    return 0
  fi

  local i
  for ((i=MAX_ROTATED_LOGS; i>=1; i--)); do
    local current="$LOG_FILE.$i"
    local next="$LOG_FILE.$((i + 1))"

    if [ "$i" -eq "$MAX_ROTATED_LOGS" ] && [ -f "$current" ]; then
      rm -f "$current"
    elif [ -f "$current" ]; then
      mv "$current" "$next"
    fi
  done

  mv "$LOG_FILE" "$LOG_FILE.1"
  touch "$LOG_FILE"
}

log_line() {
  printf '=== %s %s ===\n' "$(date -Is)" "$1" >> "$LOG_FILE"
}

fail() {
  log_line "error: $1"
  printf '%s\n' "$1" >&2
  exit 1
}

if [ ! -d "$REPO_DIR" ]; then
  fail "missing repo directory at $REPO_DIR"
fi

if [ ! -x "$CLI_BIN" ]; then
  fail "missing or non-executable CLI binary at $CLI_BIN"
fi

if [ ! -f "$ENV_PATH" ]; then
  fail "missing env file at $ENV_PATH"
fi

if [ ! -f "$CONFIG_PATH" ]; then
  fail "missing config file at $CONFIG_PATH"
fi

if [ ! -w "$LOG_FILE" ]; then
  printf '%s\n' "log file is not writable: $LOG_FILE" >&2
  exit 1
fi

rotate_logs_if_needed

if [ -e "$LEGACY_LOCK_FILE" ]; then
  log_line "warning: legacy lock file present at $LEGACY_LOCK_FILE (ignored)"
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log_line "skipped: crawl-and-notify already running lock_dir=$LOCK_DIR"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

log_line \
  "crawl-and-notify start repo_dir=$REPO_DIR config_path=$CONFIG_PATH env_path=$ENV_PATH window_hours=$WINDOW_HOURS"

cd "$REPO_DIR" || fail "failed to cd into $REPO_DIR"

if "$CLI_BIN" crawl-and-notify \
  --config-path "$CONFIG_PATH" \
  --env-path "$ENV_PATH" \
  --window-hours "$WINDOW_HOURS" >> "$LOG_FILE" 2>&1; then
  log_line "crawl-and-notify end status=0"
  exit 0
else
  status=$?
  log_line "crawl-and-notify end status=$status"
  exit "$status"
fi