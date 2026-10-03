var bool: root_1_0_0;

var bool: foo_1_0_0;
var bool: foo_1_1_0;

var bool: left_1_0_0;
var bool: right_1_0_0;

var bool: shared_1_0_0;
var bool: shared_2_0_0;

var bool: target_1_0_0;
var bool: target_2_0_0;

% root обязательно установлен
constraint root_1_0_0 = true;

% root 1.0.0 -> foo ^1.0.0 и target ^2.0.0
constraint root_1_0_0 ->
    ((foo_1_0_0 \/ foo_1_1_0) /\ target_2_0_0);

% одновременно можно выбрать только одну версию foo
constraint not (foo_1_0_0 /\ foo_1_1_0);

% foo 1.1.0 -> left ^1.0.0 и right ^1.0.0
constraint foo_1_1_0 ->
    (left_1_0_0 /\ right_1_0_0);

% foo 1.0.0 зависимостей не имеет

% left 1.0.0 -> shared >=1.0.0
constraint left_1_0_0 ->
    (shared_1_0_0 \/ shared_2_0_0);

% right 1.0.0 -> shared <2.0.0
constraint right_1_0_0 ->
    shared_1_0_0;

% только одна версия shared
constraint not (shared_1_0_0 /\ shared_2_0_0);

% shared 1.0.0 -> target ^1.0.0
constraint shared_1_0_0 ->
    target_1_0_0;

% только одна версия target
constraint not (target_1_0_0 /\ target_2_0_0);

% Минимизируем количество установленных пакетов
var int: total =
    bool2int(root_1_0_0) +
    bool2int(foo_1_0_0) +
    bool2int(foo_1_1_0) +
    bool2int(left_1_0_0) +
    bool2int(right_1_0_0) +
    bool2int(shared_1_0_0) +
    bool2int(shared_2_0_0) +
    bool2int(target_1_0_0) +
    bool2int(target_2_0_0);

solve minimize total;

output [
    "root 1.0.0 = ", show(root_1_0_0), "\n",
    "foo 1.0.0 = ", show(foo_1_0_0), "\n",
    "foo 1.1.0 = ", show(foo_1_1_0), "\n",
    "left 1.0.0 = ", show(left_1_0_0), "\n",
    "right 1.0.0 = ", show(right_1_0_0), "\n",
    "shared 1.0.0 = ", show(shared_1_0_0), "\n",
    "shared 2.0.0 = ", show(shared_2_0_0), "\n",
    "target 1.0.0 = ", show(target_1_0_0), "\n",
    "target 2.0.0 = ", show(target_2_0_0), "\n"
];