"""Лаунчер: выбор карты, роботов и запуск боя."""

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
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

from ironlogic.botapi.loader import load_bot
from ironlogic.engine.mapgen import PRESETS

ROOT = Path(__file__).resolve().parent.parent
BOTS_DIR = ROOT / "bots"
EXAMPLES_DIR = ROOT / "examples"
TEMPLATE_BOT = ROOT / "template_bot.py"

TEMPLATE_TEXT = TEMPLATE_BOT.read_text(encoding="utf-8") if TEMPLATE_BOT.exists() else ""


def ensure_template_bot() -> Path:
    """Создаёт bots/my_robot.py из шаблона при первом запуске (если нет файлов)."""
    BOTS_DIR.mkdir(parents=True, exist_ok=True)
    my_robot = BOTS_DIR / "my_robot.py"
    if not my_robot.exists() and TEMPLATE_TEXT:
        my_robot.write_text(TEMPLATE_TEXT, encoding="utf-8")
    return my_robot


class LauncherWidget(QWidget):
    """Экран выбора карты и роботов."""

    battle_requested = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        ensure_template_bot()
        self._build_ui()
        self.refresh_bots()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("⚔️ IronLogic — Битва интеллектов")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(title)

        subtitle = QLabel("Выбери карту, отметь роботов и запусти бой. Побеждает лучший код!")
        subtitle.setStyleSheet("color: #8b949e;")
        layout.addWidget(subtitle)

        # Карта
        map_row = QHBoxLayout()
        map_row.addWidget(QLabel("Карта:"))
        self.map_combo = QComboBox()
        self.map_combo.addItems(list(PRESETS))
        map_row.addWidget(self.map_combo)
        map_row.addWidget(QLabel("Seed:"))
        self.seed_edit = QLineEdit("42")
        self.seed_edit.setFixedWidth(70)
        map_row.addWidget(self.seed_edit)
        dice = QPushButton("🎲")
        dice.setFixedWidth(40)
        dice.clicked.connect(lambda: self.seed_edit.setText(str(random.randint(0, 9999))))
        map_row.addWidget(dice)
        map_row.addStretch()
        layout.addLayout(map_row)

        # Роботы
        layout.addWidget(QLabel("Роботы (выбери от 2 до 8):"))
        self.bot_list = QListWidget()
        self.bot_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        layout.addWidget(self.bot_list, stretch=2)

        bots_row = QHBoxLayout()
        refresh_btn = QPushButton("🔄 обновить список")
        refresh_btn.clicked.connect(self.refresh_bots)
        self.check_btn = QPushButton("✅ проверить")
        self.check_btn.clicked.connect(self.check_selected)
        bots_row.addWidget(refresh_btn)
        bots_row.addWidget(self.check_btn)
        bots_row.addStretch()
        layout.addLayout(bots_row)

        # Настройки
        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel("Макс. тактов:"))
        self.ticks_spin = QSpinBox()
        self.ticks_spin.setRange(100, 100_000)
        self.ticks_spin.setValue(10_000)
        settings_row.addWidget(self.ticks_spin)
        settings_row.addStretch()
        layout.addLayout(settings_row)

        # Кнопки
        buttons = QHBoxLayout()
        quick = QPushButton("⚡ Быстрый бой")
        quick.clicked.connect(self.quick_battle)
        start = QPushButton("🚀 Запустить")
        start.clicked.connect(self.start_battle)
        start.setStyleSheet("background: #238636; font-size: 16px; padding: 8px 20px;")
        replay = QPushButton("📂 Открыть реплей…")
        replay.clicked.connect(self.open_replay)
        buttons.addWidget(quick)
        buttons.addWidget(start)
        buttons.addWidget(replay)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.errors_label = QLabel("")
        self.errors_label.setWordWrap(True)
        self.errors_label.setStyleSheet("color: #f85149;")
        layout.addWidget(self.errors_label)

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

    def _collect_config(self) -> dict:
        return {
            "map": self.map_combo.currentText(),
            "seed": int(self.seed_edit.text() or "42"),
            "max_ticks": self.ticks_spin.value(),
            "bots": self.selected_bots(),
        }

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
        self.battle_requested.emit(self._collect_config())

    def quick_battle(self) -> None:
        ensure_template_bot()
        # Сбрасываем выбор и включаем my_robot + wanderer
        for i in range(self.bot_list.count()):
            self.bot_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        for i in range(self.bot_list.count()):
            path = self.bot_list.item(i).text()
            if "my_robot.py" in path or "wanderer.py" in path:
                self.bot_list.item(i).setCheckState(Qt.CheckState.Checked)
        self.map_combo.setCurrentText("arena")
        self.battle_requested.emit(self._collect_config())

    def open_replay(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть реплей", "", "Battle JSON (*.json)")
        if path:
            self.battle_requested.emit({"replay": path})