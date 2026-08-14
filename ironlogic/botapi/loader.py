"""Безопасная загрузка .py файлов роботов.

Компиляция + поиск обязательных ``robot`` и ``on_tick`` + исполнение кода
только в песочнице (ограниченные builtins).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ironlogic.botapi.errors import BotCompileError
from ironlogic.botapi.sandbox import build_globals

__all__ = ["LoadedBot", "load_bot"]


@dataclass
class LoadedBot:
    """Загруженный бот: конфигурация (Robot) и функция on_tick."""

    source: str
    path: str
    robot: Any  # ironlogic.botapi.Robot
    on_tick: Callable[..., Any]


def load_bot(path: str | Path) -> LoadedBot:
    """Загружает бота из .py файла.

    Бросает ``BotCompileError`` при ошибке компиляции, отсутствии
    ``robot``/``on_tick`` или неверной конфигурации железа.
    """
    p = Path(path)
    try:
        source = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise BotCompileError(f"не удалось прочитать файл: {exc}", path=str(p)) from exc

    try:
        code = compile(source, str(p), "exec")
    except SyntaxError as exc:
        raise BotCompileError(
            f"ошибка синтаксиса: {exc.msg}", path=str(p), line=exc.lineno
        ) from exc

    globs = build_globals({"__file__": str(p), "__name__": f"bot_{p.stem}"})
    try:
        exec(code, globs)  # noqa: S102 — внутри песочницы с ограниченными builtins
    except BotCompileError:
        raise
    except Exception as exc:  # noqa: BLE001
        import traceback

        tb = traceback.format_exc(limit=2)
        raise BotCompileError(f"ошибка при исполнении кода модуля: {exc}\n{tb}", path=str(p)) from exc

    if "robot" not in globs:
        raise BotCompileError(
            "в файле не найден обязательный объект `robot = Robot(...)`", path=str(p)
        )
    if "on_tick" not in globs or not callable(globs.get("on_tick")):
        raise BotCompileError(
            "в файле не найдена обязательная функция `def on_tick(r)`", path=str(p)
        )

    robot_obj = globs["robot"]
    try:
        from ironlogic.engine.robot import validate_hardware

        validate_hardware(robot_obj.hardware)
    except ValueError as exc:
        raise BotCompileError(str(exc), path=str(p)) from exc

    return LoadedBot(source=source, path=str(p), robot=robot_obj, on_tick=globs["on_tick"])