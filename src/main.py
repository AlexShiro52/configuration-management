"""Точка входа: python3 -m src.main."""

import json
import sys

from .config import arguments
from .graph import build_graph, load_order, read_graph
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
    """Выполнить этап 1, 2 или построение графа рекурсивным DFS."""
    if args.stage == 1:
        for key, value in vars(args).items():
            print(f"{key}={value}")
        return
    root, get_dependencies = source(args)
    if args.stage == 2:
        print("\n".join(get_dependencies(root)) or "Нет прямых зависимостей")
        return
    graph = build_graph(root, get_dependencies)
    if args.stage == 4:
        print(" -> ".join(load_order(graph, root)))
        return
    print(json.dumps(graph, ensure_ascii=False, indent=2))


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
