"""Создать три примера ZIP, не сохраняя архивы в репозитории."""

from pathlib import Path
from zipfile import ZipFile


def main():
    """Создать VFS с одним каталогом, файлами и вложенными каталогами."""
    examples = Path(__file__).resolve().parent
    variants = {
        "minimal": {"empty/": ""},
        "files": {"hello.txt": "Привет!\n", "my file.txt": "Файл с пробелом"},
        "nested": {
            "hello.txt": "Привет!\n",
            "my file.txt": "Файл с пробелом",
            ".hidden": "Скрытый файл",
            "empty/": "",
            "a/b/c/data.txt": "Три уровня каталогов",
            "binary.bin": bytes(range(256)),
        },
    }
    for name, files in variants.items():
        with ZipFile(examples / f"{name}.zip", "w") as archive:
            for filename, data in files.items():
                archive.writestr(filename, data)


if __name__ == "__main__":
    main()
