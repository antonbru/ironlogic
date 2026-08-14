"""Детальные тесты механик движка: движение, стрельба, реакторы, энергия."""

from __future__ import annotations

from ironlogic.config import (
    AMMO_PICKUP_AMOUNT,
    ENERGY_BASE_COST,
    ENERGY_MOVE_COST,
    ENERGY_SHOOT_COST,
    PROJECTILE_DAMAGE,
    REACTOR_DAMAGE,
    RECHARGE_AMOUNT,
    ROBOT_MAX_AMMO,
    ROBOT_START_ENERGY,
    ROBOT_START_HEALTH,
)
from ironlogic.engine.arena import Arena
from ironlogic.engine.battle import BattleConfig, BattleRunner
from ironlogic.engine.cells import AMMO, EAST, EMPTY, PIT, REACTOR, RECHARGE, ROBOT, STONE
from ironlogic.engine.robot import RobotState


def _manual_runner(arena: Arena, robots: list[RobotState]) -> BattleRunner:
    """Раннер с ручной ареной и роботами (без авто-спавна)."""
    config = BattleConfig(max_ticks=100)
    runner = BattleRunner(config, arena=arena)
    for r in robots:
        runner.robots[r.id] = r
        arena.set(r.x, r.y, ROBOT)
    return runner


def _mk_robot(r_id: int, x: int, y: int, dir_: str = EAST, hardware: dict | None = None) -> RobotState:
    hw = hardware or {"front": "cannon", "right": "cannon", "back": "cannon", "left": "cannon"}
    return RobotState(id=r_id, name=f"R{r_id}", file="test.py", x=x, y=y, dir=dir_, hardware=dict(hw))


# --- Движение -----------------------------------------------------------


def test_move_cooldown_by_cannon_count():
    """Cooldown движения зависит от числа пушек."""
    arena = Arena(12, 12)
    r1 = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "eye", "left": "empty"})
    r2 = _mk_robot(1, 2, 4, hardware={"front": "cannon", "right": "cannon", "back": "eye", "left": "eye"})
    r3 = _mk_robot(2, 2, 6, hardware={"front": "cannon", "right": "cannon", "back": "cannon", "left": "cannon"})
    assert r1.can_move(0), "0 пушек — движение каждый такт"
    assert not r2.can_move(0), "2 пушки — движение каждые 2 такта (на tick 0 нельзя)"
    assert r2.can_move(1)
    assert not r3.can_move(0), "4 пушки — робот неподвижен"
    assert not r3.can_move(10)


