"""Проверка порядка загрузки и диагностики циклов."""

import unittest

from src.graph import build_graph, load_order, read_graph


class OrderTests(unittest.TestCase):
    """Любая зависимость должна предшествовать своему потребителю."""

    def test_acyclic_examples(self):
        """Проверить все ребра, а не только один ожидаемый список."""
        for name in ["chain", "diamond", "single"]:
            data = read_graph(f"examples/{name}.json")
            graph = build_graph("A", data.__getitem__)
            order = load_order(graph, "A")
            self.assertEqual(set(order), set(graph))
            self.assertEqual(len(order), len(set(order)))
            for parent, children in graph.items():
                for child in children:
                    self.assertLess(order.index(child), order.index(parent))

    def test_cycle_diagnostic(self):
        """Для цикла и петли строгий топологический порядок невозможен."""
        for name, cycle in [("cycle", "A -> B -> C -> A"),
                            ("self", "A -> A")]:
            data = read_graph(f"examples/{name}.json")
            with self.assertRaisesRegex(ValueError, cycle):
                load_order(data, "A")
