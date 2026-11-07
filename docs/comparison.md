# Сравнение с pip и pipdeptree

Проверка: 7 ноября 2026 года; macOS arm64, Python 3.14.7,
pip 26.2.1, pipdeptree 4.2.14. Каждый пакет установлен в отдельное
чистое venv. pip и pipdeptree использованы только как эталон сравнения;
программа из src их не вызывает и не импортирует.

## Порядок загрузки (этап 4)

Из логов pip взята строка `Installing collected packages`, а не
алфавитный список `Successfully installed` и не порядок скачивания.

### requests 2.34.2

- Программа: `charset-normalizer → idna → urllib3 → certifi → requests`.
- pip: `urllib3 → idna → charset-normalizer → certifi → requests`.
- Все зависимости стоят перед потребителями в обоих порядках.

### flask 3.1.3

- Программа: `blinker → click → itsdangerous → markupsafe → jinja2 → werkzeug → flask`.
- pip: `markupsafe → itsdangerous → click → blinker → werkzeug → jinja2 → flask`.
- Все зависимости стоят перед потребителями в обоих порядках.

### httpx 0.28.1

- Программа: `idna → typing-extensions → anyio → certifi → h11 → httpcore → httpx`.
- pip: `typing-extensions → idna → h11 → certifi → httpcore → anyio → httpx`.
- Все зависимости стоят перед потребителями в обоих порядках.

Независимые друг от друга пакеты можно упорядочить несколькими
способами. DFS следует порядку Requires-Dist; pip использует собственный
порядок установки. Различие последовательностей не является ошибкой.

Для цикла A → B → C → A и петли A → A программа сообщает о невозможности
строгого порядка. pip применяет собственную стратегию обработки циклов;
она не превращает циклический граф в ациклический.

## Сравнение визуализации (этап 5)

У pip нет встроенной команды рисования графа. Использован стандартный
инструмент экосистемы pipdeptree: текстовое дерево и JSON-дерево.
Дополнительно сохранены поля метаданных, полученные через `pip inspect`.

| Пакет | Вершины | Ребра | Совпадение с pipdeptree |
|---|---:|---:|---|
| requests | 5 | 4 | Полное |
| flask | 7 | 8 | Полное |
| httpx | 7 | 8 | Полное |

У D2 общая зависимость изображается одной вершиной с несколькими
входящими ребрами. В дереве pipdeptree она может повторяться под разными
родителями. Сравнивались множества вершин и направленных ребер,
а не число строк или расположение узлов на картинке.

## Воспроизведение сравнения

Для каждого PACKAGE из requests, flask, httpx:

```sh
python3 -m venv .venv-check
.venv-check/bin/python -m pip install --only-binary=:all: PACKAGE
.venv-check/bin/python -m pip inspect
python3 -m src.main --package PACKAGE --stage 3
python3 -m src.main --package PACKAGE --stage 4
```

Для эталонного дерева создайте отдельное окружение:

```sh
python3 -m venv .venv-reference
.venv-reference/bin/python -m pip install pipdeptree
.venv-reference/bin/pipdeptree --python .venv-check/bin/python -p PACKAGE
```

В Windows замените bin/python на Scripts/python.exe, а bin/pipdeptree
на Scripts/pipdeptree.exe. Для каждого следующего пакета используйте новое
окружение. Версии могут измениться после даты проверки; зафиксированные
версии и результаты находятся в evidence/*-ours.json и *-pip-inspect.json.

## Возможные отличия на других пакетах

Программа анализирует метаданные последней версии каждого пакета.
Она не устанавливает пакеты и не решает ограничения версий между ними.
pip выбирает совместимые версии, поэтому для других пакетов граф может
отличаться. Также учитываются ОС, версия Python и запрошенные extras.
Для трех приведенных примеров расхождений вершин и ребер не обнаружено.

## Источники и исходные данные

- [Порядок установки pip](https://pip.pypa.io/en/stable/cli/pip_install/#installation-order).
- [pip inspect](https://pip.pypa.io/en/stable/cli/pip_inspect/).
- [pipdeptree](https://github.com/tox-dev/pipdeptree).
- `evidence/*-pip-install.txt`: фактические логи установки.
- `evidence/*-pip-inspect.json`: среда и выбранные поля pip inspect.
- `evidence/*-tree.txt`, `*-tree.json`: фактический вывод pipdeptree.
- `evidence/*-ours.json`: граф, порядок и версии из нашей программы.
- `evidence/comparison.json`: результат проверки множеств вершин и ребер.
