"""QPainter-отрисовка арены, роботов и снарядов."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ironlogic.engine.cells import AMMO, EMPTY, PIT, REACTOR, RECHARGE, STONE

CELL_COLORS: dict[int, QColor] = {
    EMPTY: QColor("#161b22"),
    STONE: QColor("#484f58"),
    PIT: QColor("#000000"),
    REACTOR: QColor("#ff4500"),
    AMMO: QColor("#ffd700"),
    RECHARGE: QColor("#2ea043"),
}

ROBOT_COLORS = [
    QColor("#ff5555"),
    QColor("#55aaff"),
    QColor("#50fa7b"),
    QColor("#ffb86c"),
    QColor("#bd93f9"),
    QColor("#f1fa8c"),
    QColor("#ff79c6"),
    QColor("#8be9fd"),
]


class ArenaWidget(QWidget):
    """Виджет арены: отрисовывает сетку, роботов, снаряды."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.arena = None
        self.robots: list = []
        self.projectiles: list = []
        self.damage_flash: dict[int, int] = {}
        self._cell = 24

    def set_state(self, arena, robots, projectiles, damage_flash=None) -> None:
        self.arena = arena
        self.robots = robots or []
        self.projectiles = projectiles or []
        if damage_flash is not None:
            self.damage_flash = damage_flash
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.arena is None:
            painter.fillRect(self.rect(), QColor("#0d1117"))
            painter.setPen(QColor("#8b949e"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Бой не запущен")
            return

        width = self.arena.width
        height = self.arena.height
        self._cell = max(12, min(self.width() // width, self.height() // height))
        origin_x = (self.width() - width * self._cell) // 2
        origin_y = (self.height() - height * self._cell) // 2

        for y in range(height):
            for x in range(width):
                kind = self.arena.get(x, y)
                color = CELL_COLORS.get(kind, QColor("#161b22"))
                painter.fillRect(
                    origin_x + x * self._cell, origin_y + y * self._cell,
                    self._cell, self._cell, color,
                )

        for i, robot in enumerate(self.robots):
            if not getattr(robot, "alive", True):
                continue
            color = ROBOT_COLORS[i % len(ROBOT_COLORS)]
            if getattr(robot, "shutdown", False):
                color = QColor("#6e7681")
            if self.damage_flash.get(robot.id, 0) > 0:
                color = QColor("#ffffff")
            self._draw_robot(painter, robot.x, robot.y, robot.dir, color, origin_x, origin_y)

        pen = QPen(QColor("#ffe66d"), 2)
        painter.setPen(pen)
        painter.setBrush(QColor("#ffe66d"))
        for proj in self.projectiles:
            cx = origin_x + proj.x * self._cell + self._cell / 2
            cy = origin_y + proj.y * self._cell + self._cell / 2
            painter.drawEllipse(QRectF(cx - 3, cy - 3, 6, 6))

    def _draw_robot(self, painter, x, y, direction, color, ox, oy) -> None:
        c = self._cell
        rect = QRectF(ox + x * c + 2, oy + y * c + 2, c - 4, c - 4)
        painter.setPen(QPen(color, 2))
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), 160))
        painter.drawRoundedRect(rect, 4, 4)

        cx = rect.center().x()
        cy = rect.center().y()
        r = c * 0.3
        pts: list[QPointF] = []
        if direction == "N":
            pts = [QPointF(cx, cy - r), QPointF(cx - r * 0.6, cy + r * 0.6), QPointF(cx + r * 0.6, cy + r * 0.6)]
        elif direction == "E":
            pts = [QPointF(cx + r, cy), QPointF(cx - r * 0.6, cy - r * 0.6), QPointF(cx - r * 0.6, cy + r * 0.6)]
        elif direction == "S":
            pts = [QPointF(cx, cy + r), QPointF(cx - r * 0.6, cy - r * 0.6), QPointF(cx + r * 0.6, cy - r * 0.6)]
        elif direction == "W":
            pts = [QPointF(cx - r, cy), QPointF(cx + r * 0.6, cy - r * 0.6), QPointF(cx + r * 0.6, cy + r * 0.6)]
        if pts:
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(pts)