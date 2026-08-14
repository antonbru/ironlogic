"""RobotAPI — объект ``r``, передаваемый в ``on_tick``.

Предоставляет сенсоры (только чтение) и действия робота.
"""

from __future__ import annotations

from typing import Any

from ironlogic.config import RADAR_MAX_RADIUS
from ironlogic.engine.cells import (
    UNKNOWN,
    abs_dir,
    cell_name,
    rel_dir,
    vector,
)

__all__ = ["RobotAPI"]

VALID_MOVE = {"forward", "backward"}
VALID_TURN = {"left", "right"}
VALID_REL = {"front", "right", "back", "left"}
VALID_KINDS = {"EMPTY", "STONE", "PIT", "REACTOR", "AMMO", "RECHARGE", "ROBOT", "FRIEND", "PROJECTILE"}


class RobotAPI:
    """Интерфейс робота для скрипта: сенсоры и действия.

    ``world`` — объект мира боя, предоставляющий:
      - ``arena`` (Arena)
      - ``robots`` (dict[int, RobotState])
      - ``robot_at(x, y)`` -> RobotState | None
      - ``projectile_at(x, y)`` -> bool
      - ``try_action(robot_id, kind, payload)`` -> bool  (первое действие в такте)
      - ``log_script(robot_id, message)``
    """

    def __init__(self, world: Any, robot_state: Any) -> None:
        self._world = world
        self._robot = robot_state

    # --- Утилиты ----------------------------------------------------------
    def _cell_in(self, rel: str) -> tuple[int, int]:
        dx, dy = vector(abs_dir(self._robot.dir, rel))
        return self._robot.x + dx, self._robot.y + dy

    def _rel_ok(self, rel: str) -> bool:
        return rel in VALID_REL

    # --- Сенсоры ----------------------------------------------------------
    def eye(self, rel: str) -> str:
        """Имя типа соседней клетки в направлении ``rel`` или ``UNKNOWN``."""
        if not self._rel_ok(rel):
            return UNKNOWN
        if self._robot.hardware.get(rel) != "eye":
            return UNKNOWN
        x, y = self._cell_in(rel)
        return cell_name(self._world.arena.get(x, y))

    def radar(self, kind: str, radius: int) -> tuple[int, str] | None:
        """Ближайший объект типа ``kind``: (расстояние, направление) или None.

        Порядок сканирования фиксированный: по возрастанию евклидова
        расстояния, затем строка, затем колонка (для детерминизма).
        """
        if not self._robot.radar or not self._robot.radar_active:
            self._world.log_script(self._robot.id, "radar: радар отсутствует или выключен")
            return None
        if kind not in VALID_KINDS:
            self._world.log_script(self._robot.id, f"radar: неизвестный тип '{kind}'")
            return None
        radius = max(1, min(radius, RADAR_MAX_RADIUS))
        rx, ry = self._robot.x, self._robot.y

        def kind_at(x: int, y: int) -> str:
            cell = self._world.arena.get(x, y)
            if cell == 6:  # ROBOT
                return "ROBOT"
            return cell_name(cell)

        found: list[tuple[int, int, int]] = []  # (dist, y, x)
        for y in range(max(0, ry - radius), min(self._world.arena.height - 1, ry + radius) + 1):
            for x in range(max(0, rx - radius), min(self._world.arena.width - 1, rx + radius) + 1):
                if (x, y) == (rx, ry):
                    continue
                dist_sq = (x - rx) ** 2 + (y - ry) ** 2
                if dist_sq > radius * radius:
                    continue
                if kind_at(x, y) != kind:
                    continue
                dist = int(dist_sq ** 0.5)
                if dist == 0:
                    dist = 1
                found.append((dist, y, x))

        if not found:
            return None
        found.sort()
        dist, y, x = found[0]
        # Направление на цель: преобладающая ось
        if abs(x - rx) >= abs(y - ry):
            abs_d = "E" if x > rx else "W"
        else:
            abs_d = "S" if y > ry else "N"
        return (dist, rel_dir(self._robot.dir, abs_d))

    def health(self) -> int:
        return self._robot.health

    def energy(self) -> int:
        return self._robot.energy

    def ammo(self) -> int:
        return self._robot.ammo

    def tick(self) -> int:
        return self._world.tick

    def facing(self) -> str:
        return self._robot.dir

    def pos(self) -> tuple[int, int]:
        return (self._robot.x, self._robot.y)

    def radar_active(self) -> bool:
        return self._robot.radar_active

    # --- Действия ---------------------------------------------------------
    def move(self, rel: str) -> bool:
        """Движение forward/backward (с учётом cooldown от пушек)."""
        if rel not in VALID_MOVE:
            self._world.log_script(self._robot.id, f"move: неверное направление '{rel}'")
            return False
        return self._world.try_action(self._robot.id, "move", {"rel": rel})

    def turn(self, rel: str) -> bool:
        """Поворот left/right на 90°."""
        if rel not in VALID_TURN:
            self._world.log_script(self._robot.id, f"turn: неверное направление '{rel}'")
            return False
        return self._world.try_action(self._robot.id, "turn", {"rel": rel})

    def shoot(self, rel: str) -> bool:
        """Выстрел из пушки в направлении rel."""
        if not self._rel_ok(rel):
            self._world.log_script(self._robot.id, f"shoot: неверное направление '{rel}'")
            return False
        return self._world.try_action(self._robot.id, "shoot", {"rel": rel})

    def wait(self) -> bool:
        """Пропустить такт."""
        return self._world.try_action(self._robot.id, "wait", {})

    def radar_on(self) -> bool:
        """Включить радар."""
        return self._world.try_action(self._robot.id, "radar_on", {})

    def radar_off(self) -> bool:
        """Выключить радар."""
        return self._world.try_action(self._robot.id, "radar_off", {})