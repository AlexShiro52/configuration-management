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
