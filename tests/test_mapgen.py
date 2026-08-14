"""Тесты генератора карт: инварианты, воспроизводимость по seed, симметрия."""

from __future__ import annotations

from collections import deque

from ironlogic.engine.arena import Arena
from ironlogic.engine.cells import AMMO, EMPTY, REACTOR, RECHARGE, STONE
from ironlogic.engine.mapgen import PRESETS, default_size, generate, spawn_positions


def _bfs_reach(arena: Arena, kind: int, start: tuple[int, int]) -> bool:
    """Достижимость клетки типа kind из start (BFS, проходимые клетки)."""
    q: deque[tuple[int, int]] = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        if arena.get(x, y) == kind:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen or not arena.in_bounds(nx, ny):
                continue
            cell = arena.get(nx, ny)
            if cell in (STONE, REACTOR):
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
    return False


def test_default_sizes():
    """Размер арены по умолчанию зависит от числа роботов."""
    assert default_size(2) == (24, 24)
    assert default_size(3) == (32, 32)
    assert default_size(5) == (40, 40)


def test_generate_all_presets_work():
    """Все пресеты генерируются с корректными размерами."""
    for preset in PRESETS:
        arena = generate(preset, seed=42)
        assert arena.width == 24
        assert arena.height == 24
        assert arena.preset == preset


def test_border_is_stone():
    """Граница любой сгенерированной карты — камень."""
    for preset in PRESETS:
        arena = generate(preset, seed=1)
        for x in range(arena.width):
            assert arena.get(x, 0) == STONE
            assert arena.get(x, arena.height - 1) == STONE
        for y in range(arena.height):
            assert arena.get(0, y) == STONE
            assert arena.get(arena.width - 1, y) == STONE


def test_reproducible_by_seed():
    """Одинаковый seed даёт одинаковую карту."""
    for preset in PRESETS:
        a1 = generate(preset, seed=7)
        a2 = generate(preset, seed=7)
        assert a1.grid_string() == a2.grid_string()
        a3 = generate(preset, seed=8)
        assert a1.grid_string() != a3.grid_string()


def test_reachable_ammo_and_recharge():
    """Из пустой клетки достижимы розетка и ящик с патронами (BFS)."""
    for preset in PRESETS:
        arena = generate(preset, seed=42)
        empties = arena.empty_cells()
        assert len(empties) >= 8
        start = empties[0]
        assert _bfs_reach(arena, AMMO, start), f"{preset}: патроны недостижимы"
        assert _bfs_reach(arena, RECHARGE, start), f"{preset}: розетка недостижима"


def test_symmetric_1v1_symmetry():
    """symmetric_1v1 зеркально-симметрична по вертикали."""
    for seed in range(5):
        arena = generate("symmetric_1v1", seed=seed)
        w = arena.width
        for y in range(arena.height):
            for x in range(1, w // 2 + 1):
                assert arena.get(x, y) == arena.get(w - 1 - x, y)


def test_spawn_positions_are_empty_and_far():
    """Спавны на пустых клетках, дистанция между ними >= минимальной."""
    arena = generate("arena", seed=42)
    positions = spawn_positions(arena, 4, 42)
    assert len(positions) == 4
    coords = [(x, y) for x, y, _ in positions]
    for x, y in coords:
        assert arena.get(x, y) == EMPTY
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            x1, y1 = coords[i]
            x2, y2 = coords[j]
            dist_sq = (x1 - x2) ** 2 + (y1 - y2) ** 2
            assert dist_sq >= 8 ** 2, "спавны слишком близко"


def test_unknown_preset_raises():
    """Неизвестный пресет — ValueError."""
    try:
        generate("nope", seed=1)
        assert False, "должен быть ValueError"
    except ValueError:
        pass


def test_many_seeds_keep_invariants():
    """Инварианты выполняются для разных seed."""
    for preset in PRESETS:
        for seed in range(6):
            arena = generate(preset, seed=seed)
            empties = arena.empty_cells()
            assert len(empties) >= 8, f"{preset} seed={seed}"
            assert _bfs_reach(arena, AMMO, empties[0]), f"{preset} seed={seed} AMMO"
            assert _bfs_reach(arena, RECHARGE, empties[0]), f"{preset} seed={seed} RECHARGE"