odoo.define("ek_pos_consult_credit.ek_consultcreditWidget", function (require) {
    "use strict";

    const {useRef} = owl.hooks;
    var models = require('point_of_sale.models');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var core = require('web.core');
    const { Gui } = require('point_of_sale.Gui');

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    var _t = core._t;

    class ek_consultcreditWidget extends PosComponent {
        constructor() {
            super(...arguments);
        }
    }

    ek_consultcreditWidget.template = "ek_consultcreditWidget";

    Registries.Component.add(ek_consultcreditWidget);

    return ek_consultcreditWidget;
});
