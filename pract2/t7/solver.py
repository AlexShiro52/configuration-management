"""Подобрать минимальный набор совместимых зависимостей с помощью Z3."""

import json
from collections import defaultdict
from z3 import Bool, Or, Implies, AtMost, Optimize, Sum, If, is_true

SINGLE_VERSION = 1

with open("dependencies.json", "r") as f:
    packages = json.load(f)

variables = {}

for i, package in enumerate(packages):
    variables[package] = Bool(f"package_{i}")

solver = Optimize()

solver.add(variables["root"])

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

versions = defaultdict(list)

for package in packages:

    if package == "root":
        continue

    name = package.split("@")[0]

    versions[name].append(
        variables[package]
    )

for name, package_versions in versions.items():

    if len(package_versions) > SINGLE_VERSION:
        solver.add(
            AtMost(*package_versions, SINGLE_VERSION)
        )

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
