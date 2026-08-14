"""Точка входа GUI IronLogic (PySide6).

Полноценный лаунчер, арена и HUD — Фаза 5. В Фазе 0 здесь только
минимальное окно-заглушка, чтобы `python -m ironlogic` запускался.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    """Главное окно приложения (заглушка Фазы 0)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IronLogic")
        self.resize(1024, 768)
        self.setCentralWidget(
            QLabel(
                "IronLogic — битва программируемых роботов.\n"
                "Полный GUI появится в Фазе 5."
            )
        )


def run_gui() -> None:
    """Запускает GUI-приложение."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())