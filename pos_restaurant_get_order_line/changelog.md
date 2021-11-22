# Changelog Module pos_restaurant_get_order_line
All the changes this project will be documented in this file.

## Create Module Version 14 || 17-08-2021

### Models

#### ADDED
- change function [_get_fields_for_order_line]:
  - add fields for order lines
- add new function [_order_lines_combo]:
  - this function allows the proper functioning of the combo
- change function [_get_order_lines]:
  -  call a new function 

### STATIC / PosSelectionComboRest.js

#### ADDED
- change function [can_be_merged_with]:
  - this change stops the merge of the lines that have property is_selection_combo

## Update Module Version 14 || 01-10-2021

### Models

### pos.order

#### ADDED

- add function _order_line_pos
  - this function was modularized in the module "pos_restaurant_get_order_line"

#### CHANGED

- change function _get_order_lines 
  - this function was modularized in the module "pos_restaurant_get_order_line"


