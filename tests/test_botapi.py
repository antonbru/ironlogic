"""Тесты загрузки и песочницы ботов."""

from __future__ import annotations

from pathlib import Path

from ironlogic.botapi.errors import BotCompileError
from ironlogic.botapi.loader import load_bot

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_all_examples_compile():
    """Все примеры компилируются."""
    for path in EXAMPLES.glob("*.py"):
        loaded = load_bot(path)
        assert loaded.robot is not None
        assert callable(loaded.on_tick)


def test_missing_robot_raises(tmp_path):
    """Файл без 'robot' → BotCompileError."""
    bad = tmp_path / "bad.py"
    bad.write_text("def on_tick(r):\n    r.wait()\n", encoding="utf-8")
    try:
        load_bot(bad)
        assert False, "должна быть ошибка"
    except BotCompileError:
        pass


def test_missing_on_tick_raises(tmp_path):
    """Файл без 'on_tick' → BotCompileError."""
    bad = tmp_path / "bad.py"
    bad.write_text("from ironlogic_api import Robot\nrobot = Robot()\n", encoding="utf-8")
    try:
        load_bot(bad)
        assert False, "должна быть ошибка"
    except BotCompileError:
        pass


def test_invalid_hardware_raises(tmp_path):
    """Недопустимое значение слота железа → BotCompileError."""
    bad = tmp_path / "bad.py"
    bad.write_text(
        "from ironlogic_api import Robot\n"
        "robot = Robot(front='laser')\n"
        "def on_tick(r):\n    r.wait()\n",
        encoding="utf-8",
    )
    try:
        load_bot(bad)
        assert False, "должна быть ошибка"
    except BotCompileError:
        pass


def test_import_blocked(tmp_path):
    """import в коде бота блокируется."""
    bad = tmp_path / "bad.py"
    bad.write_text("import os\nfrom ironlogic_api import Robot\nrobot = Robot()\ndef on_tick(r):\n    r.wait()\n", encoding="utf-8")
    try:
        load_bot(bad)
        assert False, "import должен быть заблокирован"
    except BotCompileError:
        pass