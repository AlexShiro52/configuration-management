"""Преобразование графа в D2 и PNG через официальный рендерер D2."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

RENDER_TIMEOUT = 120
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


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
