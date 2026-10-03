enum Menu = {
    menu_1_5_0,
    menu_1_4_0,
    menu_1_3_0,
    menu_1_2_0,
    menu_1_1_0,
    menu_1_0_0
};

enum Dropdown = {
    drop_2_3_0,
    drop_2_2_0,
    drop_2_1_0,
    drop_2_0_0,
    drop_1_8_0
};

enum Icons = {
    icon_2_0_0,
    icon_1_0_0
};

array[Menu, Dropdown] of bool: MenuDropdown =
[| true,  true,  true,  true,  false
 | true,  true,  true,  true,  false
 | true,  true,  true,  true,  false
 | true,  true,  true,  true,  false
 | true,  true,  true,  true,  false
 | false, false, false, false, true
|];

array[Icons, Dropdown] of bool: DropdownIcons =
[| true,  true,  true,  true,  false
 | false, false, false, false, true
|];

var Menu: selectedMenu;
var Dropdown: selectedDropdown;
var Icons: selectedIcons;

constraint MenuDropdown[selectedMenu, selectedDropdown];

constraint selectedIcons = icon_1_0_0;

constraint DropdownIcons[selectedIcons, selectedDropdown];

solve satisfy;

output [
    "menu = ", show(selectedMenu), "\n",
    "dropdown = ", show(selectedDropdown), "\n",
    "icons = ", show(selectedIcons), "\n"
];