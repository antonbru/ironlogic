# IronLogic — «Железная Логика»

> **Побеждает не железо — побеждает логика.**

Красивая десктопная игра для macOS: пиши программу боевого робота на **Python** и смотри, как роботы сражаются на клеточной арене сами, без участия человека в бою. Побеждает лучший код.

Игра — аналог классической российской игры *Robot Warfare. Битва интеллектов* (Александр Шабаршин, 1999), переосмысленный для юных программистов 10–14 лет.

## Что это?

- 🧠 **Язык ботов — настоящий Python 3.** Если ребёнок умеет писать `if` и `while` — он уже умеет писать бота.
- 🤖 **Движок симуляции** — детерминированный, честный бой такт за тактом: движение, стрельба, энергия, патроны, ямы и взрывающиеся реакторы.
- 🎨 **Красивый GUI на PySide6 (Qt)** — тёмная неоновая тема, анимированная арена, HUD и реплеи.
- ⚔️ **Режим «горячего» боя**: свои роботы против ботов из `examples/`.

## Установка

Требуется Python 3.11+ (например, через Homebrew: `brew install python@3.11`). Xcode не нужен.

```bash
# 1. Клонировать репозиторий и перейти в него
git clone <url> ironlogic && cd ironlogic

# 2. Создать виртуальное окружение
python3.11 -m venv .venv

# 3. Установить зависимости
.venv/bin/pip install -r requirements.txt

# 4. Запустить игру
.venv/bin/python -m ironlogic
```

## Как написать первого робота

Скопируйте пример и отредактируйте:

```python
# bots/my_first_bot.py
from ironlogic_api import Robot

robot = Robot(
    name="Вандер",
    front="eye",      # глаз спереди — видит соседнюю клетку
    right="empty",    # пусто
    back="eye",       # глаз сзади
    left="cannon",    # пушка слева
    radar=False,      # без радара
)

def on_tick(r):
    if r.eye("front") == "ROBOT":
        r.shoot("front")   # стреляем во врага перед собой
        return
    if r.eye("front") == "EMPTY":
        r.move("forward")
        return
    r.turn("left")
```

Полный справочник API — в [docs/bots.md](docs/bots.md) (появится в одной из фаз).

## CLI (без графики)

```bash
# Бой двух роботов headless
.venv/bin/python -m ironlogic battle --map arena --seed 42 --robots examples/kickme.py examples/wanderer.py --out /tmp/battle.json

# Сводка по сохранённому бою
.venv/bin/python -m ironlogic replay /tmp/battle.json

# Списки
.venv/bin/python -m ironlogic list-maps
.venv/bin/python -m ironlogic list-bots --dir examples

# Проверка компиляции бота
.venv/bin/python -m ironlogic check examples/kickme.py
```

## Тесты

```bash
.venv/bin/pytest
```

## Структура проекта

```
ironlogic/
├── ironlogic/           # пакет игры: движок, API ботов, GUI, CLI
├── ironlogic_api.py     # публичный API для ботов (from ironlogic_api import Robot)
├── examples/            # готовые боты-примеры
├── bots/                # личные боты
├── tests/               # pytest
└── docs/                # документация: правила игры и справочник ботов
```

## Дорожная карта

Проект строится строго по фазам, описанным в [ironlogic-task-spec.md](ironlogic-task-spec.md):

1. **Фаза 0 — Каркас** (текущая): структура пакета, CLI-каркас, тесты.
2. **Фаза 1 — Движок**: симуляция боя, детерминизм.
3. **Фаза 2 — API ботов**: песочница Python, сенсоры и действия.
4. **Фаза 3 — Генератор карт**: пресеты, seed, инварианты.
5. **Фаза 4 — CLI**: `battle`, `replay`, `list-maps`, `list-bots`, `check`.
6. **Фаза 5 — GUI**: лаунчер, арена, HUD, реплеи.
7. **Фаза 6 — Полировка**: редактор кода, сборка `.app`.