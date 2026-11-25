# Сторонние компоненты

Все скопированы без изменений в `vendor/<имя>/`, лицензия каждого лежит рядом (`LICENSE`). Версии (коммиты) записаны в [vendor/SOURCES.tsv](vendor/SOURCES.tsv). Обновление: `tools/sync-vendor.sh`.

| Папка в vendor | Исходный репозиторий | Лицензия | Что берём |
|---|---|---|---|
| `humanizer` | [blader/humanizer](https://github.com/blader/humanizer) | MIT | снятие ИИ-слога |
| `infostyle-skill` | [artgas1/infostyle-skill](https://github.com/artgas1/infostyle-skill) | MIT | редактура по «Пиши, сокращай» |
| `economist-style-guide-plugin` | [TAJD/economist-style-guide-plugin](https://github.com/TAJD/economist-style-guide-plugin) | MIT | стиль The Economist |
| `claude-skills-journalism` | [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism) | MIT | newsroom-style, fact-check-workflow, source-verification, story-pitch, editorial-workflow |
| `ru-text` | [talkstream/ru-text](https://github.com/talkstream/ru-text) | MIT | русская типографика, вычитка, оценка |

Не включено: файлы `agents/` (настройки под другие платформы), всё остальное из репозиториев-источников.
