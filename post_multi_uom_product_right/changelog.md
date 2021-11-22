# Module post_multi_uom_product_right
All the changes this project will be documented in this file.

## Migrate Module Version 13 => 14 || 24-09-2021

### MODELS

### pos.config

#### ADDED

- add allow_multi_uom field
  - allows the use of multiple units in pos

### product.template

#### ADDED
 
- add has_multi_uom field
  - allows the product to display multi units in the pos
  
- show_all_uom
  - the product will show all the units that have the same category in the pos

- allow_uoms
  - multi units that the product can use

- uom_category
  - allow filter the multi units for category in allow_uoms
  
### STATIC

### pos_multi_uom_button_1.js

#### ADDED
 
- extend Orderline
  - if push button "uom-button" activate function changeUomline

### pos_multi_uom_models.js

#### ADDED
 
- extend models , order and orderline
  - this logic allows change the uom in orderline and save the new uom
  in cache 
  
### pos_multi_uom_popup.js

#### ADDED
 
- Create a pop up 
  - this pop up show the props defined in "uom-button"
  - changes the values of ordeline

### xml / pos_multi_uom_button.xml

#### ADDED
 
- create template to uom-button and locates into orderline
  
### xml / pos_multi_uom_popup.xml

#### ADDED
 
- create template to UomOrderlinePopup 
  - this template will be called from function [changeUomLine]

### VIEWS

### pos.xml

#### ADDED

- adds field in the config session
  - this field allows that the session can use multi uom 
  
- replace field product_uom_id 

### product.xml

#### ADDED

- adds fields into view product
  - this field allows that the products can use multi uom in pos
  
## Update Module version 14 || 01-10-2021

### MODELS

### pos.order.line

#### ADDED

- inherit function _order_line_fields from module "pos_restaurant_get_order_line"
  - this function lets send formatted data from frontend to backend

### pos.order

#### ADDED

- add function _get_fields_for_order_line
 - this function was modularized in the module "pos_restaurant_get_order_line"

- add function _order_line_pos
  - this function was modularized in the module "pos_restaurant_get_order_line"

---------------------------------------------------------------------------------------------
## Update Module Version 14 || 22-10-2021

### MODELS

### pos.order

#### ADDED

- extend function native [_prepare_invoice_line]
  - allows to choose the new unity of measure for account.move.lines

### stock.picking

#### ADDED

- extend function native [_create_move_from_pos_order_lines]
  - allows to separate the lines in stock.move.line if the line had product_uom value

---------------------------------------------------------------------------------------------
## Update Module Version 14 || 27-10-2021

### MODELS

#### ADDED

- extend function native [_create_move_from_pos_order_lines]
  - allows to separate the lines in stock.move.line