"""Экран боя: воспроизведение событий с анимацией, паузой и скоростью."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ironlogic.engine.arena import Arena
from ironlogic.engine.cells import ROBOT, vector
from ironlogic.engine.robot import RobotState

from ironlogic.app.arena_widget import ArenaWidget

SPEED_MS = {1: 200, 4: 50, 16: 12, 0: 0}  # 0 = MAX


class BattleScreen(QWidget):
    """Воспроизводит battle.json (события) с анимацией."""

    back_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.events: list[dict] = []
        self.index = 0
        self.paused = False
        self.speed = 1
        self.projectiles: dict[int, tuple[int, int, int]] = {}  # id -> (x, y, owner)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        header = QHBoxLayout()
        self.title_label = QLabel("Бой")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #58a6ff;")
        header.addWidget(self.title_label)
        header.addStretch()
        self.tick_label = QLabel("Такт: 0")
        self.tick_label.setStyleSheet("font-size: 16px;")
        header.addWidget(self.tick_label)
        root.addLayout(header)

        body = QHBoxLayout()
        self.arena_widget = ArenaWidget()
        body.addWidget(self.arena_widget, stretch=3)

        right = QVBoxLayout()
        self.hud_label = QLabel("")
        self.hud_label.setStyleSheet("color: #8b949e;")
        right.addWidget(self.hud_label)

        self.log_list = QListWidget()
        right.addWidget(self.log_list, stretch=1)
        body.addLayout(right, stretch=1)
        root.addLayout(body, stretch=1)

        buttons = QHBoxLayout()
        self.pause_btn = QPushButton("⏸ Пауза (Space)")
        self.pause_btn.clicked.connect(self.toggle_pause)
        buttons.addWidget(self.pause_btn)
        for s in (1, 4, 16, 0):
            btn = QPushButton(f"×{s if s else 'MAX'}")
            btn.clicked.connect(lambda _=False, sp=s: self.set_speed(sp))
            buttons.addWidget(btn)
        self.replay_btn = QPushButton("🔄 Реплей (R)")
        self.replay_btn.clicked.connect(self.restart)
        buttons.addWidget(self.replay_btn)
        back = QPushButton("◀ В лаунчер (Esc)")
        back.clicked.connect(self.back_requested.emit)
        buttons.addWidget(back)
        buttons.addStretch()
        root.addLayout(buttons)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # --- Загрузка ----------------------------------------------------------
    def load_battle(self, config: dict) -> None:
        """Запускает бой: либо из конфига (генерирует battle.json), либо из реплея."""
        if "replay" in config:
            with open(config["replay"], "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._setup(data)
            self.timer.start(SPEED_MS[self.speed])
            return

        # Полный бой headless заранее
        from ironlogic.botapi.loader import load_bot
        from ironlogic.engine.battle import BattleConfig, BattleRunner
        from ironlogic.engine.events import battle_to_dict

        loaded = [load_bot(p) for p in config["bots"]]
        battle_config = BattleConfig(
            map_preset=config["map"], seed=config["seed"], max_ticks=config["max_ticks"]
        )
        runner = BattleRunner(battle_config, loaded_bots=loaded)
        result = runner.run()
        self._setup(battle_to_dict(result))

        # Сохраняем реплей рядом
        out = Path("battle.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(battle_to_dict(result), fh, ensure_ascii=False, indent=2)
        self.timer.start(SPEED_MS[self.speed])

    def _setup(self, data: dict) -> None:
        """Восстанавливает состояние по событиям."""
        self.map_data = data["map"]
        self.robots_data = data["robots"]
        self.events = data.get("events", [])
        self.index = 0
        self.paused = False
        self.speed = 1
        self._make_arena()
        self.tick_label.setText("Такт: 0")
        self.log_list.clear()
        self.timer.setInterval(SPEED_MS[1])
        self._apply_spawns()
        self._render()

    def _make_arena(self) -> None:
        w = self.map_data["width"]
        h = self.map_data["height"]
        self.arena = Arena.from_grid_string(
            w, h, self.map_data["grid"], preset=self.map_data.get("preset", ""),
            seed=self.map_data.get("seed", 0),
        )

    def _apply_spawns(self) -> None:
        self.robots: list[RobotState] = []
        for i, rdata in enumerate(self.robots_data):
            robot = RobotState(
                id=i,
                name=rdata["name"],
                file=rdata.get("file", ""),
                x=rdata["x"],
                y=rdata["y"],
                dir=rdata["dir"],
                hardware=dict(rdata.get("hardware", {})),
                radar=bool(rdata.get("radar", False)),
            )
            self.robots.append(robot)
            self.arena.set(robot.x, robot.y, ROBOT)

    # --- Управление --------------------------------------------------------
    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_btn.setText("▶ Продолжить (Space)" if self.paused else "⏸ Пауза (Space)")
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start(SPEED_MS[self.speed])

    def set_speed(self, speed: int) -> None:
        self.speed = speed
        if not self.paused:
            self.timer.start(SPEED_MS[speed])

    def restart(self) -> None:
        self._setup(self._battle_data() if hasattr(self, "map_data") else {"map": self.map_data, "robots": self.robots_data, "events": self.events})

    def _battle_data(self) -> dict:
        return {
            "map": self.map_data,
            "robots": self.robots_data,
            "events": self.events,
            "winner": None,
            "end_reason": "",
            "ticks": 0,
        }

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.toggle_pause()
        elif key == Qt.Key.Key_R:
            self.restart()
        elif key == Qt.Key.Key_Escape:
            self.back_requested.emit()
        elif key == Qt.Key.Key_1:
            self.set_speed(1)
        elif key == Qt.Key.Key_2:
            self.set_speed(4)
        elif key == Qt.Key.Key_3:
            self.set_speed(16)
        elif key == Qt.Key.Key_4:
            self.set_speed(0)
        else:
            super().keyPressEvent(event)

    # --- Воспроизведение ---------------------------------------------------
    def _advance(self) -> None:
        if self.index >= len(self.events):
            self.timer.stop()
            self.paused = True
            return
        event = self.events[self.index]
        self._apply_event(event)
        self.index += 1
        self.tick_label.setText(f"Такт: {event.get('t', 0) + 1}")
        self._render()

    def _apply_event(self, event: dict) -> None:
        t = event["type"]
        if t == "spawn":
            for robot in self.robots:
                if robot.id == event.get("robot"):
                    robot.x, robot.y = event["x"], event["y"]
                    robot.dir = event.get("dir", robot.dir)
                    self.arena.set(robot.x, robot.y, ROBOT)
        elif t == "move":
            robot = self._robot(event.get("robot"))
            if robot:
                self.arena.set(robot.x, robot.y, 0)
                robot.x, robot.y = event["to"]
                self.arena.set(robot.x, robot.y, ROBOT)
        elif t == "turn":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.dir = event["dir"]
        elif t == "shoot":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.ammo = max(0, robot.ammo - 1)
                dx, dy = vector(event.get("dir", robot.dir))
                self.projectiles[event["projectile"]] = (robot.x + dx, robot.y + dy, robot.id)
        elif t == "projectile_move":
            pid = event.get("projectile")
            if pid in self.projectiles:
                x, y = event["to"]
                owner = self.projectiles[pid][2]
                self.projectiles[pid] = (x, y, owner)
        elif t == "miss":
            self.projectiles.pop(event.get("projectile"), None)
        elif t == "hit":
            robot = self._robot(event.get("target"))
            if robot:
                robot.health = event.get("health", robot.health)
                self.arena_widget.damage_flash[robot.id] = 3
                # Снаряд погиб, попав в робота на его клетке.
                for pid in list(self.projectiles):
                    if (self.projectiles[pid][0], self.projectiles[pid][1]) == (robot.x, robot.y):
                        del self.projectiles[pid]
                        break
        elif t == "destroyed":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.alive = False
                self.arena.set(robot.x, robot.y, 0)
            self.projectiles = {pid: p for pid, p in self.projectiles.items() if p[2] != event.get("robot")}
        elif t == "ammo_pickup":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.ammo = event.get("ammo", robot.ammo)
        elif t == "recharge":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.energy = min(100, robot.energy + 5)
        elif t == "shutdown":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.shutdown = True
        elif t == "explosion":
            self.log_list.addItem(f"[t{event.get('t')}] 💥 Взрыв {event.get('x')},{event.get('y')} урон {event.get('damage')}")
        elif t == "destroyed":
            pass
        elif t == "script_log":
            self.log_list.addItem(f"[{event.get('robot')}] {event.get('message', '')}")
        elif t == "end":
            reason = event.get("reason", "")
            winner = self._robot(event.get("winner")) if event.get("winner") is not None else None
            winner_name = winner.name if winner else "Ничья"
            self.title_label.setText(f"🏁 Победитель: {winner_name} ({reason})")

        # Уменьшаем вспышки
        self.arena_widget.damage_flash = {k: v - 1 for k, v in self.arena_widget.damage_flash.items() if v > 1}

    def _robot(self, robot_id):
        if robot_id is None:
            return None
        for robot in self.robots:
            if robot.id == robot_id:
                return robot
        return None

    def _render(self) -> None:
        projectiles = [type("P", (), {"x": x, "y": y})() for (x, y, _) in self.projectiles.values()]
        self.arena_widget.set_state(self.arena, self.robots, projectiles, self.arena_widget.damage_flash)
        hud_lines = []
        for robot in self.robots:
            status = "💀" if not robot.alive else ("🔌" if robot.shutdown else "🟢")
            hud_lines.append(f"{status} {robot.name}: ❤{robot.health} ⚡{robot.energy} 🔫{robot.ammo} ({robot.x},{robot.y})")
        self.hud_label.setText("\n".join(hud_lines))