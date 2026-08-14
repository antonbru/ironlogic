"""Тесты движка: детерминизм, движение, стрельба, реакторы, энергия."""

from __future__ import annotations

from pathlib import Path

from ironlogic.botapi.loader import load_bot
from ironlogic.engine.battle import BattleConfig, BattleRunner
from ironlogic.engine.cells import AMMO, EAST, EMPTY, PIT, REACTOR, RECHARGE, ROBOT, STONE
from ironlogic.engine.arena import Arena
from ironlogic.engine.events import battle_to_dict

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _runner(bots, seed=42, ticks=1000, preset="arena"):
    loaded = [load_bot(p) for p in bots]
    config = BattleConfig(map_preset=preset, seed=seed, max_ticks=ticks)
    return BattleRunner(config, loaded_bots=loaded)


def test_determinism():
    """Одинаковые входные данные → одинаковый battle.json."""
    bots = [str(EXAMPLES / "wanderer.py"), str(EXAMPLES / "kickme.py")]
    r1 = _runner(bots, seed=7).run()
    r2 = _runner(bots, seed=7).run()
    assert battle_to_dict(r1) == battle_to_dict(r2)


def test_battle_runs_to_completion():
    """Бой двух роботов завершается с победителем."""
    bots = [str(EXAMPLES / "wanderer.py"), str(EXAMPLES / "kickme.py")]
    result = _runner(bots, ticks=500).run()
    assert result.end_reason in ("last_standing", "time_limit")
    assert result.winner in (0, 1)


def test_arena_border_is_stone():
    """Граница поля — непроходимый камень."""
    arena = Arena(10, 8)
    for x in range(10):
        assert arena.get(x, 0) == STONE
        assert arena.get(x, 7) == STONE
    for y in range(8):
        assert arena.get(0, y) == STONE
        assert arena.get(9, y) == STONE


def test_one_robot_battle_ends():
    """Один робот в бою — сразу победа."""
    bots = [str(EXAMPLES / "kickme.py")]
    result = _runner(bots, ticks=10).run()
    assert result.winner == 0
    assert result.end_reason == "last_standing"