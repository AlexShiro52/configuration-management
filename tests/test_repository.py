"""Тесты HTTP-метаданных и условий зависимостей без реальной сети."""

import io
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.main import enabled
from src.main import dependencies, metadata, normalize, package_name


class RepositoryTests(unittest.TestCase):
    """Нормализация, фильтрация, кэш и ошибки внешнего API."""

    def setUp(self):
        """Изолировать кэш между тестами."""
        metadata.cache_clear()

    def test_names(self):
        """Версии отделяются от имен, extras сохраняются."""
        self.assertEqual(normalize("Some_Package.Name"), "some-package-name")
        self.assertEqual(package_name("A[b,c]>=1"), "a[b,c]")
        self.assertEqual(package_name("Requests (>=2.0)"), "requests")
        with self.assertRaises(ValueError):
            package_name("!!!")

    def test_metadata_and_cache(self):
        """HTTP-ответ читается стандартной библиотекой только один раз."""
        data = b'{"info":{"requires_dist":["B>=1","C; extra == \'dev\'"]}}'
        with patch("src.main.urlopen", return_value=io.BytesIO(data)):
            self.assertEqual(dependencies("https://example.org", "a"), ["b"])
            self.assertEqual(dependencies("https://example.org", "a"), ["b"])

    def test_optional_and_empty(self):
        """Запрошенный extra включается; null означает пустой список."""
        info = {"requires_dist": ["B; extra == 'fast'", "C", "C"]}
        with patch("src.main.metadata", return_value=info):
            self.assertEqual(dependencies("url", "a[fast]"), ["b", "c"])
        with patch("src.main.metadata", return_value={}):
            self.assertEqual(dependencies("url", "a"), [])

    def test_bad_metadata(self):
        """Сеть, JSON и структура метаданных проверяются."""
        with patch("src.main.urlopen", side_effect=URLError("offline")):
            with self.assertRaises(ValueError):
                metadata("https://example.org", "a")
        for data in [b"bad", b"{}", b'{"info":[]}']:
            with patch("src.main.urlopen", return_value=io.BytesIO(data)):
                with self.assertRaises(ValueError):
                    metadata("https://example.org", "a")


class MarkerTests(unittest.TestCase):
    """Проверка условий версий, платформы, extras и безопасности."""

    def test_marker_expressions(self):
        """Числовые версии не сравниваются лексикографически."""
        self.assertTrue(enabled("'3.10' > '3.9' and '3.10' == '3.10.0'"))
        self.assertFalse(enabled("extra == 'dev'"))
        self.assertTrue(enabled("extra == 'dev' or 'a' in 'cat'"))
        self.assertTrue(enabled("('a' != 'b') and ('a' not in 'xyz')"))
        self.assertTrue(enabled("extra == 'dev'", ("", "dev")))

    def test_reject_code(self):
        """Произвольный Python-код не выполняется."""
        for marker in ["__import__('os')", "unknown == 'x'", "True", "'x'"]:
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                enabled(marker)
