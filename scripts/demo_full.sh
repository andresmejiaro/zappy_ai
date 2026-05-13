#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEMO_HOST="${DEMO_HOST:-127.0.0.1}"
DEMO_PORT="${DEMO_PORT:-4242}"
DEMO_TEAM="${DEMO_TEAM:-pollo}"
DEMO_WIDTH="${DEMO_WIDTH:-10}"
DEMO_HEIGHT="${DEMO_HEIGHT:-10}"
DEMO_AGENTS="${DEMO_AGENTS:-${N:-16}}"
DEMO_SLOTS="${DEMO_SLOTS:-4}"
DEMO_TICK="${DEMO_TICK:-100}"
DEMO_LOG_DIR="${DEMO_LOG_DIR:-$ROOT_DIR/.local/demo}"
DEMO_GUI_DELAY="${DEMO_GUI_DELAY:-4}"
DEMO_AGENT_DELAY="${DEMO_AGENT_DELAY:-0.15}"
GODOT_ARGS="${GODOT_ARGS:-}"
DEMO_MODE="${DEMO_MODE:-}"
DEMO_RECORD_PROTOCOL="${DEMO_RECORD_PROTOCOL:-}"
DEMO_REPLAY_FILE="${DEMO_REPLAY_FILE:-}"
DEMO_SKIP_SERVER="${DEMO_SKIP_SERVER:-0}"
DEMO_SKIP_AI="${DEMO_SKIP_AI:-0}"

if [[ -n "$DEMO_REPLAY_FILE" ]]; then
  DEMO_SKIP_SERVER=1
  DEMO_SKIP_AI=1
fi

SERVER_LOG="$DEMO_LOG_DIR/server.log"
GUI_LOG="$DEMO_LOG_DIR/gui.log"
AI_LOG_DIR="$DEMO_LOG_DIR/ai"
SERVER_STDIN_PIPE="$DEMO_LOG_DIR/server.stdin.pipe"
PIDS=()

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if ((${#PIDS[@]})); then
    printf '\nStopping demo processes...\n'
    kill "${PIDS[@]}" 2>/dev/null || true
    wait "${PIDS[@]}" 2>/dev/null || true
  fi
  rm -f "$SERVER_STDIN_PIPE"
  exit "$status"
}

wait_for_log() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  local timeout="${4:-10}"
  local elapsed=0

  while (( elapsed < timeout )); do
    if [[ -f "$file" ]] && rg -q "$pattern" "$file"; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  printf '%s did not become ready within %ss. Last log lines:\n' "$label" "$timeout" >&2
  if [[ -f "$file" ]]; then
    tail -n 40 "$file" >&2
  else
    printf 'No log file created: %s\n' "$file" >&2
  fi
  return 1
}

check_port_available() {
  if command -v ss >/dev/null 2>&1; then
    if ss -ltn "( sport = :$DEMO_PORT )" | rg -q "LISTEN"; then
      printf 'Port %s is already in use. Stop the existing server or set DEMO_PORT.\n' "$DEMO_PORT" >&2
      return 1
    fi
  fi
}

trap cleanup EXIT INT TERM

mkdir -p "$AI_LOG_DIR"
rm -f "$SERVER_LOG" "$GUI_LOG" "$AI_LOG_DIR"/*.log
rm -f "$SERVER_STDIN_PIPE"

cd "$ROOT_DIR"

if [[ "$DEMO_SKIP_SERVER" != "1" ]]; then
  test -x "$ROOT_DIR/external/zappy/server"
fi
if [[ "$DEMO_SKIP_AI" != "1" ]]; then
  test -x "$ROOT_DIR/.venv/bin/python"
fi
GODOT_BIN="$("$ROOT_DIR/scripts/find_godot.sh")"

printf 'Logs: %s\n' "$DEMO_LOG_DIR"
if [[ -n "$DEMO_REPLAY_FILE" ]]; then
  printf 'Replay mode: %s\n' "$DEMO_REPLAY_FILE"
fi

if [[ "$DEMO_SKIP_SERVER" != "1" ]]; then
  check_port_available
  printf 'Starting server: port=%s map=%sx%s team=%s slots=%s tick=%s\n' \
    "$DEMO_PORT" "$DEMO_WIDTH" "$DEMO_HEIGHT" "$DEMO_TEAM" "$DEMO_SLOTS" "$DEMO_TICK"
  mkfifo "$SERVER_STDIN_PIPE"
  tail -f /dev/null >"$SERVER_STDIN_PIPE" &
  PIDS+=("$!")
  "$ROOT_DIR/external/zappy/server" \
    -p "$DEMO_PORT" \
    -x "$DEMO_WIDTH" \
    -y "$DEMO_HEIGHT" \
    -n "$DEMO_TEAM" \
    -c "$DEMO_SLOTS" \
    -t "$DEMO_TICK" <"$SERVER_STDIN_PIPE" >"$SERVER_LOG" 2>&1 &
  PIDS+=("$!")
  rm -f "$SERVER_STDIN_PIPE"

  wait_for_log "$SERVER_LOG" "Server listening on port $DEMO_PORT" "server" 15
  printf 'Server ready.\n'
else
  printf 'Skipping server startup.\n'
fi

printf 'Starting GUI with Godot: %s\n' "$GODOT_BIN"
GODOT_BIN="$GODOT_BIN" "$ROOT_DIR/scripts/run_gui.sh" $GODOT_ARGS >"$GUI_LOG" 2>&1 &
PIDS+=("$!")

if [[ "$GODOT_ARGS" == *"--headless"* ]]; then
  if [[ -n "$DEMO_REPLAY_FILE" ]]; then
    wait_for_log "$GUI_LOG" "SceneLoaded!!!!" "GUI replay scene" 20
    printf 'GUI replay scene loaded in headless verification mode.\n'
  else
    wait_for_log "$GUI_LOG" "Connected to server" "GUI" 20
    printf 'GUI connected in headless verification mode.\n'
  fi
else
  printf 'Waiting %ss for the GUI window to connect before launching agents...\n' "$DEMO_GUI_DELAY"
  sleep "$DEMO_GUI_DELAY"
fi

if [[ "$DEMO_SKIP_AI" != "1" ]]; then
  if (( DEMO_AGENTS > DEMO_SLOTS )); then
    printf 'Starting %s AI clients for team %s (%s initial slots; %s bench clients wait for eggs)...\n' \
      "$DEMO_AGENTS" "$DEMO_TEAM" "$DEMO_SLOTS" "$((DEMO_AGENTS - DEMO_SLOTS))"
  else
    printf 'Starting %s AI clients for team %s...\n' "$DEMO_AGENTS" "$DEMO_TEAM"
  fi
  for i in $(seq 1 "$DEMO_AGENTS"); do
    "$ROOT_DIR/.venv/bin/python" -m zappy_ai.client \
      -h "$DEMO_HOST" \
      -p "$DEMO_PORT" \
      -n "$DEMO_TEAM" >"$AI_LOG_DIR/ai-$i.log" 2>&1 &
    PIDS+=("$!")
    sleep "$DEMO_AGENT_DELAY"
  done
else
  printf 'Skipping AI startup.\n'
fi

printf 'Demo running.\n'
printf 'Server log: %s\n' "$SERVER_LOG"
printf 'GUI log: %s\n' "$GUI_LOG"
printf 'AI logs: %s/ai-*.log\n' "$AI_LOG_DIR"
printf 'Stop with Ctrl+C.\n'

wait
