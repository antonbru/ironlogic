"""Главное окно GUI IronLogic: тёмная неоновая тема, лаунчер ↔ бой."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from ironlogic.app.launcher import LauncherWidget
from ironlogic.app.battle_screen import BattleScreen

DARK_QSS = """
QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif;
    font-size: 14px;
}
QLabel { color: #c9d1d9; }
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 6px 14px;
}
QPushButton:hover { background-color: #30363d; border-color: #58a6ff; }
QPushButton:pressed { background-color: #21262d; }
QComboBox, QLineEdit, QSpinBox, QListWidget {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px 8px;
}
QListWidget::item:selected { background-color: #1f6feb; }
QScrollBar:vertical { background: #161b22; width: 10px; }
QScrollBar::handle:vertical { background: #30363d; border-radius: 5px; min-height: 20px; }
"""

QSS_ACCENTS = {
    "title": "font-size: 26px; font-weight: bold; color: #58a6ff;",
}


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IronLogic — Железная Логика")
        self.resize(1280, 800)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.launcher = LauncherWidget()
        self.battle_screen = BattleScreen()

        self.stack.addWidget(self.launcher)
        self.stack.addWidget(self.battle_screen)

        self.launcher.battle_requested.connect(self.start_battle)
        self.battle_screen.back_requested.connect(self.go_launcher)

        self.stack.setCurrentWidget(self.launcher)

    def start_battle(self, config: dict) -> None:
        self.stack.setCurrentWidget(self.battle_screen)
        self.battle_screen.load_battle(config)
        self.battle_screen.setFocus()

    def go_launcher(self) -> None:
        self.battle_screen.timer.stop()
        self.stack.setCurrentWidget(self.launcher)


def run_gui() -> None:
    """Запускает GUI-приложение."""
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()