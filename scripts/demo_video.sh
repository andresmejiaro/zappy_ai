#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEMO_HOST="${DEMO_HOST:-127.0.0.1}"
DEMO_PORT="${DEMO_PORT:-4242}"
DEMO_TEAM="${DEMO_TEAM:-pollo}"
DEMO_WIDTH="${DEMO_WIDTH:-10}"
DEMO_HEIGHT="${DEMO_HEIGHT:-10}"
DEMO_AGENTS="${DEMO_AGENTS:-16}"
DEMO_SLOTS="${DEMO_SLOTS:-4}"
DEMO_TICK="${DEMO_TICK:-100}"
DEMO_LOG_DIR="${DEMO_LOG_DIR:-$ROOT_DIR/.local/demo}"
DEMO_MODE="${DEMO_MODE:-1}"
DEMO_RECORD_PROTOCOL="${DEMO_RECORD_PROTOCOL:-}"
DEMO_REPLAY_FILE="${DEMO_REPLAY_FILE:-}"
DEMO_VIDEO_SECONDS="${DEMO_VIDEO_SECONDS:-20}"
DEMO_VIDEO_WARMUP="${DEMO_VIDEO_WARMUP:-8}"
DEMO_VIDEO_FPS="${DEMO_VIDEO_FPS:-30}"
DEMO_VIDEO_OUT="${DEMO_VIDEO_OUT:-}"
GODOT_ARGS="${GODOT_ARGS:-}"
VIDEO_DIR="$DEMO_LOG_DIR/video"
GUI_LOG="$DEMO_LOG_DIR/gui.log"
DISPLAY_NAME="${DISPLAY:-}"
WINDOW_TITLE="Zappy Demo"

DEMO_PID=""

cleanup() {
  local status=$?
  trap - EXIT INT TERM

  if [[ -n "$DEMO_PID" ]]; then
    kill "$DEMO_PID" 2>/dev/null || true
    wait "$DEMO_PID" 2>/dev/null || true
  fi

  exit "$status"
}

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  fi
}

wait_for_log() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  local timeout="${4:-20}"
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
    tail -n 60 "$file" >&2
  fi
  exit 1
}

find_window_id() {
  xwininfo -root -tree | awk -v title="$WINDOW_TITLE" '
    $0 ~ "\"" title "\"" { print $1; found=1; exit }
    END { if (!found) exit 1 }
  ' || xwininfo -root -tree | awk '
    tolower($0) ~ /"godot/ { print $1; exit }
  '
}

wait_for_window() {
  local timeout="${1:-20}"
  local elapsed=0
  local window_id=""

  while (( elapsed < timeout )); do
    window_id="$(find_window_id || true)"
    if [[ -n "$window_id" ]]; then
      printf '%s\n' "$window_id"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  printf 'Timed out waiting for the "%s" window.\n' "$WINDOW_TITLE" >&2
  if [[ -f "$GUI_LOG" ]]; then
    tail -n 60 "$GUI_LOG" >&2
  fi
  exit 1
}

read_window_geometry() {
  local window_id="$1"
  local info
  local x
  local y
  local width
  local height

  info="$(xwininfo -id "$window_id")"
  x="$(printf '%s\n' "$info" | awk -F: '/Absolute upper-left X/ {gsub(/ /, "", $2); print $2}')"
  y="$(printf '%s\n' "$info" | awk -F: '/Absolute upper-left Y/ {gsub(/ /, "", $2); print $2}')"
  width="$(printf '%s\n' "$info" | awk -F: '/Width/ {gsub(/ /, "", $2); print $2}')"
  height="$(printf '%s\n' "$info" | awk -F: '/Height/ {gsub(/ /, "", $2); print $2}')"

  if [[ -z "$x" || -z "$y" || -z "$width" || -z "$height" ]]; then
    printf 'Failed to resolve the Godot window geometry.\n' >&2
    printf '%s\n' "$info" >&2
    exit 1
  fi

  printf '%s %s %s %s\n' "$x" "$y" "$width" "$height"
}

trap cleanup EXIT INT TERM

require_command ffmpeg
require_command ffprobe
require_command xwininfo
require_command rg

if [[ -z "$DISPLAY_NAME" ]]; then
  printf 'DISPLAY is not set. Window capture requires an X11 display.\n' >&2
  exit 1
fi

