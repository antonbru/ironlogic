"""Единое окно IronLogic: выбор роботов, арена, HUD и управление в одном месте."""

from __future__ import annotations

import json
import random
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ironlogic import paths
from ironlogic.app.arena_widget import ArenaWidget
from ironlogic.app.code_editor import CodeEditor
from ironlogic.botapi.loader import load_bot
from ironlogic.config import GUI_MAP_SIZE
from ironlogic.engine.arena import Arena
from ironlogic.engine.cells import ROBOT, vector
from ironlogic.engine.mapgen import PRESETS
from ironlogic.engine.robot import RobotState

SPEED_MS = {1: 200, 4: 50, 16: 12, 0: 0}  # 0 = MAX

BOTS_DIR = paths.bots_dir()
EXAMPLES_DIR = paths.examples_dir()
TEMPLATE_BOT = paths.template_bot_path()

TEMPLATE_TEXT = TEMPLATE_BOT.read_text(encoding="utf-8") if TEMPLATE_BOT.exists() else ""


def ensure_template_bot() -> Path:
    """Создаёт bots/my_robot.py из шаблона при первом запуске (если нет файлов)."""
    BOTS_DIR.mkdir(parents=True, exist_ok=True)
    my_robot = BOTS_DIR / "my_robot.py"
    if not my_robot.exists() and TEMPLATE_TEXT:
        my_robot.write_text(TEMPLATE_TEXT, encoding="utf-8")
    return my_robot


