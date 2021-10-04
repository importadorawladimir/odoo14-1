odoo.define('pos_bag_charges.EkconsultCredPopupWidget', function(require) {
    "use strict";

    const Popup = require('point_of_sale.ConfirmPopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');

    class EkconsultCredPopupWidget extends Popup {

        constructor() {
            super(...arguments);
        }

        go_back_screen() {
            this.showScreen('PaymentScreen');
            this.trigger('close-popup');
        }
        


    };
    EkconsultCredPopupWidget.template = 'EkconsultCredPopupWidget';

    Registries.Component.add(EkconsultCredPopupWidget);

    return EkconsultCredPopupWidget;
});