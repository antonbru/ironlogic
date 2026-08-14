"""Арена — прямоугольная сетка клеток с метаданными."""

from __future__ import annotations

from dataclasses import dataclass, field

from ironlogic.engine.cells import EMPTY, STONE, cell_name

__all__ = ["Arena"]


@dataclass
class Arena:
    """Прямоугольная сетка клеток.

    Граница поля (x=0, x=width-1, y=0, y=height-1) всегда камень (STONE).
    """

    width: int
    height: int
    grid: list[list[int]] = field(init=False)
    preset: str = "arena"
    seed: int = 0

    def __post_init__(self) -> None:
        self.grid = [
            [STONE] + [EMPTY] * (self.width - 2) + [STONE]
            for _ in range(self.height)
        ]
        for x in range(self.width):
            self.grid[0][x] = STONE
            self.grid[self.height - 1][x] = STONE

    @classmethod
    def from_grid(cls, width: int, height: int, grid: list[list[int]], *, preset: str = "arena", seed: int = 0) -> "Arena":
        """Создаёт арену из готовой сетки."""
        arena = cls.__new__(cls)
        arena.width = width
        arena.height = height
        arena.grid = grid
        arena.preset = preset
        arena.seed = seed
        return arena

    def in_bounds(self, x: int, y: int) -> bool:
        """Проверка, что координаты внутри поля (включая границу-камень)."""
        return 0 <= x < self.width and 0 <= y < self.height

    def inner_x(self, x: int) -> bool:
        """Координата внутри игровой зоны (не на границе)."""
        return 1 <= x < self.width - 1

    def inner_y(self, y: int) -> bool:
        return 1 <= y < self.height - 1

    def get(self, x: int, y: int) -> int:
        """Тип клетки (вне поля — STONE)."""
        if not self.in_bounds(x, y):
            return STONE
        return self.grid[y][x]

    def set(self, x: int, y: int, kind: int) -> None:
        """Записывает тип клетки."""
        if self.in_bounds(x, y):
            self.grid[y][x] = kind

    def get_name(self, x: int, y: int) -> str:
        """Имя типа клетки."""
        return cell_name(self.get(x, y))

    def is_passable(self, x: int, y: int) -> bool:
        """Может ли робот стоять/ехать по клетке (не STONE, не ROBOT, не PROJECTILE)."""
        kind = self.get(x, y)
        return kind not in (STONE, 6, 8)  # ROBOT=6, PROJECTILE=8

    def empty_cells(self) -> list[tuple[int, int]]:
        """Список пустых клеток (EMPTY), не на границе."""
        return [
            (x, y)
            for y in range(1, self.height - 1)
            for x in range(1, self.width - 1)
            if self.grid[y][x] == EMPTY
        ]

    def clone(self) -> "Arena":
        """Глубокая копия арены."""
        clone = Arena.__new__(Arena)
        clone.width = self.width
        clone.height = self.height
        clone.grid = [row[:] for row in self.grid]
        clone.preset = self.preset
        clone.seed = self.seed
        return clone

    def grid_string(self) -> str:
        """Сериализация сетки в строку кодов."""
        return "".join(str(c) for row in self.grid for c in row)

    @classmethod
    def from_grid_string(cls, width: int, height: int, data: str, *, preset: str = "", seed: int = 0) -> "Arena":
        """Восстанавливает арену из строки кодов."""
        grid: list[list[int]] = []
        for y in range(height):
            grid.append([int(data[y * width + x]) for x in range(width)])
        return cls.from_grid(width, height, grid, preset=preset, seed=seed)