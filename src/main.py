"""Вариант 26: зависимости Python, рекурсивный DFS, D2 и PNG."""

import argparse
import ast
import json
import operator
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

COMPARE = {ast.Eq: operator.eq, ast.NotEq: operator.ne,
           ast.Lt: operator.lt, ast.LtE: operator.le,
           ast.Gt: operator.gt, ast.GtE: operator.ge,
           ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}
TIMEOUT = 20
NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
REQUIREMENT = rf"^({NAME})(?:\[([^\]]+)\])?"
RENDER_TIMEOUT = 120
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


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


def environment(extra=""):
    """Вернуть значения стандартных маркеров текущего интерпретатора."""
    return {"python_version": ".".join(platform.python_version_tuple()[:2]),
            "python_full_version": platform.python_version(),
            "implementation_version": platform.python_version(),
            "implementation_name": sys.implementation.name,
            "os_name": os.name, "sys_platform": sys.platform,
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "platform_machine": platform.machine(),
            "platform_python_implementation": platform.python_implementation(),
            "extra": extra}


def compare(left, operation, right):
    """Сравнить числовые версии покомпонентно, остальные значения как строки."""
    if operation not in COMPARE:
        raise ValueError("Неподдерживаемое сравнение в маркере")
    numeric = r"\d+(\.\d+)*"
    if operation not in (ast.In, ast.NotIn):
        if re.fullmatch(numeric, left) and re.fullmatch(numeric, right):
            left = tuple(map(int, left.split(".")))
            right = tuple(map(int, right.split(".")))
            size = max(len(left), len(right))
            left += (0,) * (size - len(left))
            right += (0,) * (size - len(right))
    return COMPARE[operation](left, right)


def evaluate(node, env):
    """Рекурсивно вычислить только строки, имена, and/or и сравнения."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    if isinstance(node, ast.BoolOp):
        values = [evaluate(value, env) for value in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        return compare(evaluate(node.left, env), type(node.ops[0]),
                       evaluate(node.comparators[0], env))
    raise ValueError("Неизвестное выражение в маркере зависимости")


def enabled(marker, extras=("",)):
    """Проверить условие для базовой установки и запрошенных extras."""
    if not marker.strip():
        return True
    try:
        tree = ast.parse(marker.strip(), mode="eval").body
        results = [evaluate(tree, environment(extra)) for extra in extras]
    except (SyntaxError, TypeError, ValueError) as error:
        raise ValueError(f"Не поддерживается маркер: {marker}") from error
    if any(type(result) is not bool for result in results):
        raise ValueError(f"Ожидалось условие: {marker}")
    return any(results)


def normalize(name):
    """Нормализовать имя Python-пакета по правилам PyPI."""
    return re.sub(r"[-_.]+", "-", name).lower()


def package_name(requirement):
    """Выделить имя и extras; ограничения версий не решаются."""
    match = re.match(REQUIREMENT, requirement.strip())
    if not match:
        raise ValueError(f"Некорректная зависимость: {requirement}")
    name, extras = match.groups()
    if extras:
        names = sorted({normalize(item.strip()) for item in extras.split(",")})
        return f"{normalize(name)}[{','.join(names)}]"
    return normalize(name)


@lru_cache(maxsize=None)
def metadata(repository, package):
    """Прочитать метаданные последней версии, один HTTP-запрос на пакет."""
    url = f"{repository.rstrip('/')}/{package}/json"
    request = Request(url, headers={"User-Agent": "variant26/1.0"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            info = json.load(response)["info"]
        if not isinstance(info, dict):
            raise ValueError("info не является объектом")
        return info
    except (URLError, OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Не удалось прочитать {url}: {error}") from error


def dependencies(repository, package):
    """Получить прямые зависимости, учитывая условия среды и extras."""
    base, _, tail = package.partition("[")
    extras = ("",) + tuple(tail.rstrip("]").split(",")) if tail else ("",)
    requirements = metadata(repository, base).get("requires_dist") or []
    if not isinstance(requirements, list):
        raise ValueError("requires_dist должен быть списком")
    result = []
    for requirement in requirements:
        if not isinstance(requirement, str):
            raise ValueError("Зависимость должна быть строкой")
        spec, _, marker = requirement.partition(";")
        if enabled(marker, extras):
            result.append(package_name(spec))
    return list(dict.fromkeys(result))


def read_graph(path):
    """Прочитать JSON-граф и проверить имена, списки и ссылки."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("Тестовый граф должен быть непустым JSON-объектом")
    for name, children in data.items():
        if not re.fullmatch(r"[A-Z]+", name):
            raise ValueError(f"Имя {name!r}: нужны большие латинские буквы")
        if not isinstance(children, list):
            raise ValueError(f"Зависимости {name} должны быть списком")
        for child in children:
            if not isinstance(child, str) or child not in data:
                raise ValueError(f"Неизвестная зависимость {name}: {child!r}")
        data[name] = list(dict.fromkeys(children))
    return data


