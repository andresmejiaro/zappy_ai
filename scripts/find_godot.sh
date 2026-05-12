#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${GODOT_BIN:-}" ]]; then
  if [[ -x "${GODOT_BIN}" ]]; then
    printf '%s\n' "${GODOT_BIN}"
    exit 0
  fi
  printf 'Configured GODOT_BIN is not executable: %s\n' "${GODOT_BIN}" >&2
  exit 1
fi

for candidate in \
  "$(command -v godot4 2>/dev/null || true)" \
  "$(command -v godot 2>/dev/null || true)" \
  "$HOME/Godot/Godot_v4.6.1-stable_linux.x86_64"
do
  if [[ -n "${candidate}" && -x "${candidate}" ]]; then
    printf '%s\n' "${candidate}"
    exit 0
  fi
done

if [[ -d "$HOME/Godot" ]]; then
  while IFS= read -r candidate; do
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      exit 0
    fi
  done < <(find "$HOME/Godot" -maxdepth 2 -type f -name 'Godot*' | sort)
fi

printf 'Could not find a Godot executable. Set GODOT_BIN or install godot4/godot.\n' >&2
exit 1
