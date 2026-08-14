"""Типизированные события боя и сериализация в JSON."""

from __future__ import annotations

import json
from typing import Any

__all__ = ["Event", "battle_to_dict", "battle_from_dict", "load_battle_json"]


def Event(type_: str, **kwargs: Any) -> dict[str, Any]:
    """Создаёт событие боя (словарь с типом и полями)."""
    return {"type": type_, **kwargs}


def battle_to_dict(battle_result: Any) -> dict:
    """Сериализация BattleResult в dict (для battle.json)."""
    return {
        "version": 1,
        "map": {
            "preset": battle_result.map.preset,
            "seed": battle_result.map.seed,
            "width": battle_result.map.width,
            "height": battle_result.map.height,
            "grid": battle_result.map.grid_string(),
        },
        "robots": battle_result.start_robots,
        "max_ticks": battle_result.max_ticks,
        "events": battle_result.events,
        "winner": battle_result.winner,
        "end_reason": battle_result.end_reason,
        "ticks": battle_result.ticks,
    }


def load_battle_json(path: str) -> dict:
    """Загружает battle.json из файла."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def battle_from_dict(data: dict) -> dict:
    """Обратный ход battle_to_dict: возвращает dict-представление (для replay)."""
    return data