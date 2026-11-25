#!/usr/bin/env python3
"""Rules of the article-style skill: show them, validate the files, audit a draft.

Usage:
  python3 -I tools/rules.py show <style>
  python3 -I tools/rules.py check
  python3 -I tools/rules.py audit <draft.md> <style> [--lang ru|en] [--genre profile|essay|interview]

Files: rules/global.md, references/<style>/rules.md, rules.local.md (personal, not in git).
rules.local.md lines:  off: F5 G9  |  on: F8  |  + forbes: rule text  |  + all: rule text
  The last on:/off: line for a number wins. Personal rules get numbers MY1, MY2, ...
Exit codes: 0 ok, 1 a scripted rule failed (✗; ⚠ means "look by eye", not a failure), 2 usage or file error.
rules.md front matter: targets=... | targets_ru=... | targets_en=... | targets_<genre>=...
  (words_per_sentence, words_per_paragraph, tolerance); picked by --genre, then language, then plain targets.
"""
import importlib.util
import math
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent
RULE_START = re.compile(r"^- \[[ xX]\] ")
RULE = re.compile(r"^- \[( |x|X)\] ([A-Z]+[0-9]+) · (auto|model) · (.+)$")
RULE_ID = re.compile(r"[A-Za-z]+[0-9]+")
SPACES = "   "


class UserError(Exception):
    pass


def read(path):
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def read_lenient(path):
    return path.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")