def test_first_move_at_tick_zero():
    """Робот с 0/1 пушкой может двигаться на первом такте."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "empty"})
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "move", {"rel": "forward"}) is True
    assert (r.x, r.y) == (3, 2)


def test_move_blocked_by_stone():
    """Движение в камень не выполняется, робот застревает."""
    arena = Arena(12, 12)
    arena.set(3, 2, STONE)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "empty"})
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "move", {"rel": "forward"}) is False
    assert (r.x, r.y) == (2, 2)
    assert r.alive
    assert 0 in runner._action_done, "неуспешное движение тратит такт"


def test_move_blocked_by_other_robot():
    """Движение в робота не выполняется."""
    arena = Arena(12, 12)
    r1 = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "empty"})
    r2 = _mk_robot(1, 3, 2)
    runner = _manual_runner(arena, [r1, r2])
    assert runner.try_action(0, "move", {"rel": "forward"}) is False
    assert (r1.x, r1.y) == (2, 2)
    assert (r2.x, r2.y) == (3, 2)


def test_move_into_pit_destroys():
    """Движение в яму — робот уничтожен."""
    arena = Arena(12, 12)
    arena.set(3, 2, PIT)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "empty"})
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "move", {"rel": "forward"}) is True
    assert not r.alive
    reasons = [e["reason"] for e in runner.events if e["type"] == "destroyed"]
    assert reasons == ["pit"]


def test_move_into_ammo_pickup():
    """Заезд на ящик с патронами: +5 патронов, клетка становится EMPTY."""
    arena = Arena(12, 12)
    arena.set(3, 2, AMMO)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "empty"})
    start_ammo = r.ammo
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "move", {"rel": "forward"}) is True
    assert r.ammo == min(ROBOT_MAX_AMMO, start_ammo + AMMO_PICKUP_AMOUNT)
    assert arena.get(3, 2) == EMPTY
    assert (r.x, r.y) == (3, 2)


def test_ammo_cap_at_20():
    """Патроны не превышают максимум 20."""
    arena = Arena(12, 12)
    arena.set(3, 2, AMMO)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "empty"})
    r.ammo = ROBOT_MAX_AMMO - 1
    runner = _manual_runner(arena, [r])
    runner.try_action(0, "move", {"rel": "forward"})
    assert r.ammo == ROBOT_MAX_AMMO


# --- Стрельба -----------------------------------------------------------


def test_shoot_point_blank_hit():
    """Выстрел в упор наносит урон 15."""
    arena = Arena(12, 12)
    attacker = _mk_robot(0, 2, 2, hardware={"front": "cannon", "right": "empty", "back": "empty", "left": "eye"})
    victim = _mk_robot(1, 3, 2)
    runner = _manual_runner(arena, [attacker, victim])
    start_health = victim.health
    assert runner.try_action(0, "shoot", {"rel": "front"}) is True
    assert victim.health == start_health - PROJECTILE_DAMAGE
    hits = [e for e in runner.events if e["type"] == "hit"]
    assert len(hits) == 1
    assert hits[0]["damage"] == PROJECTILE_DAMAGE


def test_shoot_wall_miss():
    """Выстрел в стену — промах, снаряд уничтожен."""
    arena = Arena(12, 12)
    arena.set(3, 2, STONE)
    r = _mk_robot(0, 2, 2, hardware={"front": "cannon", "right": "empty", "back": "empty", "left": "eye"})
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "shoot", {"rel": "front"}) is True
    assert runner.projectiles == [], "снаряд не должен лететь после промаха о стену"
    miss = [e for e in runner.events if e["type"] == "miss"]
    assert len(miss) == 1
    assert miss[0]["reason"] == "wall"


def test_projectile_moves_and_hits_from_distance():
    """Снаряд летит 1 клетку за такт и попадает в цель на дистанции."""
    arena = Arena(12, 12)
    attacker = _mk_robot(0, 2, 2, hardware={"front": "cannon", "right": "empty", "back": "empty", "left": "eye"})
    victim = _mk_robot(1, 4, 2)
    runner = _manual_runner(arena, [attacker, victim])
    runner.try_action(0, "shoot", {"rel": "front"})  # снаряд на (3,2)
    assert len(runner.projectiles) == 1
    runner._move_projectiles()  # снаряд летит на (4,2) и попадает
    assert victim.health == ROBOT_START_HEALTH - PROJECTILE_DAMAGE
    assert runner.projectiles == []


def test_shoot_no_ammo():
    """Стрельба без патронов — неуспешное действие (такт потрачен)."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "cannon", "right": "empty", "back": "empty", "left": "eye"})
    r.ammo = 0
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "shoot", {"rel": "front"}) is False
    assert 0 in runner._action_done, "неуспешная попытка действия должна тратить такт"


