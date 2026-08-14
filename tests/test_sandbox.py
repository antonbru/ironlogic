"""Sandbox tests: instruction budget, recursion limit, syntax errors with line numbers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ironlogic.botapi.errors import BotCompileError, BudgetError
from ironlogic.botapi.loader import load_bot
from ironlogic.botapi.sandbox import run_in_sandbox


def test_syntax_error_reports_line(tmp_path):
    """SyntaxError must report the offending line number."""
    bad = tmp_path / "syntax.py"
    bad.write_text(
        "from ironlogic_api import Robot\n"
        "robot = Robot()\n"
        "def on_tick(r):\n"
        "    if r.eye('front') ==\n",
        encoding="utf-8",
    )
    with pytest.raises(BotCompileError) as excinfo:
        load_bot(bad)
    assert excinfo.value.line == 4


def test_recursion_limit_exceeded():
    """Recursion deeper than MAX_RECURSION_DEPTH raises BudgetError."""

    def recursive(n: int) -> int:
        return recursive(n + 1)

    with pytest.raises(BudgetError):
        run_in_sandbox(recursive, 0)


def test_infinite_loop_hits_budget():
    """An infinite loop within one tick raises BudgetError (wait action)."""

    def loop() -> None:
        i = 0
        while True:
            i += 1

    with pytest.raises(BudgetError):
        run_in_sandbox(loop)


def test_budget_error_in_battle_generates_event(tmp_path):
    """Budget exceeded during battle produces a budget_exceeded event."""
    from ironlogic.engine.arena import Arena
    from ironlogic.engine.battle import BattleConfig, BattleRunner
    from ironlogic.engine.cells import ROBOT
    from ironlogic.engine.robot import RobotState

    bot = tmp_path / "spinner.py"
    bot.write_text(
        "from ironlogic_api import Robot\n"
        "robot = Robot(front='eye', right='eye', back='eye', left='eye')\n"
        "def on_tick(r):\n"
        "    i = 0\n"
        "    while True:\n"
        "        i += 1\n",
        encoding="utf-8",
    )
    loaded = load_bot(bot)
    arena = Arena(12, 12)
    runner = BattleRunner(BattleConfig(max_ticks=5), arena=arena)
    r = RobotState(id=0, name="Spinner", file="spinner.py", x=2, y=2, dir="E",
                   hardware={"front": "eye", "right": "eye", "back": "eye", "left": "eye"})
    runner.robots[0] = r
    arena.set(2, 2, ROBOT)
    runner._run_bot_tick(loaded, r)
    types = [e["type"] for e in runner.events]
    assert "budget_exceeded" in types


def test_normal_bot_within_budget():
    """A normal bot runs within the instruction budget."""

    def normal() -> int:
        return sum(i for i in range(100))

    assert run_in_sandbox(normal) == sum(range(100))