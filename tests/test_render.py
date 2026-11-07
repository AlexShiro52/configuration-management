"""Проверка D2 и ошибок рендеринга без установленного D2."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.render import PNG_SIGNATURE, render, to_d2


class RenderTests(unittest.TestCase):
    """Описание сохраняет все вершины и ребра, ошибки не скрываются."""

    def test_d2_cycle_and_leaf(self):
        """Результат включает петлю, обычное ребро и изолированную вершину."""
        text = to_d2({"A": ["A", "B"], "B": [], "C": []})
        self.assertIn('n2: "C"', text)
        self.assertIn("n0 -> n0", text)
        self.assertIn("n0 -> n1", text)

    def test_missing_d2(self):
        """При отсутствии D2 остается текст, ложного PNG нет."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.png"
            with patch("src.render.shutil.which", return_value=None):
                with self.assertRaisesRegex(ValueError, "D2 не найден"):
                    render({"A": []}, path)
            self.assertTrue(path.with_suffix(".d2").exists())
            self.assertFalse(path.exists())

    def test_renderer_errors(self):
        """Сбой, тайм-аут и отсутствие PNG завершаются понятной ошибкой."""
        cases = [SimpleNamespace(returncode=1, stderr="broken"),
                 SimpleNamespace(returncode=0, stderr=""),
                 subprocess.TimeoutExpired("d2", 120)]
        with tempfile.TemporaryDirectory() as folder:
            for result in cases:
                kwargs = {"side_effect" if isinstance(result, Exception)
                          else "return_value": result}
                with patch("src.render.shutil.which", return_value="d2"):
                    with patch("src.render.subprocess.run", **kwargs):
                        with self.assertRaises(ValueError):
                            render({"A": []}, Path(folder) / "out.png")

    def test_success_and_invalid_png(self):
        """Выход заменяется только после успешной проверки сигнатуры."""
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "out.png"
            for content in [b"not png", PNG_SIGNATURE + b"test"]:
                output.write_bytes(b"old")

                def fake_run(command, **kwargs):
                    """Имитировать файл, созданный процессом D2."""
                    Path(command[-1]).write_bytes(content)
                    return SimpleNamespace(returncode=0, stderr="")

                with patch("src.render.shutil.which", return_value="d2"):
                    with patch("src.render.subprocess.run", fake_run):
                        if content.startswith(PNG_SIGNATURE):
                            render({"A": []}, output)
                            self.assertEqual(output.read_bytes(), content)
                        else:
                            with self.assertRaises(ValueError):
                                render({"A": []}, output)
                            self.assertEqual(output.read_bytes(), b"old")
