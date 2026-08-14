"""CLI battle / replay / check integration tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ironlogic", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_battle_creates_valid_json(tmp_path):
    out = tmp_path / "battle.json"
    proc = _run_cli(
        "battle", "--map", "arena", "--seed", "7", "--ticks", "100",
        "--robots", str(EXAMPLES / "wanderer.py"), str(EXAMPLES / "kickme.py"),
        "--out", str(out),
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["map"]["preset"] == "arena"
    assert data["map"]["seed"] == 7
    assert len(data["robots"]) == 2
    assert data["ticks"] <= 100
    assert data["end_reason"] in ("last_standing", "time_limit", "draw")
    assert "Battle.json" in proc.stdout


def test_battle_identical_for_same_seed(tmp_path):
    out1 = tmp_path / "a.json"
    out2 = tmp_path / "b.json"
    args = [
        "battle", "--map", "arena", "--seed", "42", "--ticks", "200",
        "--robots", str(EXAMPLES / "wanderer.py"), str(EXAMPLES / "kickme.py"),
    ]
    _run_cli(*args, "--out", str(out1))
    _run_cli(*args, "--out", str(out2))
    assert out1.read_bytes() == out2.read_bytes()


def test_replay_prints_summary(tmp_path):
    out = tmp_path / "battle.json"
    _run_cli(
        "battle", "--map", "ruins", "--seed", "3", "--ticks", "100",
        "--robots", str(EXAMPLES / "turret.py"), str(EXAMPLES / "wanderer.py"),
        "--out", str(out),
    )
    proc = _run_cli("replay", str(out))
    assert proc.returncode == 0, proc.stderr
    assert "Сводка" in proc.stdout
    assert "Победитель" in proc.stdout


def test_battle_compile_error_nonzero(tmp_path):
    bot = tmp_path / "bad.py"
    bot.write_text("def on_tick(r):\n    r.wait()\n", encoding="utf-8")
    proc = _run_cli(
        "battle", "--map", "arena", "--seed", "1", "--ticks", "10",
        "--robots", str(bot), str(EXAMPLES / "kickme.py"),
        "--out", str(tmp_path / "x.json"),
    )
    assert proc.returncode != 0


def test_battle_unknown_map_nonzero(tmp_path):
    proc = _run_cli(
        "battle", "--map", "nope", "--seed", "1", "--ticks", "10",
        "--robots", str(EXAMPLES / "kickme.py"), str(EXAMPLES / "kickme.py"),
        "--out", str(tmp_path / "x.json"),
    )
    assert proc.returncode != 0


def test_check_valid_bot(tmp_path):
    bot = tmp_path / "ok.py"
    bot.write_text(
        "from ironlogic_api import Robot\n"
        "robot = Robot(name='Ok')\n"
        "def on_tick(r):\n    r.wait()\n",
        encoding="utf-8",
    )
    proc = _run_cli("check", str(bot))
    assert proc.returncode == 0
    assert "OK" in proc.stdout


def test_check_invalid_bot(tmp_path):
    bot = tmp_path / "bad.py"
    bot.write_text("def on_tick(r):\n    r.wait()\n", encoding="utf-8")
    proc = _run_cli("check", str(bot))
    assert proc.returncode == 1


def test_list_maps_and_bots():
    proc_maps = _run_cli("list-maps")
    assert proc_maps.returncode == 0
    for preset in ("arena", "ruins", "ravine", "junkyard", "symmetric_1v1"):
        assert preset in proc_maps.stdout

    proc_bots = _run_cli("list-bots", "--dir", "examples")
    assert proc_bots.returncode == 0
    assert "kickme.py" in proc_bots.stdout