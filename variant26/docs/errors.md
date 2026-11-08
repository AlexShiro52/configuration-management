# Демонстрация ошибок параметров

Все примеры реально запущены. Ожидается код 2 и отсутствие traceback.

```text
$ python3 -m src.main --package bad/name
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: --package: недопустимое имя пакета
exit=2
```

```text
$ python3 -m src.main --package A --test --repository missing.json
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: --repository: тестовый файл не найден
exit=2
```

```text
$ python3 -m src.main --package requests --repository bad-url
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: --repository: нужен URL http:// или https://
exit=2
```

```text
$ python3 -m src.main --package requests --test false
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: unrecognized arguments: false
exit=2
```

```text
$ python3 -m src.main --package requests --output out.jpg
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: --output: требуется имя файла с расширением .png
exit=2
```

```text
$ python3 -m src.main --package requests --output missing-directory/out.png
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: --output: каталог не существует или недоступен
exit=2
```

```text
$ python3 -m src.main --package requests --stage 6
usage: python3.14 -m src.main [-h] --package PACKAGE [--repository REPOSITORY]
                              [--test] [--output OUTPUT] [--stage {1,2,3,4,5}]
python3.14 -m src.main: error: argument --stage: invalid choice: '6' (choose from '1', '2', '3', '4', '5')
exit=2
```

Ошибки данных (неизвестная вершина, поврежденный JSON, сеть и D2)
проверяются тестами. Цикл в режиме порядка загрузки имеет код 1;
примеры находятся в `evidence/demo.txt`.
