---
style: forbes
targets: words_per_sentence=16.4 words_per_paragraph=53 tolerance=30
targets_profile: words_per_sentence=14.3 words_per_paragraph=74 tolerance=30
targets_essay: words_per_sentence=16.2 words_per_paragraph=87 tolerance=30
targets_interview: words_per_sentence=10.4 words_per_paragraph=38.6 tolerance=30
---
# Правила стиля forbes

Цели по длине: `targets` для колонки (жанр по умолчанию), для других жанров ключи `targets_profile`, `targets_essay`, `targets_interview` (скрипту передают `--genre`). Допуск в процентах. Формат строк как в `rules/global.md`.

- [x] F1 · model · Заголовок: образный ярлык или цитата героя, двоеточие, конкретное обещание
- [x] F2 · model · Подводка: автор или герой, должность, тезис или парадокс
- [x] F3 · model · Жанр и объём: колонка около 1400 слов, профиль 1600, интервью 2000, очерк 900; жанр не назван — колонка
- [x] F4 · model · Каждое число, имя и цитата с источником и датой; прямая речь героя с короткой вводкой
- [x] F5 · model · Концовка возвращает к тезису или заголовочной цитате
- [x] F6 · model · Тезис статьи формулируется одним предложением до начала черновика
- [x] F7 · model · Без рекламы продукта автора без пометки
- [x] F8 · auto · Без призывов «покупайте», «продавайте», «вкладывайтесь»
