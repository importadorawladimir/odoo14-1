odoo.define('ek_pos_ordertoinv.screens', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var utils = require('web.utils');
    var field_utils = require('web.field_utils');
    const PaymentScreen = require('point_of_sale.PaymentScreen');


    const PaymentMethodButtonOverride = PaymentScreen =>
    class extends PaymentScreen {
    
    

                constructor() {
                    super(...arguments);
                
                console.log('uno');
                    if (this.env.pos.config.invisible_button_invoice && this.env.pos.config.invoice_background) {
               console.log("hhhhdosssss");
               var style = document.createElement('style');
                style.innerHTML = `
                    .js_invoice{
                    display:none !important;
                    }
                    `;
                    document.head.appendChild(style);


       

            }


                

            }

    };

    Registries.Component.extend(PaymentScreen, PaymentMethodButtonOverride);


    return PaymentScreen;
});