def build_graph(root, get_dependencies):
    """Обойти достижимые вершины рекурсивным DFS, сохранив циклы."""
    graph = {}

    def visit(node):
        """Зарегистрировать вершину до рекурсивного обхода ее соседей."""
        if node in graph:
            return
        graph[node] = list(dict.fromkeys(get_dependencies(node)))
        for child in graph[node]:
            visit(child)

    visit(root)
    return graph


def load_order(graph, root):
    """Вернуть зависимости раньше потребителей; при цикле сообщить его путь."""
    done, active, order, path = set(), set(), [], []

    def visit(node):
        """Добавить вершину в результат после обхода всех зависимостей."""
        if node in active:
            cycle = path[path.index(node):] + [node]
            raise ValueError("Нет порядка загрузки: цикл " + " -> ".join(cycle))
        if node in done:
            return
        active.add(node)
        path.append(node)
        for child in graph[node]:
            visit(child)
        path.pop()
        active.remove(node)
        done.add(node)
        order.append(node)

    visit(root)
    return order


def to_d2(graph):
    """Сформировать D2; отдельные ID защищают подписи от синтаксиса D2."""
    ids = {node: f"n{index}" for index, node in enumerate(graph)}
    lines = ["direction: right"]
    for node in graph:
        lines.append(f"{ids[node]}: {json.dumps(node, ensure_ascii=False)}")
    for node, children in graph.items():
        lines.extend(f"{ids[node]} -> {ids[child]}" for child in children)
    return "\n".join(lines) + "\n"


def render(graph, output):
    """Сохранить D2 и создать PNG, проверив успешность внешнего рендерера."""
    output = Path(output).resolve()
    source = output.with_suffix(".d2")
    source.write_text(to_d2(graph), encoding="utf-8")
    executable = shutil.which("d2")
    if not executable:
        raise ValueError(f"D2 не найден в PATH. Описание сохранено: {source}")
    with tempfile.TemporaryDirectory(dir=output.parent) as folder:
        image = Path(folder) / "graph.png"
        try:
            result = subprocess.run([executable, str(source), str(image)],
                                    capture_output=True, text=True,
                                    timeout=RENDER_TIMEOUT, check=False)
        except subprocess.TimeoutExpired as error:
            raise ValueError("Превышено время построения PNG") from error
        if result.returncode:
            raise ValueError(f"Ошибка D2: {result.stderr.strip()}")
        if not image.is_file():
            raise ValueError("D2 не создал PNG")
        with image.open("rb") as stream:
            if stream.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                raise ValueError("D2 создал файл, который не является PNG")
        image.replace(output)
    return source


def main(argv=None):
    """Запустить выбранный этап, сообщив об ошибке без traceback."""
    args = arguments(argv)
    try:
        run(args)
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


def run(args):
    """Выполнить выбранный этап: настройки, данные, DFS, порядок или PNG."""
    if args.stage == 1:
        for key, value in vars(args).items():
            print(f"{key}={value}")
        return
    root, get_dependencies = source(args)
    if args.stage == 2:
        print("\n".join(get_dependencies(root)) or "Нет прямых зависимостей")
        return
    graph = build_graph(root, get_dependencies)
    if args.stage == 3:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
        return
    if args.stage == 4:
        print(" -> ".join(load_order(graph, root)))
        return
    description = render(graph, args.output)
    print(f"D2: {description}\nPNG: {args.output}")


def source(args):
    """Выбрать независимый от DFS источник прямых зависимостей."""
    if args.test:
        graph = read_graph(args.repository)
        if args.package not in graph:
            raise ValueError(f"Пакет {args.package} отсутствует в репозитории")
        return args.package, graph.__getitem__
    return normalize(args.package), lambda name: dependencies(
        args.repository, name)


if __name__ == "__main__":
    raise SystemExit(main())
