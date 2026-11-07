"""Параметры командной строки и их проверка."""

import argparse
import os
import re
from pathlib import Path
from urllib.parse import urlsplit


def arguments(argv=None):
    """Прочитать настройки и проверить каждый пользовательский параметр."""
    parser = argparse.ArgumentParser(description="Зависимости: вариант 26")
    parser.add_argument("--package", required=True, help="имя пакета")
    parser.add_argument("--repository", default="https://pypi.org/pypi",
                        help="URL JSON API или путь к тестовому JSON")
    parser.add_argument("--test", action="store_true", help="тестовый JSON")
    parser.add_argument("--output", default="graph.png", help="выходной PNG")
    parser.add_argument("--stage", type=int, choices=range(1, 6), default=5,
                        help="демонстрация этапа 1-5 (по умолчанию 5)")
    args = parser.parse_args(argv)
    try:
        validate(args)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    return args


def validate(args):
    """Отклонить неверные имя, источник данных и путь результата."""
    pattern = r"[A-Z]+" if args.test else r"[A-Za-z0-9]([\w.-]*[A-Za-z0-9])?"
    if not re.fullmatch(pattern, args.package, flags=re.ASCII):
        raise ValueError("--package: недопустимое имя пакета")
    if args.test:
        if not Path(args.repository).is_file():
            raise ValueError("--repository: тестовый файл не найден")
        inputs = Path(args.repository).resolve()
        output = Path(args.output).resolve()
        if inputs in (output, output.with_suffix(".d2")):
            raise ValueError("--output: результат перезапишет входной файл")
    else:
        validate_url(args.repository)
    validate_output(Path(args.output))


def validate_url(repository):
    """Проверить адрес базового PyPI-совместимого JSON API."""
    if any(char.isspace() for char in repository):
        raise ValueError("--repository: URL не должен содержать пробелы")
    url = urlsplit(repository)
    if url.scheme not in ("http", "https") or not url.hostname:
        raise ValueError("--repository: нужен URL http:// или https://")
    if url.query or url.fragment or url.username or url.password:
        raise ValueError("--repository: лишние части URL")
    if url.port == 0:
        raise ValueError("--repository: недопустимый порт")


def validate_output(output):
    """Проверить формат PNG и доступность выходного пути."""
    if output.suffix.lower() != ".png" or output.is_dir():
        raise ValueError("--output: требуется имя файла с расширением .png")
    if not output.parent.is_dir() or not os.access(output.parent, os.W_OK):
        raise ValueError("--output: каталог не существует или недоступен")
    if output.exists() and not os.access(output, os.W_OK):
        raise ValueError("--output: файл недоступен для записи")
