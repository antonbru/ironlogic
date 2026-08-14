"""API ботов IronLogic (реализация — Фаза 2)."""

from __future__ import annotations


class Robot:
    """Конфигурация робота (железо).

    Полная реализация появляется в Фазе 2. Здесь — каркас, чтобы
    ``ironlogic_api`` импортировался и пакет собирался уже в Фазе 0.
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