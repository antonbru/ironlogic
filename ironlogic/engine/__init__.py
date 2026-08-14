"""Движок симуляции боя (чистый Python, без внешних зависимостей)."""

from ironlogic.engine.cells import *  # noqa: F401,F403
from ironlogic.engine.arena import Arena  # noqa: F401
from ironlogic.engine.robot import RobotState  # noqa: F401
from ironlogic.engine.projectile import Projectile  # noqa: F401
from ironlogic.engine.battle import BattleConfig, BattleRunner, BattleResult  # noqa: F401
from ironlogic.engine.mapgen import (  # noqa: F401
    PRESETS,
    generate,
    spawn_positions,
    default_size,
)
from ironlogic.engine.events import battle_to_dict, load_battle_json  # noqa: F401