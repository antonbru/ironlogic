"""Map generation by preset and seed (deterministic)."""

from __future__ import annotations

import random
from collections import deque

from ironlogic.config import SPAWN_MIN_DISTANCE
from ironlogic.engine.arena import Arena
from ironlogic.engine.cells import (
    AMMO,
    EAST,
    EMPTY,
    NORTH,
    PIT,
    REACTOR,
    RECHARGE,
    SOUTH,
    STONE,
    WEST,
)

__all__ = ["PRESETS", "generate", "spawn_positions", "default_size"]

PRESETS = ("arena", "ruins", "ravine", "junkyard", "symmetric_1v1")


def default_size(num_robots: int) -> tuple[int, int]:
    """Default arena size depending on the number of robots."""
    if num_robots <= 2:
        return (24, 24)
    if num_robots <= 4:
        return (32, 32)
    return (40, 40)


def _fill(w: int, h: int, rng: random.Random, preset: str) -> Arena:
    arena = Arena(w, h, preset=preset, seed=0)

    if preset == "symmetric_1v1":
        # Generate the left half, then mirror it to the right half.
        half = (w - 2) // 2
        for y in range(1, h - 1):
            for x in range(1, half + 1):
                r = rng.random()
                if r < 0.05:
                    arena.set(x, y, STONE)
                elif r < 0.09:
                    arena.set(x, y, PIT)
                elif r < 0.14:
                    arena.set(x, y, AMMO)
                elif r < 0.18:
                    arena.set(x, y, RECHARGE)
                elif r < 0.22:
                    arena.set(x, y, REACTOR)
        for y in range(1, h - 1):
            for x in range(1, half + 1):
                arena.set(w - 1 - x, y, arena.grid[y][x])
        return arena

    # arena / ruins / ravine / junkyard
    stone_prob = {"arena": 0.02, "ruins": 0.14, "ravine": 0.12, "junkyard": 0.04}[preset]
    pit_prob = {"arena": 0.02, "ruins": 0.02, "ravine": 0.06, "junkyard": 0.08}[preset]
    reactor_prob = {"arena": 0.01, "ruins": 0.02, "ravine": 0.01, "junkyard": 0.06}[preset]
    ammo_prob = {"arena": 0.03, "ruins": 0.03, "ravine": 0.02, "junkyard": 0.02}[preset]
    recharge_prob = {"arena": 0.03, "ruins": 0.02, "ravine": 0.03, "junkyard": 0.01}[preset]

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r = rng.random()
            if r < stone_prob:
                arena.set(x, y, STONE)
            elif r < stone_prob + pit_prob:
                arena.set(x, y, PIT)
            elif r < stone_prob + pit_prob + reactor_prob:
                arena.set(x, y, REACTOR)
            elif r < stone_prob + pit_prob + reactor_prob + ammo_prob:
                arena.set(x, y, AMMO)
            elif r < stone_prob + pit_prob + reactor_prob + ammo_prob + recharge_prob:
                arena.set(x, y, RECHARGE)

    # ravine: vertical corridors / walls
    if preset == "ravine":
        for x in range(2, w - 1, 3):
            for y in range(1, h - 1):
                if arena.grid[y][x] == EMPTY and rng.random() < 0.5:
                    arena.set(x, y, STONE)

    return arena


def _bfs_reach(arena: Arena, kind: int, start: tuple[int, int]) -> bool:
    """Check whether a cell of type 'kind' is reachable from 'start' (BFS)."""
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
            if cell == PIT:
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
    return False


def _satisfies_invariants(arena: Arena, preset: str) -> bool:
    """Check required map invariants.

    - enough empty cells for spawns;
    - every empty cell can reach (BFS) at least one RECHARGE pad and one AMMO
      crate, so every robot can reach vital resources;
    - symmetric_1v1 must be mirrored vertically.
    """
    if len(arena.empty_cells()) < 8:
        return False
    if preset == "symmetric_1v1":
        w = arena.width
        for y in range(arena.height):
            for x in range(1, w // 2 + 1):
                if arena.get(x, y) != arena.get(w - 1 - x, y):
                    return False
    for y in range(1, arena.height - 1):
        for x in range(1, arena.width - 1):
            if arena.get(x, y) != EMPTY:
                continue
            if not _bfs_reach(arena, RECHARGE, (x, y)):
                return False
            if not _bfs_reach(arena, AMMO, (x, y)):
                return False
    return True


def generate(preset: str, seed: int, width: int | None = None, height: int | None = None) -> Arena:
    """Generate an arena deterministically (random.Random(seed)).

    If invariants fail, the map is regenerated with a shifted seed
    (up to 10 attempts), as required by the spec.
    """
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Available: {', '.join(PRESETS)}")
    w = width or default_size(2)[0]
    h = height or default_size(2)[1]

    for attempt in range(10):
        rng = random.Random(seed * 100 + attempt)
        arena = _fill(w, h, rng, preset)
        arena.seed = seed
        arena.preset = preset
        if _satisfies_invariants(arena, preset):
            return arena
    arena = _fill(w, h, random.Random(seed * 100), preset)
    arena.seed = seed
    arena.preset = preset
    return arena


def spawn_positions(arena: Arena, count: int, seed: int) -> list[tuple[int, int, str]]:
    """Pick robot spawn positions (empty cells, min distance between spawns)."""
    rng = random.Random(seed * 7 + count)
    empties = arena.empty_cells()
    if count == 0:
        return []
    if count >= len(empties):
        empties = arena.empty_cells() or [(1, 1)]

    chosen: list[tuple[int, int]] = []
    attempts = 0
    while len(chosen) < count and attempts < 500:
        attempts += 1
        x, y = rng.choice(empties)
        if all((x - cx) ** 2 + (y - cy) ** 2 >= SPAWN_MIN_DISTANCE ** 2 for cx, cy in chosen):
            chosen.append((x, y))
    while len(chosen) < count:
        x, y = empties.pop()
        chosen.append((x, y))

    dirs = [EAST, WEST, NORTH, SOUTH]
    return [(x, y, dirs[i % 4]) for i, (x, y) in enumerate(chosen)]