class GameScreen(QWidget):
    """Одно окно: слева выбор карты/роботов, в центре арена, справа HUD и лог."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        ensure_template_bot()
        # Состояние воспроизведения боя
        self.events: list[dict] = []
        self.index = 0
        self.paused = True
        self.started = False
        self.speed = 1
        self.projectiles: dict[int, tuple[int, int, int]] = {}  # id -> (x, y, owner)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)
        self._build_ui()
        self.refresh_bots()

    # --- Построение интерфейса -------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        body = QHBoxLayout()
        body.addWidget(self._build_side_panel())
        self.arena_widget = ArenaWidget()
        body.addWidget(self.arena_widget, stretch=3)
        body.addWidget(self._build_info_panel())
        root.addLayout(body, stretch=1)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("▶ СТАРТ")
        self.start_btn.setStyleSheet(
            "background: #238636; color: white; font-size: 16px;"
            "padding: 8px 26px; border-radius: 8px; font-weight: bold;"
        )
        self.start_btn.clicked.connect(self.start_or_toggle)
        controls.addWidget(self.start_btn)
        for s in (1, 4, 16, 0):
            btn = QPushButton(f"×{s if s else 'MAX'}")
            btn.clicked.connect(lambda _=False, sp=s: self.set_speed(sp))
            controls.addWidget(btn)
        self.replay_btn = QPushButton("🔄 Реплей (R)")
        self.replay_btn.clicked.connect(self.restart)
        controls.addWidget(self.replay_btn)
        controls.addStretch()
        root.addLayout(controls)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(310)
        lay = QVBoxLayout(panel)

        title = QLabel("⚔️ IronLogic")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #58a6ff;")
        lay.addWidget(title)

        map_row = QHBoxLayout()
        map_row.addWidget(QLabel("Карта:"))
        self.map_combo = QComboBox()
        self.map_combo.addItems(list(PRESETS))
        map_row.addWidget(self.map_combo)
        map_row.addWidget(QLabel("Seed:"))
        self.seed_edit = QLineEdit()
        self.seed_edit.setFixedWidth(70)
        self.seed_edit.setReadOnly(True)
        self.seed_edit.setToolTip(
            "Seed последнего боя. Каждый бой начинается с нового случайного "
            "расположения; реплей сохраняется в ~/.ironlogic/battle.json"
        )
        self._randomize_seed()
        map_row.addWidget(self.seed_edit)
        lay.addLayout(map_row)

        ticks_row = QHBoxLayout()
        ticks_row.addWidget(QLabel("Макс. тактов:"))
        self.ticks_spin = QSpinBox()
        self.ticks_spin.setRange(100, 100_000)
        self.ticks_spin.setValue(10_000)
        ticks_row.addWidget(self.ticks_spin)
        ticks_row.addStretch()
        lay.addLayout(ticks_row)

        lay.addWidget(QLabel("Роботы (2–8):"))
        self.bot_list = QListWidget()
        self.bot_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        lay.addWidget(self.bot_list, stretch=2)

        row1 = QHBoxLayout()
        refresh_btn = QPushButton("🔄 обновить")
        refresh_btn.clicked.connect(self.refresh_bots)
        check_btn = QPushButton("✅ проверить")
        check_btn.clicked.connect(self.check_selected)
        edit_btn = QPushButton("✏️ Редактор")
        edit_btn.clicked.connect(self.open_editor)
        row1.addWidget(refresh_btn)
        row1.addWidget(check_btn)
        row1.addWidget(edit_btn)
        lay.addLayout(row1)

        quick_btn = QPushButton("⚡ Быстрый бой")
        quick_btn.clicked.connect(self.quick_battle)
        lay.addWidget(quick_btn)
        start_btn = QPushButton("🚀 Запустить")
        start_btn.clicked.connect(self.start_battle)
        start_btn.setStyleSheet("background: #238636; font-size: 16px; padding: 8px 20px;")
        lay.addWidget(start_btn)
        replay_btn = QPushButton("📂 Открыть реплей…")
        replay_btn.clicked.connect(self.open_replay)
        lay.addWidget(replay_btn)

        self.errors_label = QLabel("")
        self.errors_label.setWordWrap(True)
        self.errors_label.setStyleSheet("color: #f85149;")
        lay.addWidget(self.errors_label)
        lay.addStretch()
        return panel

    def _build_info_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(300)
        lay = QVBoxLayout(panel)

        header = QHBoxLayout()
        self.title_label = QLabel("Бой")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #58a6ff;")
        header.addWidget(self.title_label)
        header.addStretch()
        self.tick_label = QLabel("Такт: 0")
        self.tick_label.setStyleSheet("font-size: 15px;")
        header.addWidget(self.tick_label)
        lay.addLayout(header)

        self.hud_label = QLabel("")
        self.hud_label.setStyleSheet("color: #8b949e;")
        lay.addWidget(self.hud_label)

        lay.addWidget(QLabel("Лог боя:"))
        self.log_list = QListWidget()
        lay.addWidget(self.log_list, stretch=1)
        return panel

    # --- Выбор роботов ------------------------------------------------------
    def _randomize_seed(self) -> None:
        """Новый случайный seed — каждый бой начинается по-другому."""
        self.seed_edit.setText(str(random.randint(1, 99999)))

    def refresh_bots(self) -> None:
        self.bot_list.clear()
        all_bots = list(EXAMPLES_DIR.glob("*.py"))
        if BOTS_DIR.exists():
            all_bots += list(BOTS_DIR.glob("*.py"))
        for p in sorted(set(all_bots)):
            item = QListWidgetItem(str(p))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.bot_list.addItem(item)

        # Предвыбор: my_robot.py и wanderer.py
        found = 0
        for i in range(self.bot_list.count()):
            path = self.bot_list.item(i).text()
            if "my_robot.py" in path or "wanderer.py" in path:
                self.bot_list.item(i).setCheckState(Qt.CheckState.Checked)
                found += 1
                if found >= 2:
                    break

    def selected_bots(self) -> list[str]:
        return [
            self.bot_list.item(i).text()
            for i in range(self.bot_list.count())
            if self.bot_list.item(i).checkState() == Qt.CheckState.Checked
        ]

    def check_selected(self) -> None:
        errors = []
        for path in self.selected_bots():
            try:
                loaded = load_bot(path)
                print(f"OK: {loaded.robot.name} ← {path}")
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
        if errors:
            self.errors_label.setText("\n".join(f"❌ {e}" for e in errors))
            QMessageBox.warning(self, "Ошибки компиляции", "\n".join(errors))
        else:
            self.errors_label.setText("✅ Все выбранные роботы компилируются")

    def _collect_config(self) -> dict:
        cfg = {
            "map": self.map_combo.currentText(),
            "seed": int(self.seed_edit.text() or "42"),
            "max_ticks": self.ticks_spin.value(),
            "bots": self.selected_bots(),
        }
        # Компактная карта для боя до 2 роботов: боты быстрее встречаются.
        if len(cfg["bots"]) <= 2:
            cfg["width"] = GUI_MAP_SIZE
            cfg["height"] = GUI_MAP_SIZE
        return cfg

    def start_battle(self) -> None:
        bots = self.selected_bots()
        if not (2 <= len(bots) <= 8):
            QMessageBox.warning(self, "Нужны роботы", "Выбери от 2 до 8 роботов.")
            return
        for path in bots:
            try:
                load_bot(path)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Ошибка компиляции", str(exc))
                return
        self._randomize_seed()  # каждый бой — новое расположение
        self.load_battle(self._collect_config())

    def quick_battle(self) -> None:
        ensure_template_bot()
        self._randomize_seed()
        for i in range(self.bot_list.count()):
            self.bot_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        found = 0
        for i in range(self.bot_list.count()):
            path = self.bot_list.item(i).text()
            if "my_robot.py" in path or "wanderer.py" in path:
                self.bot_list.item(i).setCheckState(Qt.CheckState.Checked)
                found += 1
                if found >= 2:
                    break
        self.map_combo.setCurrentText("arena")
        self.load_battle(self._collect_config())

    def open_replay(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть реплей", "", "Battle JSON (*.json)")
        if path:
            self.load_battle({"replay": path})

    def open_editor(self) -> None:
        """Открывает выбранного робота (или шаблон) во встроенном редакторе."""
        selected = self.selected_bots()
        path = Path(selected[0]) if selected else ensure_template_bot()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактор: {path.name}")
        dialog.resize(720, 560)
        layout = QVBoxLayout(dialog)

        editor = CodeEditor(dialog)
        try:
            editor.setPlainText(path.read_text(encoding="utf-8"))
        except OSError as exc:
            QMessageBox.warning(self, "Не удалось открыть", str(exc))
            return

        hint = QLabel(f"Файл: {path}")
        hint.setStyleSheet("color: #8b949e;")
        layout.addWidget(hint)
        layout.addWidget(editor, stretch=1)

        buttons = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setStyleSheet("background: #238636; padding: 6px 16px;")
        cancel_btn = QPushButton("Отмена")

        def save() -> None:
            try:
                path.write_text(editor.toPlainText(), encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(dialog, "Не удалось сохранить", str(exc))
                return
            dialog.accept()
            self.refresh_bots()
            self.errors_label.setText(f"✅ Сохранено: {path}")

        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

        dialog.exec()

    # --- Загрузка боя ------------------------------------------------------
    def load_battle(self, config: dict) -> None:
        """Запускает бой: либо из конфига (генерирует battle.json), либо из реплея."""
        if "replay" in config:
            with open(config["replay"], "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._setup(data)
            self.setFocus()
            return

        # Полный бой headless заранее
        from ironlogic.engine.battle import BattleConfig, BattleRunner
        from ironlogic.engine.events import battle_to_dict

        loaded = [load_bot(p) for p in config["bots"]]
        battle_config = BattleConfig(
            map_preset=config["map"],
            seed=config["seed"],
            max_ticks=config["max_ticks"],
            width=config.get("width"),
            height=config.get("height"),
        )
        runner = BattleRunner(battle_config, loaded_bots=loaded)
        result = runner.run()
        self._setup(battle_to_dict(result))

        # Сохраняем реплей в каталог пользователя (в бандле cwd может быть read-only)
        out = paths.user_dir() / "battle.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(battle_to_dict(result), fh, ensure_ascii=False, indent=2)
        self.setFocus()

    def _setup(self, data: dict) -> None:
        """Восстанавливает состояние по событиям."""
        self.map_data = data["map"]
        self.robots_data = data["robots"]
        self.events = data.get("events", [])
        self.index = 0
        self.paused = True
        self.started = False
        self.speed = 1
        self.projectiles.clear()
        self._make_arena()
        self.title_label.setText("Бой")
        self.tick_label.setText("Такт: 0")
        self.log_list.clear()
        self.timer.setInterval(SPEED_MS[1])
        self._apply_spawns()
        self._render()
        self._update_start_btn()

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
    def _update_start_btn(self) -> None:
        """Текст и стиль кнопки старта по текущему состоянию."""
        if not self.started:
            label = "▶ Заново (R)" if self.index >= len(self.events) else "▶ СТАРТ"
            self.start_btn.setText(label)
            self.start_btn.setStyleSheet(
                "background: #238636; color: white; font-size: 16px;"
                "padding: 8px 26px; border-radius: 8px; font-weight: bold;"
            )
        else:
            self.start_btn.setText("▶ Продолжить" if self.paused else "⏸ Пауза")
            self.start_btn.setStyleSheet("")

    def start_or_toggle(self) -> None:
        """СТАРТ, а затем пауза/продолжение."""
        if not self.started:
            if self.index >= len(self.events):
                self.restart()
            self.started = True
            self.paused = False
            self.timer.start(SPEED_MS[self.speed])
        else:
            self.toggle_pause()
        self._update_start_btn()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start(SPEED_MS[self.speed])
        self._update_start_btn()

    def set_speed(self, speed: int) -> None:
        self.speed = speed
        if self.started and not self.paused:
            self.timer.start(SPEED_MS[speed])

    def restart(self) -> None:
        self.timer.stop()
        if hasattr(self, "map_data"):
            self._setup({
                "map": self.map_data,
                "robots": self.robots_data,
                "events": self.events,
            })

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.start_or_toggle()
        elif key == Qt.Key.Key_R:
            self.restart()
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
            self.started = False
            self._update_start_btn()
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
                robot.energy += 5
        elif t == "shutdown":
            robot = self._robot(event.get("robot"))
            if robot:
                robot.shutdown = True
        elif t == "explosion":
            self.log_list.addItem(f"[t{event.get('t')}] 💥 Взрыв {event.get('x')},{event.get('y')} урон {event.get('damage')}")
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
