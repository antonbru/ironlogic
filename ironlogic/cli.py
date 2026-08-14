"""CLI-интерфейс IronLogic.

Подкоманды (v1): battle, replay, list-maps, list-bots, check.
В Фазе 0 реализованы каркас argparse и help; полная логика — в Фазе 4.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from ironlogic import __version__


def build_parser() -> argparse.ArgumentParser:
    """Собирает парсер аргументов CLI."""
    parser = argparse.ArgumentParser(
        prog="ironlogic",
        description="IronLogic — битва программируемых роботов. "
                    "Побеждает не железо — побеждает логика.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")

    # battle
    p_battle = sub.add_parser("battle", help="запустить бой headless и записать battle.json")
    p_battle.add_argument("--map", default="arena", help="пресет карты (по умолчанию: arena)")
    p_battle.add_argument("--seed", type=int, default=42, help="seed генератора карты")
    p_battle.add_argument("--ticks", type=int, default=10_000, help="максимум тактов")
    p_battle.add_argument("--robots", nargs="+", required=True, help="файлы .py роботов (2-8)")
    p_battle.add_argument("--out", default="battle.json", help="путь для battle.json")

    # replay
    p_replay = sub.add_parser("replay", help="прочитать battle.json и напечатать сводку")
    p_replay.add_argument("path", help="путь к battle.json")

    # list-maps
    sub.add_parser("list-maps", help="список пресетов карт")

    # list-bots
    p_bots = sub.add_parser("list-bots", help="список .py файлов роботов")
    p_bots.add_argument("--dir", default="bots", help="директория для поиска")

    # check
    p_check = sub.add_parser("check", help="проверить компиляцию бота и вывести ошибки")
    p_check.add_argument("path", help="файл .py робота")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа CLI. Возвращает код возврата."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    # Реализация подкоманд добавляется в Фазе 4.
    print(f"[ironlogic {__version__}] команда '{args.command}' будет реализована в Фазе 4")
    return 0


if __name__ == "__main__":
    sys.exit(main())