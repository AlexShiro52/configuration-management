"""Небольшой безопасный обработчик условий Requires-Dist, без eval."""

import ast
import operator
import os
import platform
import re
import sys

COMPARE = {ast.Eq: operator.eq, ast.NotEq: operator.ne,
           ast.Lt: operator.lt, ast.LtE: operator.le,
           ast.Gt: operator.gt, ast.GtE: operator.ge,
           ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}


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
