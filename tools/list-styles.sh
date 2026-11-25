#!/usr/bin/env bash
# List styles with aliases, status, sample count and whether a learned profile exists.
# Usage: tools/list-styles.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
printf '%-14s %-8s %-15s %-8s %-8s %s\n' STYLE LANG STATUS SAMPLES LEARNED ALIASES
for d in "$ROOT"/references/*/; do
  s="$(basename "$d")"
  case "$s" in _*) continue ;; esac
  f="$d/style.md"
  [ -f "$f" ] || { printf '%-14s %s\n' "$s" "(no style.md)"; continue; }
  field() { sed -n "s/^$1: *//p" "$f" | head -1; }
  n=0
  [ -d "$d/samples" ] && n="$(find "$d/samples" -type f -name '*.md' | wc -l | tr -d ' ')"
  l="no"; [ -f "$d/learned.md" ] && l="yes"
  printf '%-14s %-8s %-15s %-8s %-8s %s\n' "$s" "$(field language)" "$(field status)" "$n" "$l" "$(field aliases)"
done
