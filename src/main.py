"""Точка входа: python3 -m src.main."""

from .config import arguments


def main(argv=None):
    """Вывести проверенные настройки минимального прототипа."""
    args = arguments(argv)
    for key, value in vars(args).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
