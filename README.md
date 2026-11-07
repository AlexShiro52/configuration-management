# Граф зависимостей Python: вариант 26

Практическая работа № 2 по конфигурационному управлению, ИКБО-18-25.
Python 3.10+, стандартная библиотека. Сборка не требуется.

## Этап 1

```sh
python3 -m src.main --package requests --stage 1
python3 -m unittest discover -s tests -v
```

`arguments()` читает CLI, `validate()` проверяет параметры,
`main()` запускает программу.

Настройки: `--package` - имя, `--repository` - URL API или тестовый JSON,
`--test` - тестовый режим, `--output` - путь PNG, `--stage` - этап 1-5.
По умолчанию: PyPI, реальный режим, `graph.png`, этап 5.

## Этап 2

```sh
python3 -m src.main --package requests --stage 2
```

`metadata()` читает `/pypi/<имя>/json` через urllib с кэшем и тайм-аутом.
`dependencies()` извлекает прямые зависимости из `requires_dist`.
`normalize()` нормализует имена, `package_name()` выделяет имя и extras.
`environment()`, `compare()`, `evaluate()`, `enabled()` проверяют условия
среды без eval и сторонних библиотек.

Это граф метаданных последних версий, а не решатель ограничений версий.
Условия поддерживают сравнения ==, !=, <, <=, >, >=, in, not in, and/or
и скобки. Числовые версии сравниваются покомпонентно. Редкие операторы
~=, === и версии с суффиксами PEP 440 не поддерживаются полностью.
Официальное описание API: https://docs.pypi.org/api/json/.

## Этап 3

```sh
python3 -m src.main --package A --test --repository examples/diamond.json --stage 3
python3 -m src.main --package A --test --repository examples/cycle.json --stage 3
```

`read_graph()` проверяет JSON вида `{"A": ["B"], "B": []}`.
Все вершины объявляются явно, имена состоят из A-Z.
`build_graph()` использует рекурсивный DFS: вершина отмечается до обхода
соседей, поэтому циклы сохраняются, но не вызывают бесконечной рекурсии.
`source()` выбирает источник данных. Примеры: цепь, ромб с общей
зависимостью, цикл, петля, отдельная вершина и недостижимый пакет Z.

## Этап 4

```sh
python3 -m src.main --package A --test --repository examples/diamond.json --stage 4
python3 -m src.main --package requests --stage 4
```

`load_order()` добавляет вершину после рекурсивного обхода зависимостей:
для ромба получается `D -> B -> C -> A`, для цепи `C -> B -> A`.
При цикле выводится его путь и код завершения 1: строгого порядка нет.
Порядок означает установку зависимостей до потребителей, а не очередность
скачивания архивов по сети. Сравнение с pip приводится в docs/comparison.md.
