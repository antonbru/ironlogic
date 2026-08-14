"""Типы клеток арены и вспомогательные константы направлений."""

from __future__ import annotations

# --- Коды клеток ----------------------------------------------------------
EMPTY = 0
STONE = 1
PIT = 2
REACTOR = 3
AMMO = 4
RECHARGE = 5
ROBOT = 6
FRIEND = 7
PROJECTILE = 8
UNKNOWN = 255

# Имена клеток (контракт для ботов — строки)
EMPTY_NAME = "EMPTY"
STONE_NAME = "STONE"
PIT_NAME = "PIT"
REACTOR_NAME = "REACTOR"
AMMO_NAME = "AMMO"
RECHARGE_NAME = "RECHARGE"
ROBOT_NAME = "ROBOT"
FRIEND_NAME = "FRIEND"
PROJECTILE_NAME = "PROJECTILE"
UNKNOWN_NAME = "UNKNOWN"

# Обратные таблицы имя <-> код
CODE_TO_NAME: dict[int, str] = {
    EMPTY: EMPTY_NAME,
    STONE: STONE_NAME,
    PIT: PIT_NAME,
    REACTOR: REACTOR_NAME,
    AMMO: AMMO_NAME,
    RECHARGE: RECHARGE_NAME,
    ROBOT: ROBOT_NAME,
    FRIEND: FRIEND_NAME,
    PROJECTILE: PROJECTILE_NAME,
    UNKNOWN: UNKNOWN_NAME,
}

NAME_TO_CODE: dict[str, int] = {v: k for k, v in CODE_TO_NAME.items()}


def cell_name(code: int) -> str:
    """Возвращает имя клетки по коду (для UNKNOWN-кодов — 'UNKNOWN')."""
    return CODE_TO_NAME.get(code, UNKNOWN_NAME)


def cell_code(name: str) -> int:
    """Возвращает код клетки по имени (для неизвестных имён — UNKNOWN)."""
    return NAME_TO_CODE.get(name, UNKNOWN)


# --- Направления ----------------------------------------------------------
NORTH = "N"
EAST = "E"
SOUTH = "S"
WEST = "W"

DIR_VECTORS: dict[str, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

ORDER: list[str] = [NORTH, EAST, SOUTH, WEST]

# Относительные направления относительно ориентации робота
RELATIVE = ("front", "right", "back", "left")


def turn_right(facing: str) -> str:
    """Поворот направо на 90°."""
    return ORDER[(ORDER.index(facing) + 1) % 4]


def turn_left(facing: str) -> str:
    """Поворот налево на 90°."""
    return ORDER[(ORDER.index(facing) - 1) % 4]


def abs_dir(facing: str, rel: str) -> str:
    """Абсолютное направление по относительному (front/right/back/left)."""
    idx = ORDER.index(facing)
    delta = {"front": 0, "right": 1, "back": 2, "left": 3}[rel]
    return ORDER[(idx + delta) % 4]


def rel_dir(facing: str, abs_d: str) -> str:
    """Относительное направление по абсолютному."""
    delta = (ORDER.index(abs_d) - ORDER.index(facing)) % 4
    return ("front", "right", "back", "left")[delta]


def vector(facing: str) -> tuple[int, int]:
    """Вектор направления (dx, dy)."""
    return DIR_VECTORS[facing]


__all__ = [
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
    "EMPTY_NAME",
    "STONE_NAME",
    "PIT_NAME",
    "REACTOR_NAME",
    "AMMO_NAME",
    "RECHARGE_NAME",
    "ROBOT_NAME",
    "FRIEND_NAME",
    "PROJECTILE_NAME",
    "UNKNOWN_NAME",
    "CODE_TO_NAME",
    "NAME_TO_CODE",
    "cell_name",
    "cell_code",
    "NORTH",
    "EAST",
    "SOUTH",
    "WEST",
    "DIR_VECTORS",
    "ORDER",
    "RELATIVE",
    "turn_right",
    "turn_left",
    "abs_dir",
    "rel_dir",
    "vector",
]