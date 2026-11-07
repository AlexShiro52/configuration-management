"""Точка входа: python3 -m src.main."""

import json
import sys

from .config import arguments
from .graph import build_graph, load_order, read_graph
from .repository import dependencies, normalize
from .render import render


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
    """Выполнить выбранный этап: настройки, данные, DFS, порядок или PNG."""
    if args.stage == 1:
        for key, value in vars(args).items():
            print(f"{key}={value}")
        return
    root, get_dependencies = source(args)
    if args.stage == 2:
        print("\n".join(get_dependencies(root)) or "Нет прямых зависимостей")
        return
    graph = build_graph(root, get_dependencies)
    if args.stage == 3:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
        return
    if args.stage == 4:
        print(" -> ".join(load_order(graph, root)))
        return
    description = render(graph, args.output)
    print(f"D2: {description}\nPNG: {args.output}")


def source(args):
    """Выбрать независимый от DFS источник прямых зависимостей."""
    if args.test:
        graph = read_graph(args.repository)
        if args.package not in graph:
            raise ValueError(f"Пакет {args.package} отсутствует в репозитории")
        return args.package, graph.__getitem__
    return normalize(args.package), lambda name: dependencies(
        args.repository, name)


if __name__ == "__main__":
    raise SystemExit(main())
