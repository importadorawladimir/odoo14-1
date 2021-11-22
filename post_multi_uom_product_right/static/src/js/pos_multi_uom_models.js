odoo.define('post_multi_uom_product_right.pos_multi_uom_order', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var utils = require('web.utils');
    var field_utils = require('web.field_utils');

    var round_pr = utils.round_precision;

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_pricelist: function (pricelist) {
            var self = this;
            this.pricelist = pricelist;

            var lines_to_recompute = _.filter(this.get_orderlines(), function (line) {
                return !line.price_manually_set;
            });
            _.each(lines_to_recompute, function (line) {
                if (line.product_uom === '') {
                    line.set_unit_price(line.product.get_price(self.pricelist, line.get_quantity()));
                    self.fix_tax_included_price(line);
                }
            });
            this.trigger('change');
        },
    });

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attributes, options) {
            _super_order_line.initialize.apply(this, arguments);
            this.has_multi_uom = this.get_product().has_multi_uom || false;
            this.allow_uoms = this.get_product().allow_uoms;
            this.product_uom = this.product_uom || '';
        },
        set_product_uom: function (uom_id) {
            this.product_uom = this.pos.units_by_id[uom_id];
            this.trigger('change', this)
        },
        set_quantity: function (quantity, keep_price) {

            this.order.assert_editable();
            if (quantity === 'remove') {
                this.order.remove_orderline(this);
                return;
            } else {
                var quant = parseFloat(quantity) || 0;
                var unit = this.get_unit();
                if (unit) {
                    if (unit.rounding) {
                        var decimals = this.pos.dp['Product Unit of Measure'];
                        var rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                        this.quantity = round_pr(quant, rounding);
                        this.quantityStr = field_utils.format.float(this.quantity, {digits: [69, decimals]});
                    } else {
                        this.quantity = round_pr(quant, 1);
                        this.quantityStr = this.quantity.toFixed(0);
                    }
                } else {
                    this.quantity = quant;
                    this.quantityStr = '' + this.quantity;
                }
            }

            // just like in sale.order changing the quantity will recompute the unit price
            if (this.product_uom === '') {
                if (!keep_price && !this.price_manually_set) {
                    this.set_unit_price(this.product.get_price(this.order.pricelist, this.get_quantity()));
                    this.order.fix_tax_included_price(this);
                }
            }
            this.trigger('change', this);
        },

        get_unit: function () {
            return this.product_uom === '' ? this.product.get_unit() : this.product_uom;
        },

        init_from_JSON: function (json) {
            var self = this;
            _super_order_line.init_from_JSON.apply(this, arguments);
            this.has_multi_uom = json.has_multi_uom;
            this.allow_uoms = json.allow_uoms;
            this.product_uom = json.product_uom;
        },
        export_as_JSON: function () {
            var self = this;
            var json = _super_order_line.export_as_JSON.apply(this, arguments);
            json.has_multi_uom = this.has_multi_uom;
            json.allow_uoms = this.allow_uoms;
            json.product_uom = this.product_uom === '' ? '': this.product_uom;
            return json;
        },
        export_for_printing: function () {
            var json = _super_order_line.export_for_printing.apply(this, arguments);
            json['has_multi_uom'] = this.allow_uoms
            json['allow_uoms'] = this.allow_uoms;
            return json;
        },
    });
});


