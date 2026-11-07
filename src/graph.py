"""Рекурсивный DFS и тестовый репозиторий."""

import json
import re
from pathlib import Path


def read_graph(path):
    """Прочитать JSON-граф и проверить имена, списки и ссылки."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("Тестовый граф должен быть непустым JSON-объектом")
    for name, children in data.items():
        if not re.fullmatch(r"[A-Z]+", name):
            raise ValueError(f"Имя {name!r}: нужны большие латинские буквы")
        if not isinstance(children, list):
            raise ValueError(f"Зависимости {name} должны быть списком")
        for child in children:
            if not isinstance(child, str) or child not in data:
                raise ValueError(f"Неизвестная зависимость {name}: {child!r}")
        data[name] = list(dict.fromkeys(children))
    return data


def build_graph(root, get_dependencies):
    """Обойти достижимые вершины рекурсивным DFS, сохранив циклы."""
    graph = {}

    def visit(node):
        """Зарегистрировать вершину до рекурсивного обхода ее соседей."""
        if node in graph:
            return
        graph[node] = list(dict.fromkeys(get_dependencies(node)))
        for child in graph[node]:
            visit(child)

    visit(root)
    return graph


def load_order(graph, root):
    """Вернуть зависимости раньше потребителей; при цикле сообщить его путь."""
    done, active, order, path = set(), set(), [], []

    def visit(node):
        """Добавить вершину в результат после обхода всех зависимостей."""
        if node in active:
            cycle = path[path.index(node):] + [node]
            raise ValueError("Нет порядка загрузки: цикл " + " -> ".join(cycle))
        if node in done:
            return
        active.add(node)
        path.append(node)
        for child in graph[node]:
            visit(child)
        path.pop()
        active.remove(node)
        done.add(node)
        order.append(node)

    visit(root)
    return order
