odoo.define('post_multi_uom_product_right.pos_multi_uom_button', function (require) {
    "use strict";
    const Orderline = require("point_of_sale.Orderline");
    const Registries = require("point_of_sale.Registries");
    const {Gui} = require('point_of_sale.Gui');

    const PosOrderline = (Orderline) =>
        class extends Orderline {
            changeUomLine() {
                var core = require('web.core');
                var _t = core._t;

                let orderline = this.props.line;
                let lines_all_units = this.env.pos.units;
                let data = [];
                let price = orderline.price * orderline.get_unit().factor;
                let product = orderline.product

                for (let line of lines_all_units) {
                    if (orderline.get_unit().category_id[0] === line.category_id[0]) {
                        if (product.show_all_uom) {
                            line['price'] = price / line.factor
                            data.push(line)
                        } else {
                            if (orderline.allow_uoms.includes(line.id)) {
                                line['price'] = price / line.factor
                                data.push(line)
                            }
                        }
                    }
                }

                Gui.showPopup("UomOrderlinePopup", {
                    title: _t("POS Multi UOM"),
                    confirmText: _t("Exit"),
                    orderline_allow_uoms: data,
                    product: product,
                });
            }
        };
    Registries.Component.extend(Orderline, PosOrderline);
    return Orderline;
});