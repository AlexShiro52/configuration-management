"""Тестирование рекурсивного обхода и тестового репозитория."""

import json
import tempfile
import unittest
from pathlib import Path

from src.main import build_graph, read_graph


class GraphTests(unittest.TestCase):
    """Цепь, ромб, недостижимая вершина, цикл, петля и ошибки."""

    def test_dfs_and_shared_dependency(self):
        """Порядок первого посещения соответствует DFS, повторов нет."""
        data = read_graph("examples/diamond.json")
        calls = []

        def get(node):
            """Записать реальный порядок запросов."""
            calls.append(node)
            return data[node]

        graph = build_graph("A", get)
        self.assertEqual(calls, ["A", "B", "D", "C"])
        self.assertEqual(graph["C"], ["D"])
        self.assertNotIn("Z", graph)

    def test_examples(self):
        """Циклы не приводят к бесконечному обходу и не теряют ребра."""
        cases = {"chain": 3, "cycle": 3, "self": 1, "single": 1}
        for name, size in cases.items():
            with self.subTest(name=name):
                data = read_graph(f"examples/{name}.json")
                graph = build_graph("A", data.__getitem__)
                self.assertEqual(len(graph), size)
                self.assertEqual(graph, {node: data[node] for node in graph})

    def test_invalid_graph(self):
        """Поврежденные и противоречивые входные данные отклоняются."""
        cases = [[], {}, {"a": []}, {"A": "B"}, {"A": ["B"]},
                 {"A": [1]}, {"A": [[]]}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "graph.json"
            for data in cases:
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.subTest(data=data), self.assertRaises(ValueError):
                    read_graph(path)

    def test_duplicate_edges(self):
        """Повторяющиеся зависимости не дублируют ребра."""
        data = {"A": ["B", "B"], "B": []}
        self.assertEqual(build_graph("A", data.__getitem__)["A"], ["B"])