def test_shoot_no_cannon():
    """Стрельба из слота без пушки — неуспешное действие."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "eye"})
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "shoot", {"rel": "front"}) is False


# --- Реакторы -----------------------------------------------------------


def test_reactor_explosion_damage():
    """Взрыв реактора: урон 40 роботам в радиусе 1, реактор становится EMPTY."""
    arena = Arena(12, 12)
    arena.set(5, 5, REACTOR)
    nearby = _mk_robot(0, 5, 6)
    far = _mk_robot(1, 9, 9)
    runner = _manual_runner(arena, [nearby, far])
    runner._explode_reactor(5, 5)
    assert arena.get(5, 5) == EMPTY
    assert nearby.health == ROBOT_START_HEALTH - REACTOR_DAMAGE
    assert far.health == ROBOT_START_HEALTH, "робот вне радиуса не получает урон"
    explosions = [e for e in runner.events if e["type"] == "explosion"]
    assert len(explosions) == 1
    assert explosions[0]["damage"] == REACTOR_DAMAGE


def test_chain_reactor_explosion():
    """Взрыв одного реактора подрывает соседний (цепная реакция)."""
    arena = Arena(12, 12)
    arena.set(5, 5, REACTOR)
    arena.set(6, 5, REACTOR)
    victim = _mk_robot(0, 7, 5)
    runner = _manual_runner(arena, [victim])
    runner._explode_reactor(5, 5)
    assert arena.get(5, 5) == EMPTY
    assert arena.get(6, 5) == EMPTY, "соседний реактор должен взорваться"
    explosions = [e for e in runner.events if e["type"] == "explosion"]
    assert len(explosions) == 2


def test_shoot_reactor_from_distance():
    """Снаряд, попавший в реактор, взрывает его."""
    arena = Arena(12, 12)
    arena.set(4, 2, REACTOR)
    r = _mk_robot(0, 2, 2, hardware={"front": "cannon", "right": "empty", "back": "empty", "left": "eye"})
    runner = _manual_runner(arena, [r])
    runner.try_action(0, "shoot", {"rel": "front"})  # снаряд на (3,2)
    runner._move_projectiles()  # снаряд летит на (4,2) и взрывает реактор
    assert arena.get(4, 2) == EMPTY
    explosions = [e for e in runner.events if e["type"] == "explosion"]
    assert len(explosions) == 1


# --- Энергия ------------------------------------------------------------


def test_energy_base_cost_each_tick():
    """Базовый расход энергии 1 за такт."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "eye"})
    runner = _manual_runner(arena, [r])
    runner._apply_effects()
    assert r.energy == ROBOT_START_ENERGY - ENERGY_BASE_COST


def test_energy_shutdown_and_restore():
    """При энергии 0 робот в shutdown; на RECHARGE энергия восстанавливается."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "eye"})
    r.energy = 1
    runner = _manual_runner(arena, [r])
    runner._apply_effects()
    assert r.shutdown
    arena.set(2, 2, RECHARGE)
    shutdown = [e for e in runner.events if e["type"] == "shutdown"]
    assert len(shutdown) == 1
    r.energy = 1
    runner._apply_effects()
    assert r.energy == 1 - ENERGY_BASE_COST + RECHARGE_AMOUNT
    assert not r.shutdown


def test_energy_move_and_shoot_costs():
    """Движение тратит 2 энергии, выстрел — 3."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "cannon", "right": "empty", "back": "empty", "left": "eye"})
    runner = _manual_runner(arena, [r])
    runner.try_action(0, "move", {"rel": "forward"})
    assert r.energy == ROBOT_START_ENERGY - ENERGY_MOVE_COST
    assert (r.x, r.y) == (3, 2)
    runner._action_done = set()
    runner.try_action(0, "shoot", {"rel": "front"})
    assert r.energy == ROBOT_START_ENERGY - ENERGY_MOVE_COST - ENERGY_SHOOT_COST


def test_second_action_same_tick_blocked():
    """Второе действие в такте возвращает False (первое — финальное)."""
    arena = Arena(12, 12)
    r = _mk_robot(0, 2, 2, hardware={"front": "eye", "right": "empty", "back": "empty", "left": "eye"})
    runner = _manual_runner(arena, [r])
    assert runner.try_action(0, "move", {"rel": "forward"}) is True
    assert (r.x, r.y) == (3, 2)
    assert runner.try_action(0, "turn", {"rel": "left"}) is False, "второе действие в такте запрещено"