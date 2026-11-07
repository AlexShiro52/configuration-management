"""Самостоятельное получение зависимостей через PyPI JSON API."""

import json
import re
from functools import lru_cache
from urllib.error import URLError
from urllib.request import Request, urlopen

from .markers import enabled

TIMEOUT = 20
NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
REQUIREMENT = rf"^({NAME})(?:\[([^\]]+)\])?"


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