if [[ "$GODOT_ARGS" == *"--headless"* ]]; then
  printf 'Headless mode cannot produce a video capture. Remove --headless from GODOT_ARGS.\n' >&2
  exit 1
fi

if [[ -n "$DEMO_REPLAY_FILE" && ! -f "$DEMO_REPLAY_FILE" ]]; then
  printf 'Replay file not found: %s\n' "$DEMO_REPLAY_FILE" >&2
  exit 1
fi

mkdir -p "$VIDEO_DIR"

if [[ -z "$DEMO_VIDEO_OUT" ]]; then
  timestamp="$(date +%Y%m%d-%H%M%S)"
  if [[ -n "$DEMO_REPLAY_FILE" ]]; then
    DEMO_VIDEO_OUT="$VIDEO_DIR/zappy-replay-$timestamp.mp4"
  else
    DEMO_VIDEO_OUT="$VIDEO_DIR/zappy-demo-$timestamp.mp4"
  fi
fi

printf 'Video output: %s\n' "$DEMO_VIDEO_OUT"
printf 'Starting demo launcher...\n'

(
  cd "$ROOT_DIR"
  DEMO_HOST="$DEMO_HOST" \
    DEMO_PORT="$DEMO_PORT" \
    DEMO_TEAM="$DEMO_TEAM" \
    DEMO_WIDTH="$DEMO_WIDTH" \
    DEMO_HEIGHT="$DEMO_HEIGHT" \
    DEMO_AGENTS="$DEMO_AGENTS" \
    DEMO_SLOTS="$DEMO_SLOTS" \
    DEMO_TICK="$DEMO_TICK" \
    DEMO_LOG_DIR="$DEMO_LOG_DIR" \
    DEMO_MODE="$DEMO_MODE" \
    DEMO_RECORD_PROTOCOL="$DEMO_RECORD_PROTOCOL" \
    DEMO_REPLAY_FILE="$DEMO_REPLAY_FILE" \
    GODOT_ARGS="$GODOT_ARGS" \
    ./scripts/demo_full.sh
) &
DEMO_PID="$!"

if [[ -n "$DEMO_REPLAY_FILE" ]]; then
  wait_for_log "$GUI_LOG" "SceneLoaded!!!!" "GUI replay scene" 30
else
  wait_for_log "$GUI_LOG" "Connected to server" "GUI connection" 30
  wait_for_log "$GUI_LOG" "SceneLoaded!!!!" "GUI scene load" 30
fi

printf 'Warming up the scene for %ss...\n' "$DEMO_VIDEO_WARMUP"
sleep "$DEMO_VIDEO_WARMUP"

WINDOW_ID="$(wait_for_window 60)"
CAPTURE_WINDOW_ID="$WINDOW_ID"
read -r WINDOW_X WINDOW_Y WINDOW_WIDTH WINDOW_HEIGHT < <(read_window_geometry "$CAPTURE_WINDOW_ID")

printf 'Recording %ss at %sfps from %s (window %s, %sx%s at +%s,+%s)...\n' \
  "$DEMO_VIDEO_SECONDS" "$DEMO_VIDEO_FPS" "$WINDOW_TITLE" "$CAPTURE_WINDOW_ID" "$WINDOW_WIDTH" "$WINDOW_HEIGHT" "$WINDOW_X" "$WINDOW_Y"

ffmpeg -y \
  -f x11grab \
  -draw_mouse 0 \
  -framerate "$DEMO_VIDEO_FPS" \
  -window_id "$CAPTURE_WINDOW_ID" \
  -i "$DISPLAY_NAME" \
  -t "$DEMO_VIDEO_SECONDS" \
  -vf "crop=w='trunc(if(gt(iw/ih\,16/9)\,ih*16/9\,iw)/2)*2':h='trunc(if(gt(iw/ih\,16/9)\,ih\,iw*9/16)/2)*2',scale=1920:1080" \
  -c:v libx264 \
  -crf 18 \
  -preset fast \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$DEMO_VIDEO_OUT"

printf 'Stopping demo launcher...\n'
kill "$DEMO_PID" 2>/dev/null || true
wait "$DEMO_PID" 2>/dev/null || true
DEMO_PID=""

printf 'Capture complete.\n'
ffprobe -v error \
  -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate \
  -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=0 \
  "$DEMO_VIDEO_OUT"
