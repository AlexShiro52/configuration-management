import argparse
import base64
import calendar
import getpass
import posixpath as path
import shlex
import socket
import zipfile
from datetime import date

MAX_PATH_ARGS = 1
YEAR_ARGS = 1
MONTH_YEAR_ARGS = 2
CHMOD_ARGS = 2
COPY_ARGS = 2
MODE_LENGTHS = (3, 4)


class Shell:
    """Простой эмулятор: файлы и права хранятся только в памяти."""

    def __init__(self, vfs="", script=""):
        """Создать пустую VFS и при необходимости загрузить архив."""
        self.config = {"vfs": vfs, "script": script}
        self.nodes = {"/": (None, 0o755)}
        self.cwd = "/"
        self.history = []
        self.running = True
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        if vfs:
            self.load(vfs)

    def full(self, name):
        """Превратить путь в абсолютный путь внутри VFS."""
        return "/" + path.normpath(path.join(self.cwd, name)).lstrip("/")

    def load(self, filename):
        """Прочитать ZIP без распаковки; содержимое хранить в base64."""
        with zipfile.ZipFile(filename) as archive:
            for info in archive.infolist():
                name = self.full(info.filename)
                parent = path.dirname(name)
                while parent != "/":
                    self.nodes.setdefault(parent, (None, 0o755))
                    parent = path.dirname(parent)
                data = None
                mode = 0o755 if info.is_dir() else 0o644
                if not info.is_dir():
                    data = base64.b64encode(archive.read(info)).decode()
                stored_mode = (info.external_attr >> 16) & 0o7777
                self.nodes[name] = (data, stored_mode or mode)
        for name in self.nodes:
            self.require(path.dirname(name), directory=True)

    def require(self, name, directory=False):
        """Проверить существование файла или каталога."""
        if name not in self.nodes:
            raise ValueError(f"Путь не найден: {name}")
        if directory and self.nodes[name][0] is not None:
            raise ValueError(f"Это не каталог: {name}")

    def prompt(self):
        """Имя пользователя и компьютера берутся из реальной ОС."""
        return f"{self.user}@{self.host}:{self.cwd}$ "

    def conf_dump(self):
        """Вывести параметры запуска в формате ключ=значение."""
        for key, value in self.config.items():
            print(f"{key}={value}")

    def is_directory(self, name):
        """Определить, является ли существующий узел каталогом."""
        return self.nodes[name][0] is None

    def list_entries(self, target):
        """Вернуть файл либо отсортированные записи каталога."""
        if not self.is_directory(target):
            return [target]
        return sorted(name for name in self.nodes
                      if name != target and path.dirname(name) == target)

    def print_entry(self, name, long_format):
        """Вывести имя узла и, по запросу, его права."""
        label = path.basename(name) or "/"
        data, mode = self.nodes[name]
        if data is None and name != "/":
            label += "/"
        print(f"{mode:03o} {label}" if long_format else label)

    def listing_options(self, args):
        """Разобрать флаги ls и выбрать путь для просмотра."""
        names = [arg for arg in args if not arg.startswith("-")]
        flags = set(args) - set(names)
        if len(names) > MAX_PATH_ARGS or flags - {"-a", "-l"}:
            raise ValueError("Формат: ls [-a] [-l] [путь]")
        target = self.full(names[0]) if names else self.cwd
        return target, flags

    def ls(self, args):
        """ls [-a] [-l] [путь]: показать содержимое каталога или файл."""
        target, flags = self.listing_options(args)
        self.require(target)
        show_hidden = "-a" in flags or not self.is_directory(target)
        for name in self.list_entries(target):
            if show_hidden or not path.basename(name).startswith("."):
                self.print_entry(name, "-l" in flags)

    def cd(self, args):
        """cd [путь]: перейти в каталог, без аргумента — в корень VFS."""
        if len(args) > MAX_PATH_ARGS:
            raise ValueError("Формат: cd [путь]")
        target = self.full(args[0]) if args else "/"
        self.require(target, directory=True)
        self.cwd = target

    def cal(self, args):
        """cal [год] или cal месяц год; без аргументов — текущий месяц."""
        today = date.today()
        if not args:
            result = calendar.month(today.year, today.month)
        elif len(args) == YEAR_ARGS:
            result = calendar.calendar(int(args[0]))
        elif len(args) == MONTH_YEAR_ARGS:
            month, year = map(int, args)
            result = calendar.month(year, month)
        else:
            raise ValueError("Формат: cal [год] или cal месяц год")
        print(result, end="")

    def chmod(self, args):
        """chmod права путь: изменить восьмеричные права в памяти."""
        if len(args) != CHMOD_ARGS:
            raise ValueError("Формат: chmod 755 путь")
        mode, name = args
        is_octal = all(char in "01234567" for char in mode)
        if len(mode) not in MODE_LENGTHS or not is_octal:
            raise ValueError("Права: 3 или 4 восьмеричные цифры")
        name = self.full(name)
        self.require(name)
        self.nodes[name] = (self.nodes[name][0], int(mode, 8))

    def copy_target(self, source, target, recursive):
        """Проверить назначение и вычислить итоговый путь копии."""
        self.require(source)
        directory = self.is_directory(source)
        if directory and not recursive:
            raise ValueError("Для копирования каталога нужен cp -r")
        if target in self.nodes and self.is_directory(target):
            target = self.full(path.join(target, path.basename(source)))
        self.validate_copy_paths(source, target, directory)
        return target

    def validate_copy_paths(self, source, target, directory):
        """Исключить копирование в себя и проверить родительский каталог."""
        if source == target or (directory and target.startswith(source + "/")):
            raise ValueError("Нельзя копировать объект в самого себя")
        if directory and source == "/":
            raise ValueError("Копирование корня VFS не поддерживается")
        self.require(path.dirname(target), directory=True)

    def copy_entries(self, source, target):
        """Собрать новые узлы и проверить конфликты до записи в VFS."""
        copies = {target: self.nodes[source]}
        if self.is_directory(source):
            for name, node in self.nodes.items():
                if name.startswith(source + "/"):
                    copies[target + name[len(source):]] = node
        for name, node in copies.items():
            if name in self.nodes:
                if self.is_directory(name) != (node[0] is None):
                    raise ValueError(f"Конфликт файла и каталога: {name}")
        return copies

    def cp(self, args):
        """cp [-r] источник назначение: копировать файлы и каталоги."""
        recursive = bool(args and args[0] == "-r")
        args = args[1:] if recursive else args
        if len(args) != COPY_ARGS:
            raise ValueError("Формат: cp [-r] источник назначение")
        source, target = map(self.full, args)
        target = self.copy_target(source, target, recursive)
        self.nodes.update(self.copy_entries(source, target))

    def print_history(self):
        """Вывести историю введённых команд."""
        for number, item in enumerate(self.history, 1):
            print(number, item)

    def stop(self):
        """Завершить цикл чтения команд."""
        self.running = False

    def dispatch(self, command, args):
        """Найти обработчик команды и передать ему аргументы."""
        commands = {"ls": self.ls, "cd": self.cd, "cal": self.cal,
                    "chmod": self.chmod, "cp": self.cp}
        simple = {"exit": self.stop, "history": self.print_history,
                  "conf-dump": self.conf_dump}
        if command in commands:
            commands[command](args)
        elif command in simple:
            if args:
                raise ValueError(f"{command}: аргументы не нужны")
            simple[command]()
        else:
            raise ValueError(f"Неизвестная команда: {command}")

    def execute(self, line):
        """Разобрать кавычки и комментарии, выполнить одну команду."""
        if line.strip() and not line.lstrip().startswith("#"):
            self.history.append(line)
        try:
            words = shlex.split(line, comments=True)
            if words:
                command, *args = words
                self.dispatch(command, args)
        except ValueError as error:
            print(f"Ошибка: {error}")

    def run(self):
        """Выполнить стартовый скрипт, затем читать команды с клавиатуры."""
        self.conf_dump()
        if self.config["script"]:
            try:
                with open(self.config["script"], encoding="utf-8") as script:
                    for line in script:
                        if not self.running:
                            break
                        line = line.rstrip("\n")
                        print(self.prompt() + line)
                        self.execute(line)
            except (OSError, UnicodeError) as error:
                print(f"Ошибка скрипта: {error}")
        while self.running:
            try:
                self.execute(input(self.prompt()))
            except (EOFError, KeyboardInterrupt):
                print()
                break


def main():
    """Прочитать параметры и запустить консольный эмулятор."""
    parser = argparse.ArgumentParser(description="Эмулятор, вариант 26")
    parser.add_argument("--vfs", default="", help="Путь к ZIP-архиву")
    parser.add_argument("--script", default="", help="Стартовый скрипт")
    args = parser.parse_args()
    try:
        shell = Shell(args.vfs, args.script)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Ошибка загрузки VFS: {error}\n")
    shell.run()


if __name__ == "__main__":
    main()
