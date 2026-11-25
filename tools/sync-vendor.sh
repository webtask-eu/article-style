#!/usr/bin/env bash
# Re-copy MIT-licensed upstream skills into vendor/ and rebuild vendor/SOURCES.tsv.
# Usage: tools/sync-vendor.sh   (needs git, rsync, network)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

T=""
if command -v gtimeout >/dev/null 2>&1; then T="gtimeout 120"; elif command -v timeout >/dev/null 2>&1; then T="timeout 120"; fi

# name|owner/repo|paths copied (space separated, relative to repo root)
SOURCES="humanizer|blader/humanizer|SKILL.md
infostyle-skill|artgas1/infostyle-skill|skills/infostyle
economist-style-guide-plugin|TAJD/economist-style-guide-plugin|economist-style/skills/economist-style
claude-skills-journalism|jamditis/claude-skills-journalism|journalism-core/skills/newsroom-style journalism-core/skills/fact-check-workflow journalism-core/skills/source-verification journalism-core/skills/story-pitch journalism-core/skills/editorial-workflow
ru-text|talkstream/ru-text|skills"

mkdir -p "$ROOT/vendor"
OUT="$TMP/SOURCES.tsv"
printf 'name\trepo\tcommit\tlicense\tsynced\n' > "$OUT"

echo "$SOURCES" | while IFS='|' read -r name repo paths; do
  [ -n "$name" ] || continue
  echo "sync $name <- $repo"
  $T git clone -q --depth 1 "https://github.com/$repo.git" "$TMP/$name"
  grep -q "MIT License" "$TMP/$name/LICENSE" || { echo "error: $name LICENSE is not MIT, stop" >&2; exit 1; }
  commit="$(git -C "$TMP/$name" rev-parse --short HEAD)"
  dest="$TMP/out/$name"
  mkdir -p "$dest"
  # shellcheck disable=SC2086
  (cd "$TMP/$name" && rsync -aR --exclude='agents/' --exclude='.git/' $paths "$dest/")
  cp "$TMP/$name/LICENSE" "$dest/LICENSE"
  printf '%s\t%s\t%s\tMIT\t%s\n' "$name" "$repo" "$commit" "$(date +%Y-%m-%d)" >> "$OUT"
done

for d in "$TMP"/out/*/; do
  n="$(basename "$d")"
  rm -rf "$ROOT/vendor/$n"
  cp -R "$d" "$ROOT/vendor/$n"
done
cp "$OUT" "$ROOT/vendor/SOURCES.tsv"
echo "done: $(($(wc -l < "$OUT") - 1)) sources in vendor/"
