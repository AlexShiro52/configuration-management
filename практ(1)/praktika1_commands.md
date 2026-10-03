# Практическая работа №1 — команды и скрипты

Ниже собраны команды и Bash-скрипты, которые мы использовали для решения заданий 1–10.

---

## Задание 1 — пользователи из `/etc/passwd`

Вывести имена пользователей в алфавитном порядке:

```bash
grep -o '^[^:]*' /etc/passwd | sort
```

Полезные части:

```bash
grep -o '^[^:]*' /etc/passwd
sort
```

---

## Задание 2 — 5 наибольших номеров из `/etc/protocols`

```bash
grep -v '^[[:space:]]*#' /etc/protocols |
awk 'NF >= 2 {print $2, $1}' |
sort -nr |
head -n 5
```

Основные команды:

```bash
grep -v '^[[:space:]]*#' /etc/protocols
awk 'NF >= 2 {print $2, $1}'
sort -nr
head -n 5
```

---

## Задание 3 — `banner`

Файл `banner`:

```bash
#!/bin/bash

text="$1"
length=${#text}

border=$(printf '%*s' "$((length + 2))" '' | tr ' ' '-')

echo "+${border}+"
echo "| ${text} |"
echo "+${border}+"
```

Создание и запуск:

```bash
nano banner
chmod +x banner
./banner "Hello from RTU MIREA!"
```

Проверка через ShellCheck:

```bash
shellcheck banner
```

Установка ShellCheck на Ubuntu/Debian:

```bash
sudo apt update
sudo apt install shellcheck
```

Проверка версии:

```bash
shellcheck --version
```

---

## Задание 4 — поиск идентификаторов

Файл `identifiers`:

```bash
#!/bin/bash

grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u | paste -sd ' ' -
```

Запуск:

```bash
chmod +x identifiers
./identifiers hello.c
```

Создать тестовый C-файл:

```bash
nano hello.c
```

Пример содержимого:

```c
#include <stdio.h>

int main(void) {
    int number = 10;
    printf("hello world\n");
    return number;
}
```

Проверка скрипта:

```bash
shellcheck identifiers
```

---

## Задание 5 — регистрация пользовательской команды

Файл `reg`:

```bash
#!/bin/bash

chmod +x "$1"
sudo cp "$1" /usr/local/bin/
```

Подготовка:

```bash
nano reg
chmod +x reg
```

Запуск, если `banner` лежит в другой папке:

```bash
./reg ../t3/banner
```

После этого `banner` можно запускать как обычную команду:

```bash
banner "Hello"
```

Проверить, где находится команда:

```bash
which banner
```

или:

```bash
command -v banner
```

Посмотреть `PATH`:

```bash
echo "$PATH"
```

Если остался остановленный процесс:

```bash
jobs
kill %1
```

---

## Задание 6 — комментарий в первой строке `.c`, `.js`, `.py`

Файл `comments`:

```bash
#!/bin/bash

for file in *.c *.js *.py; do
    first_line=$(head -n 1 "$file")

    case "$file" in
        *.c|*.js)
            if echo "$first_line" | grep -Eq '^[[:space:]]*(//|/\*)'; then
                echo "$file: комментарий есть"
            else
                echo "$file: комментария нет"
            fi
            ;;
        *.py)
            if echo "$first_line" | grep -Eq '^[[:space:]]*#'; then
                echo "$file: комментарий есть"
            else
                echo "$file: комментария нет"
            fi
            ;;
    esac
done
```

Запуск:

```bash
nano comments
chmod +x comments
./comments
```

Тестовые файлы:

```bash
nano test.c
nano test.js
nano test.py
```

`test.c`:

```c
// комментарий в C
#include <stdio.h>

int main(void) {
    printf("Hello\n");
    return 0;
}
```

`test.js`:

```javascript
let x = 10;
// комментарий уже на второй строке
console.log(x);
```

`test.py`:

```python
# комментарий в Python

print("Hello")
```

Проверка:

```bash
shellcheck comments
```

---

## Задание 7 — поиск файлов-дубликатов

Для macOS использовали `shasum`.

Файл `duplicates`:

```bash
#!/bin/bash

find "$1" -type f -exec shasum {} + | sort | awk '
$1 == hash { print previous; print }
{ hash=$1; previous=$0 }
'
```

Подготовка и запуск:

```bash
nano duplicates
chmod +x duplicates
./duplicates test
```

Создать тест:

