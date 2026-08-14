# IronLogic — AGENTS.md

Десктопная игра «битва программируемых роботов» на Python: боты пишутся на настоящем Python и сражаются сами на клеточной арене (аналог «Робот-Войны», для детей 10–14 лет). Python 3.11+, GUI на PySide6. Отвечать на русском; комментарии и docstrings в коде — на английском.

## Проект

- Движок симуляции — чистый Python, только stdlib (детерминированный, без random и wall-clock).
- GUI — PySide6 (Qt 6.6+), тёмная неоновая тема через QSS.
- Боты исполняются в песочнице (ограниченные builtins, бюджет инструкций через `sys.settrace`, лимит рекурсии).
- Точка входа: `ironlogic/__main__.py` → без аргументов GUI, с аргументами CLI (`ironlogic/cli.py`).
- Публичный API бота — `ironlogic_api.py` (`from ironlogic_api import Robot`).
- Полное ТЗ и правила работы: `ironlogic-task-spec.md` и `.clinerules/ironlogic-project.md`.

## Команды

Всё из корня репозитория, через venv:

- Тесты: `.venv/bin/pytest`
- Компиляция пакета: `.venv/bin/python -m compileall ironlogic`
- Запуск GUI: `.venv/bin/python -m ironlogic`
- Headless бой: `.venv/bin/python -m ironlogic battle --map arena --seed 42 --robots examples/kickme.py examples/wanderer.py --out /tmp/battle.json`
- Реплей: `.venv/bin/python -m ironlogic replay /tmp/battle.json`
- Списки: `.venv/bin/python -m ironlogic list-maps` / `list-bots --dir examples`
- Проверка бота: `.venv/bin/python -m ironlogic check examples/kickme.py`

## Архитектура

- `ironlogic/engine/` — симуляция: `battle.py` (цикл тактов), `arena.py`, `cells.py`, `projectile.py`, `events.py` (события → `battle.json`), `mapgen.py` (генератор карт с seed).
- `ironlogic/botapi/` — песочница (`sandbox.py`), загрузка ботов (`loader.py`), API робота (`robot.py`), ошибки (`errors.py`).
- `ironlogic/app/` — PySide6 GUI: `main.py` (окно), `launcher.py`, `battle_screen.py`, `arena_widget.py`, `code_editor.py`.
- `ironlogic/cli.py` — подкоманды battle / replay / list-maps / list-bots / check.
- `ironlogic/config.py` — ВСЕ константы баланса (урон, энергия, бюджеты, лимиты); магических чисел в коде нет.
- `examples/` — боты-примеры; боты пользователя — в `bots/`; документация — `docs/bots.md`, `docs/rules.md`.

## Конвенции

- Детерминизм обязателен: запрещены `random` и wall-clock в движке; порядок обработки фиксирован (роботы по id, снаряды по порядку создания, радар по расстоянию→строка→колонка); одинаковые входные данные → побайтово одинаковый `battle.json`.
- PEP 8, type hints на всех публичных функциях, docstrings на модулях `engine/` и `botapi/`.
- Константы баланса — только в `ironlogic/config.py`.
- Работа строго по фазам 0→6 из ТЗ; после каждой фазы — `pytest` + `compileall`; коммиты с conventional-сообщениями (`feat:`, `fix:`, `test:`, `docs:`).
- Не менять тестовые ассерты под код — код должен проходить существующие тесты.
- Не добавлять фичи вне ТЗ (см. Non-goals); при неясном требовании — уточнить, а не домысливать.

## Notes

<!-- Сюда можно добавлять краткие заметки для будущих сессий. -->
