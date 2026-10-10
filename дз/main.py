import getpass
import socket
import os
import shlex

user = getpass.getuser()
host = socket.gethostname()

while True:
    try:
        parts = shlex.split(input(f"{user}@{host}:{os.getcwd()}$ "))
    except ValueError:
        print("Ошибка: незакрытая кавычка")
        continue
    except (EOFError, KeyboardInterrupt):
        print()
        break

    if not parts:
        continue

    command, *args = parts

    if command == "exit":
        break
    elif command in ("ls", "cd"):
        print(f"Команда: {command}, аргументы: {args}")
    else:
        print(f"Ошибка: неизвестная команда '{command}'")