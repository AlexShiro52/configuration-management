"""Проверка настроек без сети и внешних программ."""

import contextlib
import io
import unittest

from src.config import arguments


class ConfigTests(unittest.TestCase):
    """Корректные значения и ошибки каждого параметра."""

    def test_defaults(self):
        """Значения по умолчанию пригодны для реального репозитория."""
        args = arguments(["--package", "requests"])
        self.assertEqual(args.output, "graph.png")
        self.assertFalse(args.test)

    def test_invalid_options(self):
        """Ошибочные значения завершаются кодом 2, без traceback."""
        cases = [[], ["--package", "bad/name"], ["--package", ""],
                 ["--repository", "file:///tmp/a"],
                 ["--repository", "https://pypi.org:bad"],
                 ["--repository", "https://pypi.org/?q=a"],
                 ["--test", "false"], ["--test"],
                 ["--output", "graph.svg"],
                 ["--output", "missing-directory/graph.png"],
                 ["--stage", "0"], ["--stage", "abc"]]
        for options in cases:
            argv = ["--package", "requests"] + options if options else []
            with self.subTest(options=options):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        arguments(argv)
                self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
