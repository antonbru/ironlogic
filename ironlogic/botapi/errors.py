"""Ошибки загрузки и исполнения ботов."""

from __future__ import annotations

__all__ = ["BotCompileError", "BotRuntimeError", "BudgetError"]


class BotCompileError(Exception):
    """Ошибка компиляции/конфигурации бота (файл не допущен к бою)."""

    def __init__(self, message: str, *, path: str = "", line: int | None = None) -> None:
        self.path = path
        self.line = line
        full = message
        if path:
            prefix = path
            if line is not None:
                prefix += f":{line}"
            full = f"{prefix}: {message}"
        super().__init__(full)


class BotRuntimeError(Exception):
    """Ошибка времени исполнения бота (такт завершается wait())."""


class BudgetError(BotRuntimeError):
    """Превышен бюджет инструкций за такт."""