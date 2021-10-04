/* Copyright 2021 Ekuasoft Groupsolutions */

odoo.define("ek_pos_consult_credit.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var utils = require("web.utils");
    var rpc = require("web.rpc");

    var _t = core._t;
    var round_pr = utils.round_precision;

    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const ClientListScreen = require("point_of_sale.ClientListScreen");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const ekConsultCredit = (_PaymentScreen) =>
        class extends _PaymentScreen {
            constructor() {
            super(...arguments);
        }
        async renderElement (){
            var self = this;
            var selectedOrder = self.env.pos.get_order();
            var client_id = selectedOrder.get_client();
            var journal_credit = self.env.pos.config.journal_credit_id;
            console.log('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>');
            console.log(client_id);
            console.log(journal_credit);
            console.log('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>');



            try {
                const result = await this.rpc({
                    model: 'account.journal',
                    method: 'get_credit_notes_by_client',
                    args: [journal_credit[0],client_id],
                });

                var creditlines= result.creditlines || {}
                var total_balance= result.total_balance || 0.00

                console.log('>>>>>>>>>>>>>>>RESULT RPC>>>>>>>>>>>>>>>>>');
                console.log(creditlines);
                console.log(total_balance);
                console.log('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>');
                self.showPopup('EkconsultCredPopupWidget', {'creditlines': creditlines,
                                'total_balance':total_balance});
            } catch (error) {
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: 'Offline',
                        body: 'Unable to get orders count',
                    });
                } else {
                    throw error;
                }
            }



        }

        };

    Registries.Component.extend(PaymentScreen, ekConsultCredit);




});