```bash
mkdir -p test/folder

echo "hello" > test/a.txt
echo "other" > test/b.txt
cp test/a.txt test/folder/copy.txt
```

После этого:

```bash
./duplicates test
```

`a.txt` и `copy.txt` должны иметь одинаковый хеш.

> Примечание: это короткий учебный вариант. Если одинаковых файлов больше двух, некоторые строки могут выводиться повторно.

---

## Задание 8 — архивирование файлов заданного расширения

Файл `archive`:

```bash
#!/bin/bash

dir="$1"
ext="$2"

find "$dir" -type f -name "*.$ext" > files.txt

tar -cf archive.tar -T files.txt

rm files.txt
```

Подготовка:

```bash
nano archive
chmod +x archive
```

Пример запуска:

```bash
./archive test txt
```

Посмотреть содержимое архива:

```bash
tar -tf archive.tar
```

Создать тестовые файлы:

```bash
mkdir -p test/folder

echo "file one" > test/a.txt
echo "file two" > test/b.txt
echo "program" > test/program.c
echo "nested file" > test/folder/c.txt
echo "python" > test/folder/test.py
```

Запуск теста:

```bash
./archive test txt
tar -tf archive.tar
```

В архив должны попасть:

```text
test/a.txt
test/b.txt
test/folder/c.txt
```

---

## Задание 9 — заменить 4 пробела на табуляцию

Файл `spaces`:

```bash
#!/bin/bash

sed $'s/    /\t/g' "$1" > "$2"
```

Подготовка:

```bash
nano spaces
chmod +x spaces
```

Создать входной файл:

```bash
nano input.txt
```

Например:

```text
hello    world
one    two    three
```

Запуск:

```bash
./spaces input.txt output.txt
```

`output.txt` создастся автоматически.

Посмотреть результат:

```bash
cat output.txt
```

Проверить настоящие символы табуляции:

```bash
cat -te output.txt
```

Табуляция отображается как:

```text
^I
```

---

## Задание 10 — пустые `.txt`-файлы

Мы сделали вариант, который проверяет именно файлы с расширением `.txt`.

Файл `empty`:

```bash
#!/bin/bash

dir="$1"

for file in "$dir"/*.txt; do
    if [ -f "$file" ] && [ ! -s "$file" ]; then
        basename "$file"
    fi
done
```

Подготовка:

```bash
nano empty
chmod +x empty
```

Создать тест:

```bash
mkdir -p test

touch test/empty1.txt
touch test/empty2.txt
echo "hello" > test/notempty.txt
echo "test" > test/file.c
```

Запуск:

```bash
./empty test
```

Ожидаемый вывод:

```text
empty1.txt
empty2.txt
```

Посмотреть размеры файлов:

```bash
ls -l test
```

---

## Полезные команды, которые использовались по ходу работы

Создать/редактировать файл:

```bash
nano имя_файла
```

Сделать скрипт исполняемым:

```bash
chmod +x имя_файла
```

Запустить файл из текущей директории:

```bash
./имя_файла
```

Запустить Bash-скрипт явно через Bash:

```bash
bash имя_файла
```

Посмотреть файлы в текущем каталоге:

```bash
ls
```

Посмотреть подробную информацию:

```bash
ls -l
```

Создать пустой файл:

```bash
touch file.txt
```

Создать папку:

```bash
mkdir test
```

Создать папку вместе с вложенными каталогами:

```bash
mkdir -p test/folder
```

Записать строку в файл:

```bash
echo "hello" > file.txt
```

Скопировать файл:

```bash
cp source.txt copy.txt
```

Удалить файл:

```bash
rm file.txt
```

Проверить Bash-скрипт через ShellCheck:

```bash
shellcheck имя_файла
```

---

## Короткая шпаргалка по конструкциям Bash

Первый аргумент:

```bash
$1
```

Второй аргумент:

```bash
$2
```

Цикл:

```bash
for file in ...; do
    команды
done
```

Условие:

```bash
if условие; then
    команды
else
    команды
fi
```

Выбор варианта:

```bash
case "$file" in
    шаблон)
        команды
        ;;
esac
```

Результат команды в переменную:

```bash
result=$(команда)
```

Передача вывода одной команды другой:

```bash
команда1 | команда2
```

Перенаправление вывода в файл:

```bash
команда > file.txt
```

Логическое «И»:

```bash
условие1 && условие2
```

Отрицание:

```bash
!
```
