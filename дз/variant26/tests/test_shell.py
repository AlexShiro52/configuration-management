import base64
import io
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.main import Shell


class ShellTests(unittest.TestCase):
    """Проверки команд, ошибок и сохранности исходного архива."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.archive = Path(self.folder.name) / "vfs.zip"
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("a/b/c/file.txt", "Привет")
            archive.writestr("my file.txt", "Текст")
            archive.writestr("binary.bin", bytes(range(256)))
            archive.writestr(".hidden", "Скрытый")
            archive.writestr("empty/", "")
        self.original = self.archive.read_bytes()
        self.shell = Shell(str(self.archive))

    def command(self, line):
        """Выполнить команду и получить ее вывод."""
        with redirect_stdout(io.StringIO()) as output:
            self.shell.execute(line)
        return output.getvalue()

    def test_quotes_and_comments(self):
        self.command('cp "my file.txt" "new file.txt" # комментарий')
        self.assertEqual(self.shell.nodes["/my file.txt"],
                         self.shell.nodes["/new file.txt"])
        self.assertIn("Ошибка", self.command('ls "'))
        self.assertEqual(self.command("# комментарий"), "")

    def test_paths(self):
        self.command("cd a/b/c")
        self.assertEqual(self.shell.cwd, "/a/b/c")
        self.assertIn("file.txt", self.command("ls"))
        self.command("cd ../../../../..")
        self.assertEqual(self.shell.cwd, "/")

    def test_hidden_and_long_listing(self):
        self.assertNotIn(".hidden", self.command("ls"))
        self.assertIn(".hidden", self.command("ls -a"))
        self.assertIn(".hidden", self.command("ls .hidden"))
        self.command('chmod 600 "my file.txt"')
        self.assertIn("600 my file.txt", self.command("ls -l"))

    def test_recursive_copy(self):
        self.command("cp -r a copy")
        self.assertEqual(self.shell.nodes["/a/b/c/file.txt"],
                         self.shell.nodes["/copy/b/c/file.txt"])
        self.command("cp -r a empty")
        self.assertIn("/empty/a/b/c/file.txt", self.shell.nodes)
        self.assertIn("Ошибка", self.command("cp -r a a/b"))

    def test_binary_and_archive_unchanged(self):
        self.command("cp binary.bin binary-copy.bin")
        data = self.shell.nodes["/binary-copy.bin"][0]
        self.assertEqual(base64.b64decode(data), bytes(range(256)))
        self.command("chmod 000 binary-copy.bin")
        self.assertEqual(self.shell.nodes["/binary-copy.bin"][1], 0)
        self.assertEqual(self.archive.read_bytes(), self.original)
        self.assertEqual(set(Path(self.folder.name).iterdir()), {self.archive})

    def test_errors_leave_state_unchanged(self):
        before = self.shell.nodes.copy()
        for command in ("cd binary.bin", "ls missing", "ls -z", "cp a copy",
                        "cp binary.bin binary.bin", "chmod 999 binary.bin",
                        "cp binary.bin missing/file", "unknown", "exit x"):
            with self.subTest(command=command):
                self.assertIn("Ошибка", self.command(command))
                self.assertEqual(self.shell.nodes, before)
        self.assertTrue(self.shell.running)

    def test_history_calendar_and_config(self):
        self.command("ls")
        self.assertIn("1 ls", self.command("history"))
        self.assertIn("vfs=", self.command("conf-dump"))
        self.assertIn("2026", self.command("cal 10 2026"))
        self.assertIn("2026", self.command("cal 2026"))
        self.assertTrue(self.command("cal"))
        self.assertIn("Ошибка", self.command("cal 13 2026"))
        self.assertIn("Ошибка", self.command("history extra"))

    def test_script_errors_and_exit(self):
        script = Path(self.folder.name) / "start.txt"
        script.write_text("# комментарий\nunknown\nls\nexit\nls\n",
                          encoding="utf-8")
        self.shell.config["script"] = str(script)
        with patch("builtins.input", side_effect=AssertionError):
            with redirect_stdout(io.StringIO()) as output:
                self.shell.run()
        self.assertIn("Ошибка", output.getvalue())
        self.assertIn(self.shell.prompt() + "ls", output.getvalue())
        self.assertEqual(self.shell.history, ["unknown", "ls", "exit"])

    def test_bad_archives(self):
        with self.assertRaises(FileNotFoundError):
            Shell(str(self.archive.parent / "missing.zip"))
        self.archive.write_text("не ZIP", encoding="utf-8")
        with self.assertRaises(zipfile.BadZipFile):
            Shell(str(self.archive))


if __name__ == "__main__":
    unittest.main()