def load_measure():
    spec = importlib.util.spec_from_file_location("measure", ROOT / "tools" / "measure.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_front(text):
    meta = {}
    m = re.match(r"---\n(.*?)\n---(?:\n|$)", text, re.S)
    if m:
        for line in m.group(1).split("\n"):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta


def parse_rules(path):
    text = read(path)
    rules = []
    for n, line in enumerate(text.split("\n"), 1):
        if RULE_START.match(line):
            m = RULE.match(line)
            if not m:
                raise UserError("%s/%s:%d bad rule line (ID must be Latin capitals + digits, type auto|model): %s"
                                % (path.parent.name, path.name, n, line[:70]))
            rules.append({"id": m.group(2), "on": m.group(1) != " ", "kind": m.group(3), "text": m.group(4)})
    return read_front(text), rules


def parse_targets(s):
    out = {}
    for part in s.split():
        k, sep, v = part.partition("=")
        try:
            if not sep:
                raise ValueError
            x = float(v.replace(",", "."))
        except ValueError:
            raise UserError("bad targets value: %s" % part)
        if not math.isfinite(x) or x <= 0:
            raise UserError("targets value must be a positive number: %s" % part)
        out[k] = x
    return out


def styles():
    return sorted(p.name for p in (ROOT / "references").iterdir() if p.is_dir() and not p.name.startswith("_"))


def parse_local():
    states, adds, warns = {}, [], []
    path = ROOT / "rules.local.md"
    if not path.exists():
        return states, adds, warns
    try:
        text = read(path)
    except (OSError, UnicodeDecodeError) as e:
        return states, adds, ["файл не прочитан (%s), пропущен" % type(e).__name__]
    for n, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        low = s.lower()
        if low.startswith("off:") or low.startswith("on:"):
            for tok in re.split(r"[\s,;]+", s.split(":", 1)[1].strip()):
                if not tok:
                    continue
                if RULE_ID.fullmatch(tok):
                    states[tok.upper()] = low.startswith("on:")
                else:
                    warns.append("строка %d: непонятный номер «%s» (нужны латинские буквы и цифры)" % (n, tok))
        elif s.startswith("+"):
            scope, sep, txt = s[1:].partition(":")
            scope = scope.strip().lower()
            if not sep or not txt.strip():
                warns.append("строка %d: нет двоеточия или текста, пропущена" % n)
            elif scope != "all" and scope not in styles():
                warns.append("строка %d: неизвестный стиль «%s», пропущена" % (n, scope))
            else:
                adds.append({"id": "MY%d" % (len(adds) + 1), "on": True, "kind": "model", "scope": scope, "text": txt.strip()})
        else:
            warns.append("строка %d: не понял, пропущена" % n)
    return states, adds, warns


def load(style):
    if style not in styles():
        raise UserError("unknown style '%s' (have: %s)" % (style, ", ".join(styles())))
    _, glob = parse_rules(ROOT / "rules" / "global.md")
    p = ROOT / "references" / style / "rules.md"
    meta, own = parse_rules(p) if p.exists() else ({}, [])
    states, adds, warns = parse_local()
    adds = [a for a in adds if a["scope"] in ("all", style)]
    for r in glob + own + adds:
        if r["id"] in states:
            r["on"] = states[r["id"]]
    return glob, own, adds, meta, states, warns


def all_ids():
    _, glob = parse_rules(ROOT / "rules" / "global.md")
    ids = [r["id"] for r in glob]
    for s in styles():
        p = ROOT / "references" / s / "rules.md"
        if p.exists():
            ids += [r["id"] for r in parse_rules(p)[1]]
    return ids


def unknown_ids(states, adds_all):
    return sorted(set(states) - set(all_ids()) - {a["id"] for a in adds_all})


def show(style):
    glob, own, adds, _, states, warns = load(style)
    sm = ROOT / "references" / style
    status = read_front(read(sm / "style.md")).get("status", "?") if (sm / "style.md").exists() else "?"
    n = len(list((sm / "samples").rglob("*.md"))) if (sm / "samples").is_dir() else 0
    print("Стиль: %s · статус %s · образцов %d" % (style, status, n))
    print("Приоритет: запрос в чате > rules.local.md > rules.md стиля > rules/global.md > style.md и learned.md\n")
    for title, items in (("Общие (rules/global.md)", glob), ("Стиль %s (references/%s/rules.md)" % (style, style), own),
                         ("Личные (rules.local.md)", adds)):
        if not items:
            continue
        print(title)
        for r in items:
            tag = "[%s] " % r["scope"] if "scope" in r else ""
            print("  %-4s %-5s %-7s %s%s" % (r["id"], "вкл" if r["on"] else "выкл",
                                              "скрипт" if r["kind"] == "auto" else "модель", tag, r["text"]))
        print()
    off = [r["id"] for r in glob + own + adds if not r["on"]]
    if off:
        print("Выключено: " + ", ".join(off))
    for i in unknown_ids(states, parse_local()[1]):
        warns.append("неизвестный номер %s" % i)
    for w in warns:
        print("Проблема в rules.local.md: " + w)


def check():
    bad, notes = [], []
    _, glob = parse_rules(ROOT / "rules" / "global.md")
    ids = [r["id"] for r in glob]
    allrules = list(glob)
    for s in styles():
        p = ROOT / "references" / s / "rules.md"
        if not p.exists():
            bad.append("%s: rules.md missing (add a sample with tools/add-reference.sh to restore it)" % s)
            continue
        meta, own = parse_rules(p)
        if meta.get("style") != s:
            bad.append("%s: front matter style differs from folder" % s)
        for k, v in meta.items():
            if k.startswith("targets"):
                try:
                    parse_targets(v)
                except UserError as e:
                    bad.append("%s: %s" % (s, e))
        ids += [r["id"] for r in own]
        allrules += own
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        bad.append("duplicate rule ids: " + ", ".join(dup))
    for r in allrules:
        if r["kind"] == "auto" and r["id"] not in CHECKS:
            bad.append("%s is auto but has no check in rules.py" % r["id"])
    states, adds, warns = parse_local()
    for i in unknown_ids(states, adds):
        notes.append("rules.local.md: неизвестный номер %s" % i)
    notes += ["rules.local.md: " + w for w in warns]
    for b in bad:
        print("FAIL: " + b, file=sys.stderr)
    for n in notes:
        print("WARN: " + n, file=sys.stderr)
    if not bad:
        print("rules: ok (%d rules)" % len(ids))
    return 1 if bad else 0


def strip_code(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    return re.sub(r"`[^`\n]*`", " ", t)


def norm(t):
    for ch in SPACES:
        t = t.replace(ch, " ")
    return t.replace("’", "'").replace("‘", "'")


def no_quotes(t):
    return re.sub(r"«[^»]*»", " ", t)


def toks(t):
    return re.findall(r"\w+", norm(t).lower())


def hits(rx, text):
    return [re.sub(r"\s+", " ", m.group(0)).strip()[:50] for m in re.finditer(rx, text, re.I)]


def res(ok, detail=""):
    return ("✓" if ok else "✗", detail)


def warn(ok, detail=""):
    return ("✓", "") if ok else ("⚠", detail)


def c_g2(c):
    files = sorted((ROOT / "references" / c["style"] / "samples").rglob("*.md"))
    if not files:
        return ("–", "нет образцов")
    d = toks(c["text"])
    g = {tuple(d[i:i + 8]) for i in range(len(d) - 7)}
    found, where = 0, []
    for f in files:
        s = toks(f.read_text(encoding="utf-8", errors="replace"))
        for i in range(len(s) - 7):
            if tuple(s[i:i + 8]) in g:
                found += 1
                if len(where) < 2:
                    where.append("%s: «%s»" % (f.name[:30], " ".join(s[i:i + 8])))
    return res(found == 0, ("пересечений по 8 слов: %d; %s" % (found, "; ".join(where))) if found else "пересечений по 8 слов: 0")


def c_g6(c):
    if c["lang"] != "ru":
        return ("–", "только русский")
    t = no_quotes(c["plain"])
    hard = hits(r"\bявля(?:ется|ются|лся|лась|лось)\b|осуществля\w+|\bв\s+рамках\b|\bпредставля\w*\s+собой\b|"
                r"\bв\s+настоящее\s+время\b|\bна\s+сегодняшний\s+день\b|\bв\s+целях\b|"
                r"\bданн(?:ый|ая|ое|ого|ому|ой|ом|ую)\b", t)
    if hard:
        return ("✗", ", ".join(hard[:6]))
    soft = hits(r"\bочень\b|максимально|уникальн\w+|качественн\w+|инновацион\w+", t)
    return warn(not soft, "слова-усилители, проверьте глазами: " + ", ".join(soft[:6]))


def c_g7(c):
    rx = (r"\bне [^.!?;,\n—–]{0,40}(?:, а |, это | [—–] (?:а|это) )|\bне только [^.!?\n]{0,60}, но |"
          r"\bне потому,? что [^.!?\n]{0,60}, а потому|\bnot only [^.!?\n]{0,60}\bbut\b|"
          r"\bnot (?:just|only|merely) [^.!?\n]{0,60}[,;] ?(?:but|it's|it is)\b|"
          r"\b(?:it|this|that)(?: is|'s| isn't| is not) (?:not )?[^.!?\n]{0,60}[,;—–-]+ ?(?:it|this|that)(?: is|'s)\b")
    found = [h for h in hits(rx, c["plain"]) if re.search(r"\bне\b|\bnot\b|isn't", h, re.I)]
    return warn(not found, "проверьте глазами, обе части могут нести смысл: " + "; ".join(found[:4]))


def c_g9(c):
    if c["lang"] != "ru":
        return ("–", "только русский")
    lines = [l for l in c["raw_plain"].split("\n") if not l.lstrip().startswith("|") and not re.fullmatch(r"\s*[-*_]{3,}\s*", l)]
    t = re.sub(r"(?m)^\s*[-*] ", "", "\n".join(lines))
    outside = re.sub(r"«[^»]*»", " ", t)
    letter = "A-Za-zА-Яа-яЁё"
    prob = []
    for name, rx, src in (("прямые кавычки", r'"', t), ("кавычки не «» (вложенные „“ внутри «» допустимы)", r"[“”„]", outside),
                          ("« - » вместо тире", r"(?<=[%s)»]) - (?=[%s«(\d])" % (letter, letter), t),
                          ("« – » или « -- » вместо тире", r" – | -- ", t), ("тире без пробелов", r"[%s]—[%s]" % (letter, letter), t),
                          ("«...»", r"\.\.\.", t), ("тире без неразрывного пробела", r"[^\s] — ", t)):
        n = len(re.findall(rx, src))
        if n:
            prob.append("%s: %d" % (name, n))
    return res(not prob, "; ".join(prob))


def c_g10(c):
    tg = c["targets"]
    if "words_per_sentence" not in tg or "words_per_paragraph" not in tg:
        return ("–", "цели не заданы")
    m = load_measure().metrics(norm(strip_code(c["text"])))
    tol = tg.get("tolerance", 30.0)
    out, ok = [], True
    for key, name in (("words_per_sentence", "предложение"), ("words_per_paragraph", "абзац")):
        goal = tg[key]
        got = m[key + "_avg"]
        dev = (got - goal) / goal * 100
        ok = ok and abs(dev) <= tol
        out.append("%s %.1f (цель %.1f, %+.0f%%)" % (name, got, goal, dev))
    return res(ok, "; ".join(out) + ", допуск ±%.0f%%" % tol)


PROMO = {
    "F8": r"покупайте|продавайте|вкладывайтесь",
    "T8": r"покупайте|продавайте|гарантированн\w+ (?:доход|прибыл)|гарантир\w+ (?:доход|прибыл)|вы заработаете|"
          r"^\s*(?:buy|sell) now\b|guaranteed (?:profit|income|returns)",
}
NEGATION = re.compile(r"\bне\b|\bнет\b|\bни\b|\bбез\b|\bnever\b|\bno\b|\bnot\b|n't|\bwithout\b", re.I)


def c_promo(c):
    hard, soft = [], []
    for sent in re.split(r"(?<=[.!?])\s+|\n+", no_quotes(c["plain"])):
        found = hits(PROMO[c["rule"]], sent)
        if found:
            (soft if NEGATION.search(sent) else hard).extend(found)
    if hard:
        return ("✗", ", ".join(hard[:5]))
    return warn(not soft, "в предложении с отрицанием, проверьте глазами: " + ", ".join(soft[:5]))


def c_t9(c):
    if c["lang"] != "ru":
        return ("–", "только русский")
    t = no_quotes(c["plain"])
    t = "\n".join(l for l in t.split("\n") if not l.lstrip().startswith("— "))
    t = re.sub(r"\b[А-ЯЁ]\.\s?[А-ЯЁ]\.?", " ", t)
    h = hits(r"\b(?:я|мне|меня|мной|мною|мой|моя|моё|мое|мои|мою|моей|моего|моему|моим|моими|моих|мо[её]м)\b", t)
    return res(not h, ", ".join(h[:6]))


CHECKS = {"G2": c_g2, "G6": c_g6, "G7": c_g7, "G9": c_g9, "G10": c_g10, "F8": c_promo, "T8": c_promo, "T9": c_t9}


def pick_targets(meta, lang, genre):
    if genre:
        if not meta.get("targets_" + genre):
            have = sorted(k[8:] for k in meta if k.startswith("targets_") and k[8:] not in ("ru", "en"))
            raise UserError("no targets for genre '%s' in rules.md (have: %s)" % (genre, ", ".join(have) or "none"))
        return parse_targets(meta["targets_" + genre])
    return parse_targets(meta.get("targets_" + lang) or meta.get("targets", ""))


def audit(draft, style, lang, genre):
    glob, own, adds, meta, _, warns = load(style)
    path = pathlib.Path(draft)
    if not path.is_file():
        raise UserError("draft not found: %s" % draft)
    text = load_measure().strip_front_matter(read_lenient(path))
    plain_raw = strip_code(text)
    if lang is None:
        letters = re.findall(r"[A-Za-zА-Яа-яЁё]", plain_raw)
        cyr = len(re.findall(r"[А-Яа-яЁё]", plain_raw))
        lang = "ru" if letters and cyr / len(letters) > 0.3 else "en"
    ctx = {"text": text, "raw_plain": plain_raw, "plain": norm(plain_raw), "lang": lang, "style": style,
           "targets": pick_targets(meta, lang, genre)}
    print("Аудит: %s · стиль %s · язык %s%s\n" % (path.name, style, lang, " · жанр " + genre if genre else ""))
    print("| Правило | Итог | Детали |\n|---|---|---|")
    failed = scripted = warned = 0
    manual = []
    for r in glob + own:
        if not r["on"]:
            continue
        if r["kind"] == "auto":
            if r["id"] not in CHECKS:
                raise UserError("rule %s is auto but has no check in rules.py (set its type to model)" % r["id"])
            ctx["rule"] = r["id"]
            status, detail = CHECKS[r["id"]](ctx)
            scripted += status != "–"
            failed += status == "✗"
            warned += status == "⚠"
            print("| %s %s | %s | %s |" % (r["id"], r["text"][:60].replace("|", "/"), status, detail.replace("|", "/")))
        else:
            manual.append(r)
    manual += [a for a in adds if a["on"]]
    if manual:
        print("\nПравила для оценки моделью (по каждому: ✓ или ✗ и причина; это оценка, не измерение):")
        for r in manual:
            print("  %s  %s" % (r["id"], r["text"]))
    off = [r["id"] for r in glob + own + adds if not r["on"]]
    if off:
        print("\nВыключено: " + ", ".join(off))
    facts = len(re.findall(r"\[(?:ФАКТ|FACT)\?", text))
    print("\nСправка: слов %d, пометок [ФАКТ?] %d." % (len(re.findall(r"\w+", plain_raw)), facts))
    print("Итог скрипта: проверено %d, нарушено %d, на проверку глазами %d." % (scripted, failed, warned))
    return 1 if failed else 0


def option(argv, name, allowed=None):
    if name not in argv:
        return None
    i = argv.index(name)
    if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
        raise UserError("%s needs a value" % name)
    v = argv[i + 1]
    if allowed and v not in allowed:
        raise UserError("%s must be one of: %s" % (name, ", ".join(allowed)))
    return v


def positional(argv):
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
        elif a in ("--lang", "--genre"):
            skip = True
        else:
            out.append(a)
    return out


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip())
        return 0
    try:
        pos = positional(argv)
        if len(pos) == 2 and pos[0] == "show":
            show(pos[1])
            return 0
        if pos == ["check"]:
            return check()
        if len(pos) == 3 and pos[0] == "audit":
            return audit(pos[1], pos[2], option(argv, "--lang", ("ru", "en")), option(argv, "--genre"))
        print(__doc__.strip(), file=sys.stderr)
        return 2
    except Exception as e:  # any failure of the tool itself is exit 2, never 1 (1 means a failed rule)
        print("error: %s" % (e if isinstance(e, UserError) else "%s: %s" % (type(e).__name__, e)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
