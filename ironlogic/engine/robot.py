"""Состояние робота в бою."""

from __future__ import annotations

from dataclasses import dataclass, field

from ironlogic.config import (
    ROBOT_START_AMMO,
    ROBOT_START_ENERGY,
    ROBOT_START_HEALTH,
    CANNON_COOLDOWN,
)
from ironlogic.engine.cells import EAST

__all__ = ["RobotState"]

VALID_HARDWARE = {"eye", "cannon", "empty"}
VALID_REL_DIRS = ("front", "right", "back", "left")


@dataclass
class RobotState:
    """Динамическое состояние робота в бою."""

    id: int
    name: str
    file: str
    x: int
    y: int
    dir: str = EAST
    team: str | None = None
    hardware: dict[str, str] = field(
        default_factory=lambda: {"front": "eye", "right": "empty", "back": "empty", "left": "cannon"}
    )
    radar: bool = False
    health: int = ROBOT_START_HEALTH
    energy: int = ROBOT_START_ENERGY
    ammo: int = ROBOT_START_AMMO
    alive: bool = True
    shutdown: bool = False
    move_cooldown: int = 1
    last_move_tick: int = -1
    radar_active: bool = False

    # --- Характеристики ----------------------------------------------------
    @property
    def cannon_count(self) -> int:
        return sum(1 for slot in self.hardware.values() if slot == "cannon")

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    @pos.setter
    def pos(self, value: tuple[int, int]) -> None:
        self.x, self.y = value

    def can_move(self, tick: int) -> bool:
        """Может ли робот двигаться в этом такте (cooldown от пушек)."""
        cooldown = CANNON_COOLDOWN[self.cannon_count]
        if cooldown is None:
            return False
        return tick - self.last_move_tick >= cooldown

    def on_moved(self, tick: int) -> None:
        self.last_move_tick = tick

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "file": self.file,
            "team": self.team,
            "x": self.x,
            "y": self.y,
            "dir": self.dir,
            "hardware": dict(self.hardware),
            "radar": self.radar,
            "health": self.health,
            "energy": self.energy,
            "ammo": self.ammo,
            "alive": self.alive,
            "shutdown": self.shutdown,
        }


def validate_hardware(hardware: dict[str, str]) -> None:
    """Валидация словаря железа. Бросает ValueError с понятным сообщением."""
    if set(hardware) != set(VALID_REL_DIRS):
        raise ValueError(
            f"hardware должен содержать ключи {list(VALID_REL_DIRS)}, получено: {sorted(hardware)}"
        )
    for slot, value in hardware.items():
        if value not in VALID_HARDWARE:
            raise ValueError(
                f"Слот '{slot}' имеет недопустимое значение '{value}'. "
                f"Допустимо: {sorted(VALID_HARDWARE)}"
            )