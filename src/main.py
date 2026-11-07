"""Точка входа: python3 -m src.main."""

import sys

from .config import arguments
from .repository import dependencies, normalize


def main(argv=None):
    """Запустить выбранный этап, сообщив об ошибке без traceback."""
    args = arguments(argv)
    try:
        run(args)
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


def run(args):
    """Вывести настройки либо список прямых зависимостей."""
    if args.stage == 1:
        for key, value in vars(args).items():
            print(f"{key}={value}")
        return
    if args.test:
        raise ValueError("Тестовый источник будет добавлен на этапе 3")
    names = dependencies(args.repository, normalize(args.package))
    print("\n".join(names) or "Нет прямых зависимостей")


if __name__ == "__main__":
    raise SystemExit(main())
