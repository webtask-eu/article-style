#!/usr/bin/env bash
# Structure check: styles, vendor licenses, paths named in SKILL.md, sample hygiene, stray big files.
# Usage: tools/check.sh   (exit 1 on any problem; WARN lines do not fail)
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
bad=0
fail() { echo "FAIL: $*" >&2; bad=1; }
warn() { echo "WARN: $*" >&2; }

for d in references/*/; do
  s="$(basename "$d")"
  f="$d/style.md"
  [ -f "$f" ] || { fail "$s: style.md missing"; continue; }
  case "$s" in _*) continue ;; esac
  for k in name aliases language status; do grep -q "^$k:" "$f" || fail "$s: front matter field '$k' missing"; done
  [ "$(sed -n 's/^name: *//p' "$f" | head -1)" = "$s" ] || fail "$s: front matter name differs from folder"
  [ -d "$d/samples" ] || fail "$s: samples/ missing"
  [ ! -L "${d%/}/samples" ] || fail "$s: samples/ is a symlink (its target path would reach git)"
done

for d in vendor/*/; do
  [ -f "$d/LICENSE" ] || fail "$d: LICENSE missing"
  grep -q "MIT License" "$d/LICENSE" 2>/dev/null || fail "$d: LICENSE is not MIT"
done
[ -f vendor/SOURCES.tsv ] || fail "vendor/SOURCES.tsv missing"

for p in $(grep -oE '(vendor|tools|references|rules)/[A-Za-z0-9_./-]*[A-Za-z0-9_]' SKILL.md | sort -u); do
  case "$p" in *'<'*) continue ;; esac
  [ -e "$p" ] || fail "SKILL.md names missing path $p"
done

python3 -I tools/rules.py check || fail "rules.py check failed"
[ -z "$(git ls-files rules.local.md 2>/dev/null)" ] || fail "rules.local.md is tracked by git (personal file)"
if git rev-parse --git-dir >/dev/null 2>&1; then
  git check-ignore -q rules.local.md || fail "rules.local.md is not ignored by git"
  git check-ignore -q drafts/x.md || warn "drafts/ is not ignored by git"
fi

grep -q '^references/\*/samples/\*' .gitignore || warn ".gitignore does not exclude sample texts"
if git rev-parse --git-dir >/dev/null 2>&1; then
  t="$(git ls-files 'references/*/samples/*' | grep -v '/\.gitkeep$' | wc -l | tr -d ' ')"
  [ "$t" = "0" ] || warn "$t sample files are tracked by git (they go public with the repo)"
fi

big="$(find . \( -path ./.git -o -path './references/*/samples' \) -prune -o -type f -size +400k -print)"
[ -z "$big" ] || fail "files over 400 KB: $big"

[ "$bad" -eq 0 ] && echo "check: ok" || exit 1
