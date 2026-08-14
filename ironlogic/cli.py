"""CLI-интерфейс IronLogic.

Подкоманды: battle, replay, list-maps, list-bots, check.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Sequence

from ironlogic import __version__
from ironlogic.botapi.errors import BotCompileError
from ironlogic.botapi.loader import load_bot
from ironlogic.engine.battle import BattleConfig, BattleRunner
from ironlogic.engine.events import battle_to_dict
from ironlogic.engine.mapgen import PRESETS

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
BOTS_DIR = Path(__file__).resolve().parent.parent / "bots"


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


def _paths_for_bots(bot_args: list[str]) -> list[Path]:
    """Разрешает имена ботов в пути (примеры/боты/относительные пути)."""
    paths: list[Path] = []
    for name in bot_args:
        p = Path(name)
        if p.exists():
            paths.append(p)
            continue
        candidates = [
            Path(name),
            Path(name) if not name.endswith(".py") else Path(name),
            Path("bots") / name,
            Path("examples") / name,
            BOTS_DIR / name,
            EXAMPLES_DIR / name,
        ]
        for cand in candidates:
            if cand.exists():
                paths.append(cand)
                break
        else:
            raise BotCompileError(f"файл робота не найден: {name}")
    return paths


def cmd_battle(args: argparse.Namespace) -> int:
    """Команда battle: запустить бой и сохранить battle.json."""
    if not (2 <= len(args.robots) <= 8):
        print("Ошибка: нужно от 2 до 8 роботов.", file=sys.stderr)
        return 1

    try:
        paths = _paths_for_bots(args.robots)
    except BotCompileError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    loaded = []
    for p in paths:
        try:
            loaded.append(load_bot(p))
        except BotCompileError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.map not in PRESETS:
        print(f"Ошибка: неизвестный пресет '{args.map}'. Доступно: {', '.join(PRESETS)}", file=sys.stderr)
        return 1

    config = BattleConfig(map_preset=args.map, seed=args.seed, max_ticks=args.ticks)
    runner = BattleRunner(config, loaded_bots=loaded)
    start = time.monotonic()
    result = runner.run()
    elapsed = time.monotonic() - start

    data = battle_to_dict(result)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    winner_name = ""
    if result.winner is not None:
        winner_name = data["robots"][result.winner]["name"]
    print(f"Карта: {args.map} (seed {args.seed}, {result.map.width}x{result.map.height})")
    print(f"Роботы: {', '.join(b['name'] for b in data['robots'])}")
    print(f"Победитель: {winner_name or '— (ничья)'}")
    print(f"Причина: {result.end_reason}")
    print(f"Такты: {result.ticks}")
    print(f"Время исполнения: {elapsed:.3f} с")
    print(f"Battle.json: {out}")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Команда replay: сводка по battle.json."""
    try:
        with open(args.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Ошибка чтения реплея: {exc}", file=sys.stderr)
        return 1

    winner = data.get("winner")
    winner_name = ""
    robots = data.get("robots", [])
    if winner is not None and winner < len(robots):
        winner_name = robots[winner].get("name", "")
    print(f"Сводка боя: {data.get('map', {}).get('preset', '?')} "
          f"(seed {data.get('map', {}).get('seed', '?')})")
    print(f"Роботы: {', '.join(r.get('name', '?') for r in robots)}")
    print(f"Победитель: {winner_name or '— (ничья)'}")
    print(f"Причина: {data.get('end_reason', '?')}")
    print(f"Такты: {data.get('ticks', '?')}")
    print(f"Событий: {len(data.get('events', []))}")
    return 0


def cmd_list_maps() -> int:
    """Команда list-maps."""
    for name in PRESETS:
        print(name)
    return 0


def cmd_list_bots(args: argparse.Namespace) -> int:
    """Команда list-bots."""
    d = Path(args.dir)
    if not d.exists():
        d = BOTS_DIR
    if not d.exists() and d != BOTS_DIR:
        print("Директория не найдена.", file=sys.stderr)
        return 1
    if not d.exists():
        d = EXAMPLES_DIR
    for p in sorted(d.glob("*.py")):
        print(p)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Команда check: проверка компиляции бота."""
    try:
        loaded = load_bot(args.path)
    except BotCompileError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {loaded.robot.name} (все слоты валидны, on_tick найдена)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа CLI. Возвращает код возврата."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "battle":
        return cmd_battle(args)
    if args.command == "replay":
        return cmd_replay(args)
    if args.command == "list-maps":
        return cmd_list_maps()
    if args.command == "list-bots":
        return cmd_list_bots(args)
    if args.command == "check":
        return cmd_check(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())