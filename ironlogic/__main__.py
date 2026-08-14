"""Точка входа: ``python -m ironlogic``.

Без аргументов запускается GUI (PySide6), с аргументами — CLI.
"""

import sys

from ironlogic.cli import main


def _run() -> None:
    if len(sys.argv) == 1:
        # Запуск GUI, если PySide6 доступен
        try:
            from ironlogic.app.main import run_gui
        except ImportError:
            print(
                "GUI недоступен (PySide6 не установлен). "
                "Установите зависимости: pip install -r requirements.txt"
            )
            sys.exit(1)
        run_gui()
    else:
        main()


if __name__ == "__main__":
    _run()