"""Публичный API для ботов IronLogic.

Боты импортируют только из этого модуля::

    from ironlogic_api import Robot

Реализация классов живёт в ``ironlogic.botapi``; этот модуль — тонкая
стабильная обёртка (контракт для игроков).
"""

from ironlogic.botapi import (  # noqa: F401
    Robot,
    EMPTY,
    STONE,
    PIT,
    REACTOR,
    AMMO,
    RECHARGE,
    ROBOT,
    FRIEND,
    PROJECTILE,
    UNKNOWN,
)

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