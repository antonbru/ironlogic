"""Песочница исполнения кода ботов.

Ограниченные ``__builtins__``, бюджет инструкций через ``sys.settrace``,
лимит глубины рекурсии.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from typing import Any

from ironlogic.config import INSTRUCTION_BUDGET, MAX_RECURSION_DEPTH
from ironlogic.botapi.errors import BudgetError, BotRuntimeError

__all__ = ["SAFE_BUILTINS", "build_globals", "run_in_sandbox"]

# Белый список встроенных имён, доступных ботам (детям).
SAFE_BUILTINS: dict[str, Any] = {
    "True": True,
    "False": False,
    "None": None,
    "abs": abs,
    "min": min,
    "max": max,
    "int": int,
    "bool": bool,
    "len": len,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "str": str,
    "range": range,
    "round": round,
    "sum": sum,
    "sorted": sorted,
    "enumerate": enumerate,
    "zip": zip,
    "isinstance": isinstance,
    "print": print,  # результат пишется в лог скрипта (по контракту)
    "__build_class__": __builtins__["__build_class__"],  # для class в коде бота
}


def _safe_import(
    name: str,
    globals_: Any = None,  # noqa: ARG001
    locals_: Any = None,  # noqa: ARG001
    fromlist: Any = (),  # noqa: ARG001
    level: int = 0,
) -> Any:
    """Импорт, разрешающий только стабильный модуль ``ironlogic_api``.

    Любой другой импорт (``import os``, ``import random`` и т.п.) бросает
    ``ImportError`` — код бота не должен выходить за пределы песочницы.
    """
    if level != 0:
        raise ImportError("относительные импорты запрещены")
    if name != "ironlogic_api":
        raise ImportError(f"import запрещён: {name!r}")

    import importlib

    return importlib.import_module("ironlogic_api")


SAFE_BUILTINS["__import__"] = _safe_import


def build_globals(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Строит словарь globals для exec кода бота."""
    globs: dict[str, Any] = {"__builtins__": dict(SAFE_BUILTINS)}
    if extra:
        globs.update(extra)
    return globs


class _InstructionBudget:
    """Счётчик «инструкций» такта через sys.settrace."""

    def __init__(self, budget: int = INSTRUCTION_BUDGET, max_depth: int = MAX_RECURSION_DEPTH) -> None:
        self.budget = budget
        self.max_depth = max_depth
        self.count = 0
        self.depth = 0

    def tracer(self, frame: Any, event: str, arg: Any) -> Callable[..., Any] | None:
        if event == "call":
            self.depth += 1
        elif event == "return":
            self.depth -= 1
        self.count += 1
        if self.count > self.budget:
            raise BudgetError(f"бюджет инструкций превышен: >{self.budget} за такт")
        if self.depth > self.max_depth:
            raise BudgetError(f"глубина рекурсии >{self.max_depth}")
        return self.tracer


def run_in_sandbox(func: Callable[..., Any], *args: Any, globals_: dict[str, Any] | None = None) -> Any:
    """Исполняет ``func(*args)`` в песочнице с бюджетом инструкций и лимитом рекурсии.

    Возвращает результат функции. При превышении бюджета/рекурсии бросает
    ``BudgetError``; при любой другой ошибке исполнения — ``BotRuntimeError``
    с текстом исключения.
    """
    budget = _InstructionBudget()
    prev_trace = sys.gettrace()
    try:
        sys.settrace(budget.tracer)
        try:
            return func(*args)
        finally:
            sys.settrace(prev_trace)
    except BudgetError:
        raise
    except BotRuntimeError:
        raise
    except RecursionError:
        raise BudgetError(f"глубина рекурсии >{budget.max_depth}")
    except Exception as exc:  # noqa: BLE001
        tb = traceback.format_exc(limit=3)
        raise BotRuntimeError(f"{type(exc).__name__}: {exc}\n{tb}") from exc