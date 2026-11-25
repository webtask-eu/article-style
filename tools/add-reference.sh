#!/usr/bin/env bash
# Save an article as a reference sample for a style.
# Usage: tools/add-reference.sh <style> <file|-> [--source URL] [--title TEXT] [--lang ru|en] [--tags a,b]
# Creates references/<style>/ from _template if the style is new. Reads stdin when file is "-".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
die() { echo "error: $1" >&2; exit "${2:-1}"; }
[ $# -ge 2 ] || die "usage: add-reference.sh <style> <file|-> [--source URL] [--title TEXT] [--lang ru|en] [--tags a,b]" 2

style="$1"; file="$2"; shift 2
source_url=""; title=""; lang=""; tags=""
while [ $# -gt 0 ]; do
  [ $# -ge 2 ] || die "option $1 needs a value" 2
  case "$1" in
    --source) source_url="$2" ;;
    --title)  title="$2" ;;
    --lang)   lang="$2" ;;
    --tags)   tags="$2" ;;
    *) die "unknown option: $1" 2 ;;
  esac
  shift 2
done

case "$style" in
  [a-z0-9]*) ;;
  *) die "style must match [a-z0-9][a-z0-9_-]* (lowercase latin)" 2 ;;
esac
case "$style" in *[!a-z0-9_-]*) die "style must match [a-z0-9][a-z0-9_-]* (lowercase latin)" 2 ;; esac
[ -z "$lang" ] || case "$lang" in ru|en) ;; *) die "--lang must be ru or en" 2 ;; esac

clean() { printf '%s' "$1" | LC_ALL=C tr -d '\000-\037"\\' ; }

dir="$ROOT/references/$style"
if [ -z "$lang" ]; then
  lang="ru"
  [ -f "$dir/style.md" ] && l="$(sed -n 's/^language: *//p' "$dir/style.md" | head -1)" && [ -n "$l" ] && lang="$l"
fi

tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
if [ "$file" = "-" ]; then
  cat > "$tmp"
else
  [ -f "$file" ] || die "file not found: $file"
  cat -- "$file" > "$tmp"
fi
[ -s "$tmp" ] || die "empty input"
[ "$(wc -c < "$tmp")" -le 500000 ] || die "sample larger than 500 KB"
iconv -f UTF-8 -t UTF-8 "$tmp" > /dev/null 2>&1 || die "input is not valid UTF-8 text (convert it first)"
[ "$(LC_ALL=C tr -d '\000' < "$tmp" | wc -c)" = "$(wc -c < "$tmp")" ] || die "input looks binary"

if [ ! -d "$dir" ]; then
  cp -R "$ROOT/references/_template" "$dir"
  sed -i.bak "s/^name: .*/name: $style/; s/^aliases: .*/aliases: [$style]/; s/^language: .*/language: $lang/" "$dir/style.md"
  rm -f "$dir/style.md.bak"
  echo "created style: references/$style"
fi
mkdir -p "$dir/samples"

base="$(clean "$title")"
[ -n "$base" ] || { [ "$file" = "-" ] && base="sample" || base="$(clean "$(basename "$file")")"; }
slug="$(printf '%s' "$base" | sed 's/\.[A-Za-z0-9]*$//' | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed 's/[^a-z0-9]\{1,\}/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -n "$slug" ] || slug="sample"
out="$dir/samples/$(date +%Y-%m-%d)-$slug.md"
n=2; while [ -e "$out" ]; do out="$dir/samples/$(date +%Y-%m-%d)-$slug-$n.md"; n=$((n + 1)); done

{
  echo "---"
  echo "title: \"$base\""
  echo "source: \"$(clean "$source_url")\""
  echo "added: $(date +%Y-%m-%d)"
  echo "language: $lang"
  echo "tags: [$(clean "$tags")]"
  echo "---"
  echo
  cat "$tmp"
} > "$out"
echo "saved: ${out#"$ROOT"/}"
