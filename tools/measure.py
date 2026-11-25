#!/usr/bin/env python3
"""Prose-shape metrics for reference samples (read-only).

Usage: python3 -I tools/measure.py <style-dir | sample.md> [...]
Prints one JSON object: per-file metrics (by file name) and the median across files.
A style folder is measured through its samples/ subfolder only.
"""
import json
import pathlib
import re
import statistics
import sys

WORD = re.compile(r"\w+(?:[-']\w+)*")
NUMBER = re.compile(r"\d+(?:[   ]\d{3})*(?:[.,]\d+)?")
LIST_LINE = re.compile(r"^\s*(?:\d{1,2}[.)]\s|[-*]\s)|^\s{2,}\S")
KEYLINE = re.compile(r"^[\w-]+:|^\s+-\s|^\s*#|^\s*$")
ABBR = re.compile(
    r"(?<!\w)(?:г|гг|т\.\s?[екдп]|др|пр|см|рис|тыс|млн|млрд|руб|ул|им|напр|англ|Mr|Mrs|Dr|vs|etc|e\.g|i\.e)\."
    r"|(?<!\w)[A-ZА-ЯЁ]\.(?=\s?[A-ZА-ЯЁ])"
)


def strip_front_matter(text):
    while text.startswith("---"):
        m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
        if not m or not all(KEYLINE.match(line) for line in m.group(1).split("\n")):
            break
        text = text[m.end():]
    return text


def sentences(par):
    masked = ABBR.sub(lambda m: m.group(0).replace(".", "․"), par)
    parts = re.split(r"(?<=[.!?…])\s+(?=[«\"“„(\[—–A-ZА-ЯЁ0-9])", masked)
    return [p for p in parts if re.search(r"\w", p)]


def metrics(raw):
    text = strip_front_matter(raw.replace("\r\n", "\n")).strip()
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"^(#.*)$", r"\1\n", text, flags=re.M)
    raw_blocks = [b for b in re.split(r"\n[ \t]*\n", text) if b.strip()]
    blocks = [b.strip() for b in raw_blocks]
    heads = [b for b in blocks if b.startswith("#")]
    paras = []
    for raw in raw_blocks:
        b = raw.strip("\n")
        if b.lstrip().startswith(("#", ">", "|")):
            continue
        body = "\n".join(l for l in b.split("\n") if not LIST_LINE.match(l)).strip()
        if body and not re.fullmatch(r"[-*_]{3,}", body) and not re.fullmatch(r"\[[^\]]{0,200}\]", body):
            paras.append(body)
    sents = [s for p in paras for s in sentences(p)]
    words = WORD.findall(text)
    swords = [len(WORD.findall(s)) for s in sents] or [0]
    pwords = [len(WORD.findall(p)) for p in paras] or [0]
    n_words = max(len(words), 1)
    openers = text.count("«") + text.count("„") + max(text.count("“") - text.count("„"), 0) + text.count('"') // 2
    return {
        "words": len(words),
        "paragraphs": len(paras),
        "headings": len(heads),
        "list_items": len(re.findall(r"^\s*(?:[-*]|\d+\.)\s", text, re.M)),
        "words_per_sentence_avg": round(statistics.mean(swords), 1),
        "words_per_sentence_max": max(swords),
        "words_per_paragraph_avg": round(statistics.mean(pwords), 1),
        "numbers_per_1000_words": round(1000 * len(NUMBER.findall(text)) / n_words, 1),
        "quotes_per_1000_words": round(1000 * openers / n_words, 1),
        "questions": text.count("?"),
        "dashes_per_1000_words": round(1000 * len(re.findall(r"[—–]", text)) / n_words, 1),
    }


def collect(arg):
    p = pathlib.Path(arg)
    if p.is_dir():
        if (p / "samples").is_dir():
            return sorted(p.glob("samples/**/*.md"))
        if (p / "style.md").exists():
            return []
        return sorted(p.rglob("*.md"))
    return [p]


def main(argv):
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    files = [f for a in argv for f in collect(a)]
    if not files:
        print(json.dumps({"files": 0, "note": "no samples found"}))
        return 0
    per = {}
    for f in files:
        name = f.name
        while name in per:
            name = "_" + name
        per[name] = metrics(f.read_text(encoding="utf-8", errors="replace"))
    keys = next(iter(per.values())).keys()
    median = {k: round(statistics.median(v[k] for v in per.values()), 1) for k in keys}
    print(json.dumps({"files": len(files), "median": median, "per_file": per}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
