"""Проверка взаимодействия этапов через основную точку входа."""

import contextlib
import io
import json
import unittest
from unittest.mock import patch

from src.main import main


class CliTests(unittest.TestCase):
    """Каждый этап выдает свой результат и корректный код завершения."""

    def call(self, stage, example="diamond", package="A"):
        """Запустить программу с тестовым репозиторием и захватить вывод."""
        stdout, stderr = io.StringIO(), io.StringIO()
        args = ["--package", package, "--test", "--repository",
                f"examples/{example}.json", "--stage", str(stage)]
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_settings(self):
        """Этап 1 выводит все настройки в формате ключ-значение."""
        code, output, error = self.call(1)
        values = dict(line.split("=", 1) for line in output.splitlines())
        self.assertEqual(code, 0)
        self.assertEqual(values["package"], "A")
        self.assertEqual(values["test"], "True")
        self.assertEqual(len(values), 5)
        self.assertFalse(error)

    def test_direct_and_transitive(self):
        """Этап 2 выводит только соседей, этап 3 включает транзитивность."""
        self.assertEqual(self.call(2)[:2], (0, "B\nC\n"))
        code, output, _ = self.call(3)
        self.assertEqual(code, 0)
        self.assertIn("D", json.loads(output))
        self.assertNotIn("Z", json.loads(output))

    def test_order(self):
        """Этап 4 дает постпорядок DFS и не печатает настройки."""
        self.assertEqual(self.call(4)[:2], (0, "D -> B -> C -> A\n"))

    def test_graphics_stage(self):
        """Этап 5 передает полный граф рендереру."""
        with patch("src.main.render", return_value="graph.d2") as render:
            code, output, error = self.call(5)
        self.assertEqual(code, 0)
        self.assertIn("PNG: graph.png", output)
        self.assertEqual(len(render.call_args.args[0]), 4)
        self.assertFalse(error)

    def test_missing_package_and_cycle(self):
        """Содержательные ошибки обрабатываются без трассировки стека."""
        for stage, example, package in [(3, "single", "B"),
                                        (4, "cycle", "A")]:
            code, output, error = self.call(stage, example, package)
            self.assertEqual(code, 1)
            self.assertFalse(output)
            self.assertIn("Ошибка:", error)
            self.assertNotIn("Traceback", error)
