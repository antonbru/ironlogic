"""Разрешение путей в dev-режиме и в собранном .app (PyInstaller).

В бандле read-only ресурсы (examples/, template_bot.py) лежат в
``sys._MEIPASS``, а пользовательские данные (bots/, звуки) — в
``~/.ironlogic``, иначе запись в каталог приложения запрещена.
"""

from __future__ import annotations

import sys
from pathlib import Path

_FROZEN = bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Каталог read-only ресурсов: examples/, template_bot.py."""
    if _FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(".")))
    return Path(__file__).resolve().parent.parent


def user_dir() -> Path:
    """Каталог пользовательских данных: bots/, звуки. Создаётся при первом вызове."""
    if _FROZEN:
        base = Path.home() / ".ironlogic"
    else:
        base = Path(__file__).resolve().parent.parent
    base.mkdir(parents=True, exist_ok=True)
    return base


def bots_dir() -> Path:
    """Каталог личных ботов пользователя."""
    path = user_dir() / "bots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def examples_dir() -> Path:
    """Каталог примеров ботов (read-only в бандле)."""
    return resource_dir() / "examples"


def template_bot_path() -> Path:
    """Путь к шаблону бота.

    В dev лежит внутри пакета (``ironlogic/template_bot.py``),
    в бандле — в корне ``_MEIPASS`` (см. datas в ironlogic.spec).
    """
    if _FROZEN:
        return resource_dir() / "template_bot.py"
    return Path(__file__).resolve().parent / "template_bot.py"
