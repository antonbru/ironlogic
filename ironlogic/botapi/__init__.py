"""API ботов IronLogic: конфигурация Robot и константы клеток."""

from __future__ import annotations

from ironlogic.botapi.robot import RobotAPI  # noqa: F401
from ironlogic.botapi.loader import LoadedBot, load_bot  # noqa: F401
from ironlogic.botapi.errors import (  # noqa: F401
    BotCompileError,
    BotRuntimeError,
    BudgetError,
)


class Robot:
    """Конфигурация робота (железо).

    Параметры:
        name: имя робота (показывается в бою).
        front/right/back/left: слоты аппаратуры ('eye', 'cannon' или 'empty').
        radar: наличие радара (bool).
    """

    def __init__(
        self,
        *,
        name: str = "Robo",
        front: str = "eye",
        right: str = "empty",
        back: str = "empty",
        left: str = "cannon",
        radar: bool = False,
    ) -> None:
        self.name = name
        self.hardware = {"front": front, "right": right, "back": back, "left": left}
        self.radar = radar


# Константы типов клеток (строки-имена — контракт для детей)
EMPTY = "EMPTY"
STONE = "STONE"
PIT = "PIT"
REACTOR = "REACTOR"
AMMO = "AMMO"
RECHARGE = "RECHARGE"
ROBOT = "ROBOT"
FRIEND = "FRIEND"
PROJECTILE = "PROJECTILE"
UNKNOWN = "UNKNOWN"

__all__ = [
    "Robot",
    "RobotAPI",
    "LoadedBot",
    "load_bot",
    "BotCompileError",
    "BotRuntimeError",
    "BudgetError",
    "EMPTY",
    "STONE",
    "PIT",
    "REACTOR",
    "AMMO",
    "RECHARGE",
    "ROBOT",
    "FRIEND",
    "PROJECTILE",
    "UNKNOWN",
]