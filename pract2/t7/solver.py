import json
from collections import defaultdict
from z3 import Bool, Or, Implies, AtMost, Optimize, Sum, If, is_true

# Читаем метаданные пакетов
with open("dependencies.json", "r") as f:
    packages = json.load(f)

# Для каждого пакета/версии автоматически создаём переменную
variables = {}

for i, package in enumerate(packages):
    variables[package] = Bool(f"package_{i}")

solver = Optimize()

# root должен быть установлен
solver.add(variables["root"])

# Автоматически строим ограничения зависимостей
for package, dependency_groups in packages.items():

    for alternatives in dependency_groups:

        possible_versions = [
            variables[dependency]
            for dependency in alternatives
        ]

        solver.add(
            Implies(
                variables[package],
                Or(possible_versions)
            )
        )

# Группируем разные версии одного пакета
versions = defaultdict(list)

for package in packages:

    if package == "root":
        continue

    name = package.split("@")[0]

    versions[name].append(
        variables[package]
    )

# Нельзя одновременно установить две версии одного пакета
for name, package_versions in versions.items():

    if len(package_versions) > 1:
        solver.add(
            AtMost(*package_versions, 1)
        )

# Выбираем минимальное количество пакетов
solver.minimize(
    Sum([
        If(variable, 1, 0)
        for variable in variables.values()
    ])
)

result = solver.check()

print("Result:", result)

if str(result) == "sat":

    model = solver.model()

    print("\nSelected packages:")

    for package, variable in variables.items():

        if is_true(model.eval(variable)):
            print(package)
