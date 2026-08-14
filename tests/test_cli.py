"""Тесты CLI (Фаза 0: каркас; полные — в Фазе 4)."""

from ironlogic.cli import build_parser


def test_parser_builds() -> None:
    """Парсер CLI собирается и содержит все подкоманды v1."""
    parser = build_parser()
    subparsers_action = next(
        action for action in parser._actions if action.dest == "command"  # noqa: SLF001
    )
    subcommands = set(subparsers_action.choices)
    assert subcommands == {"battle", "replay", "list-maps", "list-bots", "check"}


def test_version() -> None:
    """Пакет имеет версию."""
    from ironlogic import __version__

    assert __version__ == "0.1.0"