"""Движок симуляции боя.

Главный цикл тактов: роботы по id -> снаряды -> эффекты -> условия конца.
Полностью детерминированно: никакого random, никакого wall-clock времени.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ironlogic.config import (
    AMMO_PICKUP_AMOUNT,
    DEFAULT_MAX_TICKS,
    ENERGY_BASE_COST,
    ENERGY_MOVE_COST,
    ENERGY_RADAR_COST,
    ENERGY_SHOOT_COST,
    REACTOR_BLAST_RADIUS,
    REACTOR_DAMAGE,
    RECHARGE_AMOUNT,
    ROBOT_MAX_AMMO,
)
from ironlogic.engine.cells import (
    AMMO,
    EMPTY,
    PIT,
    REACTOR,
    RECHARGE,
    ROBOT,
    STONE,
    abs_dir,
    cell_name,
    turn_left,
    turn_right,
    vector,
)
from ironlogic.engine.arena import Arena
from ironlogic.engine.events import Event
from ironlogic.engine.projectile import Projectile
from ironlogic.engine.robot import RobotState

__all__ = ["BattleConfig", "BattleRunner", "BattleResult"]


@dataclass
class BattleConfig:
    """Конфигурация боя."""

    map_preset: str = "arena"
    seed: int = 42
    width: int | None = None
    height: int | None = None
    max_ticks: int = DEFAULT_MAX_TICKS
    bots: list[str] = field(default_factory=list)


@dataclass
class BattleResult:
    """Результат боя: карта, роботы, события, победитель."""

    map: Arena
    start_robots: list[dict]
    max_ticks: int
    events: list[dict[str, Any]]
    winner: int | None
    end_reason: str
    ticks: int


class _BattleWorld:
    """Промежуточный объект мира боя, передаваемый в RobotAPI."""

    def __init__(self, runner: "BattleRunner") -> None:
        self.battle = runner
        self.tick = 0

    @property
    def arena(self) -> Arena:
        return self.battle.arena

    @property
    def robots(self) -> dict[int, RobotState]:
        return self.battle.robots

    def robot_at(self, x: int, y: int) -> RobotState | None:
        for r in self.battle.robots.values():
            if r.alive and (r.x, r.y) == (x, y):
                return r
        return None

    def projectile_at(self, x: int, y: int) -> bool:
        return any(p.x == x and p.y == y for p in self.battle.projectiles)

    def log_script(self, robot_id: int, message: str) -> None:
        self.battle.script_log(robot_id, message, "debug")

    def try_action(self, robot_id: int, kind: str, payload: dict[str, Any]) -> bool:
        return self.battle.try_action(robot_id, kind, payload)


class BattleRunner:
    """Запускает и проводит бой до конца. Результат — BattleResult."""

    def __init__(
        self,
        config: BattleConfig,
        *,
        arena: Arena | None = None,
        loaded_bots: list[Any] | None = None,
    ) -> None:
        self.config = config
        self.arena = arena if arena is not None else self._make_arena()
        self.loaded_bots: list[Any] = loaded_bots if loaded_bots is not None else []
        self.robots: dict[int, RobotState] = {}
        self.projectiles: list[Projectile] = []
        self.events: list[dict[str, Any]] = []
        self.tick = 0
        self.winner: int | None = None
        self.end_reason: str | None = None
        self._action_done: set[int] = set()
        self._world = _BattleWorld(self)
        self._projectile_counter = 0

    # --- Инициализация -----------------------------------------------------
    def _make_arena(self) -> Arena:
        from ironlogic.engine.mapgen import generate

        return generate(self.config.map_preset, self.config.seed, self.config.width, self.config.height)

    def _spawn_robots(self) -> None:
        from ironlogic.engine.mapgen import spawn_positions

        positions = spawn_positions(self.arena, len(self.loaded_bots), self.config.seed)
        for i, loaded in enumerate(self.loaded_bots):
            x, y, d = positions[i]
            robot = RobotState(
                id=i,
                name=getattr(loaded.robot, "name", f"Robot{i}"),
                file=loaded.path,
                x=x,
                y=y,
                dir=d,
                hardware=dict(loaded.robot.hardware),
                radar=bool(getattr(loaded.robot, "radar", False)),
            )
            self.arena.set(x, y, ROBOT)
            self.robots[i] = robot
            self.events.append(
                Event("spawn", t=-1, robot=i, x=x, y=y, dir=d, name=robot.name)
            )

    # --- Публичный API -----------------------------------------------------
    def run(self) -> BattleResult:
        if not self.robots:
            self._spawn_robots()
        for tick in range(self.config.max_ticks):
            self._step()
            end = self._check_end(tick)
            if end:
                break
        else:
            self._finish_time_limit(self.config.max_ticks - 1)

        self.events.append(
            Event(
                "end",
                t=self.tick,
                winner=self.winner,
                reason=self.end_reason,
                ticks=self.tick,
            )
        )
        return BattleResult(
            map=self.arena,
            start_robots=[r.to_dict() for r in self.robots.values()],
            max_ticks=self.config.max_ticks,
            events=self.events,
            winner=self.winner,
            end_reason=self.end_reason or "draw",
            ticks=self.tick,
        )

    # --- Основной цикл -----------------------------------------------------
    def _step(self) -> None:
        self._action_done = set()
        self._world.tick = self.tick

        for robot in sorted(self.robots.values(), key=lambda r: r.id):
            if not robot.alive or robot.shutdown:
                continue
            loaded = self.loaded_bots[robot.id] if robot.id < len(self.loaded_bots) else None
            if loaded is None:
                continue
            self._run_bot_tick(loaded, robot)

        self._move_projectiles()
        self._apply_effects()
        self.tick += 1

    def _run_bot_tick(self, loaded: Any, robot: RobotState) -> None:
        from ironlogic.botapi.errors import BudgetError
        from ironlogic.botapi.robot import RobotAPI
        from ironlogic.botapi.sandbox import run_in_sandbox

        api = RobotAPI(self._world, robot)
        try:
            run_in_sandbox(loaded.on_tick, api, bot_file=loaded.path)
        except BudgetError as exc:
            self.events.append(
                Event("budget_exceeded", t=self.tick, robot=robot.id, message=str(exc))
            )
            self.script_log(robot.id, f"budget_exceeded: {exc}", "error")
            return
        except Exception as exc:  # noqa: BLE001
            self.script_log(robot.id, f"ошибка скрипта: {exc}", "error")
            return
        if robot.id not in self._action_done:
            self.try_action(robot.id, "wait", {})

    # --- Действия ----------------------------------------------------------
    def try_action(self, robot_id: int, kind: str, payload: dict[str, Any]) -> bool:
        """Обрабатывает действие робота. Возвращает True, если действие выполнено."""
        robot = self.robots.get(robot_id)
        if robot is None or not robot.alive:
            return False
        if robot.shutdown:
            self.script_log(robot_id, f"действие {kind} проигнорировано: робот в shutdown", "warn")
            return False
        if robot_id in self._action_done:
            self.script_log(robot_id, f"действие {kind} проигнорировано: такт уже занят", "warn")
            return False
        # Такт занят любой попыткой действия (даже неуспешной).
        self._action_done.add(robot_id)

        if kind == "move":
            return self._do_move(robot, payload.get("rel", "forward"))
        if kind == "turn":
            return self._do_turn(robot, payload.get("rel", "left"))
        if kind == "shoot":
            return self._do_shoot(robot, payload.get("rel", "front"))
        if kind == "wait":
            return True
        if kind == "radar_on":
            return self._do_radar(robot, True)
        if kind == "radar_off":
            return self._do_radar(robot, False)
        return False

    def _do_move(self, robot: RobotState, rel: str) -> bool:
        if not robot.can_move(self.tick):
            self.script_log(robot.id, "move: перезарядка от пушек", "warn")
            return False
        if robot.energy < ENERGY_MOVE_COST:
            self.script_log(robot.id, "move: не хватает энергии", "warn")
            return False
        self._action_done.add(robot.id)
        robot.energy -= ENERGY_MOVE_COST
        abs_rel = {"forward": "front", "backward": "back"}[rel]
        dx, dy = vector(abs_dir(robot.dir, abs_rel))
        nx, ny = robot.x + dx, robot.y + dy
        cell = self.arena.get(nx, ny)

        if cell == PIT:
            self.arena.set(robot.x, robot.y, EMPTY)
            self._destroy_robot(robot, "pit")
            return True

        if cell in (STONE,) or self._world.robot_at(nx, ny) is not None or self._world.projectile_at(nx, ny):
            self.script_log(robot.id, f"move: препятствие впереди ({cell_name(cell)})", "warn")
            return False

        oldx, oldy = robot.x, robot.y
        self.arena.set(oldx, oldy, EMPTY)
        robot.x, robot.y = nx, ny
        robot.on_moved(self.tick)
        self.arena.set(nx, ny, ROBOT)

        if cell == AMMO:
            robot.ammo = min(ROBOT_MAX_AMMO, robot.ammo + AMMO_PICKUP_AMOUNT)
            self.arena.set(nx, ny, EMPTY)
            self.events.append(Event("ammo_pickup", t=self.tick, robot=robot.id, ammo=robot.ammo))
        self.events.append(Event("move", t=self.tick, robot=robot.id, from_=[oldx, oldy], to=[nx, ny]))
        return True

    def _do_turn(self, robot: RobotState, rel: str) -> bool:
        if robot.energy < ENERGY_BASE_COST:
            self.script_log(robot.id, "turn: не хватает энергии", "warn")
            return False
        self._action_done.add(robot.id)
        robot.dir = turn_left(robot.dir) if rel == "left" else turn_right(robot.dir)
        self.events.append(Event("turn", t=self.tick, robot=robot.id, dir=robot.dir))
        return True

    def _do_shoot(self, robot: RobotState, rel: str) -> bool:
        if robot.hardware.get(rel) != "cannon":
            self.script_log(robot.id, f"shoot: нет пушки в слоте {rel}", "warn")
            return False
        if robot.ammo <= 0:
            self.script_log(robot.id, "shoot: нет патронов", "warn")
            return False
        if robot.energy < ENERGY_SHOOT_COST:
            self.script_log(robot.id, "shoot: не хватает энергии", "warn")
            return False
        self._action_done.add(robot.id)
        robot.ammo -= 1
        robot.energy -= ENERGY_SHOOT_COST
        dx, dy = vector(abs_dir(robot.dir, rel))
        abs_d = abs_dir(robot.dir, rel)
        sx, sy = robot.x + dx, robot.y + dy
        self._projectile_counter += 1
        proj = Projectile(id=self._projectile_counter, owner=robot.id, x=sx, y=sy, dir=abs_d)
        self.events.append(
            Event("shoot", t=self.tick, robot=robot.id, dir=abs_d, projectile=proj.id)
        )

        # Попадание на месте появления (выстрел в упор): робот/реактор/стена.
        cell = self.arena.get(sx, sy)
        if cell == STONE:
            self._miss(proj, sx, sy, "wall")
            return True
        if cell == REACTOR:
            self._explode_reactor(sx, sy)
            return True
        target = self._world.robot_at(sx, sy)
        if target is not None and target.id != robot.id:
            self._hit_robot(proj, target)
            return True
        self.projectiles.append(proj)
        return True

    def _do_radar(self, robot: RobotState, on: bool) -> bool:
        if not robot.radar:
            self.script_log(robot.id, "radar: радар отсутствует", "warn")
            return False
        self._action_done.add(robot.id)
        robot.radar_active = on
        return True

    # --- Снаряды -----------------------------------------------------------
    def _move_projectiles(self) -> None:
        alive: list[Projectile] = []
        for proj in self.projectiles:
            dx, dy = vector(proj.dir)
            nx, ny = proj.x + dx, proj.y + dy
            self.events.append(
                Event("projectile_move", t=self.tick, projectile=proj.id, from_=[proj.x, proj.y], to=[nx, ny])
            )
            cell = self.arena.get(nx, ny)

            if cell == STONE:
                self._miss(proj, nx, ny, "wall")
                continue
            target_robot = self._world.robot_at(nx, ny)
            if target_robot is not None:
                self._hit_robot(proj, target_robot)
                continue
            if cell == REACTOR:
                self._explode_reactor(nx, ny)
                continue
            if cell == PIT or not self.arena.in_bounds(nx, ny):
                self._miss(proj, nx, ny, "miss")
                continue
            proj.x, proj.y = nx, ny
            alive.append(proj)
        self.projectiles = alive

    def _miss(self, proj: Projectile, x: int, y: int, reason: str) -> None:
        self.events.append(Event("miss", t=self.tick, projectile=proj.id, x=x, y=y, reason=reason))

    def _hit_robot(self, proj: Projectile, target: RobotState) -> None:
        target.health -= proj.damage
        self.events.append(
            Event("hit", t=self.tick, target=target.id, damage=proj.damage, health=target.health, by=proj.owner)
        )
        if target.health <= 0:
            self._destroy_robot(target, "health")

    # --- Реакторы ----------------------------------------------------------
    def _explode_reactor(self, x: int, y: int) -> None:
        queue = [(x, y)]
        while queue:
            cx, cy = queue.pop(0)
            if self.arena.get(cx, cy) != REACTOR:
                continue
            self.arena.set(cx, cy, EMPTY)
            affected: list[int] = []
            for dy in range(-REACTOR_BLAST_RADIUS, REACTOR_BLAST_RADIUS + 1):
                for dx in range(-REACTOR_BLAST_RADIUS, REACTOR_BLAST_RADIUS + 1):
                    nx, ny = cx + dx, cy + dy
                    if self.arena.get(nx, ny) == REACTOR and (nx, ny) != (cx, cy):
                        queue.append((nx, ny))
                    robot = self._world.robot_at(nx, ny)
                    if robot is not None:
                        robot.health -= REACTOR_DAMAGE
                        affected.append(robot.id)
                        if robot.health <= 0:
                            self._destroy_robot(robot, "explosion")
            self.events.append(
                Event("explosion", t=self.tick, x=cx, y=cy, damage=REACTOR_DAMAGE, affected=sorted(affected))
            )

    # --- Эффекты -----------------------------------------------------------
    def _apply_effects(self) -> None:
        for robot in sorted(self.robots.values(), key=lambda r: r.id):
            if not robot.alive:
                continue
            if robot.radar_active:
                robot.energy -= ENERGY_RADAR_COST
            robot.energy -= ENERGY_BASE_COST
            if self.arena.get(robot.x, robot.y) == RECHARGE:
                robot.energy += RECHARGE_AMOUNT
                self.events.append(Event("recharge", t=self.tick, robot=robot.id))
            if robot.energy <= 0:
                robot.energy = 0
                if not robot.shutdown:
                    robot.shutdown = True
                    self.events.append(Event("shutdown", t=self.tick, robot=robot.id))
            elif robot.shutdown:
                robot.shutdown = False
                self.events.append(Event("energy_restored", t=self.tick, robot=robot.id))

    def _destroy_robot(self, robot: RobotState, reason: str) -> None:
        if not robot.alive:
            return
        robot.alive = False
        robot.shutdown = False
        self.arena.set(robot.x, robot.y, EMPTY)
        self.events.append(Event("destroyed", t=self.tick, robot=robot.id, reason=reason))
        self.projectiles = [p for p in self.projectiles if p.owner != robot.id]

    # --- Лог скриптов ------------------------------------------------------
    def script_log(self, robot_id: int, message: str, level: str = "debug") -> None:
        self.events.append(
            Event("script_log", t=self.tick, robot=robot_id, level=level, message=message)
        )

    # --- Конец боя ---------------------------------------------------------
    def _check_end(self, tick: int) -> bool:
        alive = [r for r in self.robots.values() if r.alive]
        if len(alive) == 0:
            self.winner = None
            self.end_reason = "draw"
            return True
        if len(alive) == 1:
            self.winner = alive[0].id
            self.end_reason = "last_standing"
            return True
        return False

    def _finish_time_limit(self, tick: int) -> None:
        alive = [r for r in self.robots.values() if r.alive]
        if not alive:
            self.winner = None
            self.end_reason = "draw"
            return
        alive.sort(key=lambda r: (-r.health, -r.ammo, -r.energy, r.id))
        self.winner = alive[0].id
        self.end_reason = "time_limit"
