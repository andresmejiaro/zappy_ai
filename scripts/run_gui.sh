#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT_BIN="${GODOT_BIN:-$("$ROOT_DIR/scripts/find_godot.sh")}"

printf 'Using Godot: %s\n' "$GODOT_BIN"
exec env ZAPPY_REPO_ROOT="$ROOT_DIR" "$GODOT_BIN" --path "$ROOT_DIR/external/ZAPPY_GC" "$@"
