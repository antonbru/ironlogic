"""Летящие снаряды."""

from __future__ import annotations

from dataclasses import dataclass

from ironlogic.config import PROJECTILE_DAMAGE

__all__ = ["Projectile"]


@dataclass
class Projectile:
    """Снаряд: летит 1 клетку за такт в своём направлении."""

    id: int
    owner: int
    x: int
    y: int
    dir: str
    damage: int = PROJECTILE_DAMAGE

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    def to_dict(self) -> dict:
        return {"id": self.id, "owner": self.owner, "x": self.x, "y": self.y, "dir": self.dir}