# article-style

Скил для Claude Code: пишет статьи в стиле выбранного издания («как Forbes», «как fortraders») и учится на образцах, которые вы кладёте в папки.

Внутри: процедура ([SKILL.md](SKILL.md)), папки стилей ([references/](references/README.md)) и пять готовых MIT-скилов в `vendor/`: humanizer, infostyle, economist-style, journalism-core (проверка фактов, питч, AP-стиль), ru-text. Список с коммитами: [vendor/SOURCES.tsv](vendor/SOURCES.tsv), условия: [THIRD_PARTY.md](THIRD_PARTY.md).

## Установка
```bash
git clone https://github.com/webtask-eu/article-style ~/.claude/skills/article-style
```
Новая сессия Claude Code подхватит скил. Проверка структуры:
```bash
~/.claude/skills/article-style/tools/check.sh
```

## Как пользоваться
1. Положите статьи-образцы: `tools/add-reference.sh forbes статья.md --source URL --title "Заголовок"` (или `pbpaste | tools/add-reference.sh forbes - --title ...`).
2. Скажите: «обнови стиль forbes». Скил замерит образцы и запишет `references/forbes/learned.md`.
3. Просите: «напиши статью про … как форбс». Скил читает `style.md`, `learned.md`, образцы, пишет черновик и прогоняет редактуру.

Новый стиль: та же команда `add-reference.sh` с новым именем создаёт папку. Алиасы запроса правятся в `references/<стиль>/style.md`.

## Правила
У каждого правила есть номер (G1, F3, T5). Показать: «покажи правила forbes». После статьи скил выдаёт блок «Правила статьи»: что проверил скрипт и что оценила модель.
Изменить: «выключи правило F5», «добавь правило …» (личные поправки идут в `rules.local.md`, он не попадает в git). Общие правила лежат в `rules/global.md` и `references/<стиль>/rules.md`.

## Команды
| Команда | Что делает |
|---|---|
| `tools/list-styles.sh` | стили, число образцов, есть ли `learned.md` |
| `tools/add-reference.sh` | сохраняет образец, создаёт стиль |
| `tools/measure.py` | замеры текста: длина предложений и абзацев, числа, цитаты |
| `tools/rules.py` | `show <стиль>`: список правил, `check`: проверка файлов правил, `audit <черновик> <стиль>`: проверка черновика |
| `tools/check.sh` | проверка структуры репозитория |
| `tools/sync-vendor.sh` | обновляет `vendor/` из исходных репозиториев |

## Авторские права на образцы
Образцы защищены правом их издателей, поэтому `samples/` исключены из git. В репозитории лежат только ваши заметки о стиле (`style.md`, `learned.md`), своими словами.

## Лицензия
MIT для собственного кода и текстов репозитория. Вендорные скилы: каждый со своей MIT-лицензией в `vendor/<имя>/LICENSE`.
