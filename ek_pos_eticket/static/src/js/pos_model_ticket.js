odoo.define('ek_pos_eticket.pos_model_ticket', function (require) {
    "use strict"

    var pos_model = require("point_of_sale.models");
    var SuperPosModel = pos_model.PosModel.prototype;
    var SuperOrder = pos_model.Order.prototype;
    var rpc = require('web.rpc');
    var core = require('web.core');
    var qweb = core.qweb;
    var l10n_latam_document_type_id = "";
    var invoice_date_due = "";
    var company_id = "";
    var street = "";
    var city = "";
    var country = "";
    var invoice_name = "";
    var account_move = 0;
    var access_key = "";






    pos_model.PosModel = pos_model.PosModel.extend({

        _flush_orders: function (orders, options) {
            var self = this;
            var result, data;
            result = data = SuperPosModel._flush_orders.call(this, orders, options)
            _.each(orders, function (order) {

                if (order.to_invoice)
                    var order = self.env.pos.get_order();
                //if (this.env.pos.config.receipt_invoice_number)
                data.then(function (order_server_id) {
                    rpc.query({
                        model: 'pos.order',
                        method: 'read',
                        domain: [['pos_reference', '=', order['name']]],
                        fields: ['account_move'],
                        args: [order_server_id, ['account_move', 'company_id']]
                    }).then(function (result_dict) {
                        if (result_dict.length) {
                            let invoice = result_dict[0].account_move;
                            self.get_order().invoice_id = invoice[1];
                            account_move = result_dict[0]['account_move'][0];
                            company_id = result_dict[0]['company_id'][0];

                        }
                    }).then(function (einvoices) {
                        rpc.query({
                            model: 'account.move',
                            method: 'search_read',
                            args: [[['id', '=', account_move]], ['name',
                                    'invoice_date',
                                    'l10n_latam_document_type_id',
                                    'company_id'
                                ]],
                        }
                        ).then(function (einvoicejm) {
                            if (account_move > 0) {
                                console.log("cargando account_move");
                                console.log(einvoicejm);
                                invoice_name = einvoicejm[0]['name'];

                                l10n_latam_document_type_id = einvoicejm[0]['l10n_latam_document_type_id'];
                                invoice_date_due = einvoicejm[0]['invoice_date'];
                                var split_invoice_date_due = invoice_date_due.split('-');
                                invoice_date_due = split_invoice_date_due[2] + "-" + split_invoice_date_due[1] + "-" + split_invoice_date_due[0];
                                company_id = einvoicejm[0]['company_id'][0];
                            }
                        }).then(function (company) {
                            rpc.query({
                                model: 'res.company',
                                method: 'search_read',
                                args: [[['id', '=', company_id]], ['street', 'city', 'state_id', 'country_id', 'company_registry', 'zip']],
                            }).then(function (company_partner) {
                                street = company_partner[0]['street'];
                                city = company_partner[0]['city'];
                                country=company_partner[0]['country_id'];
                            }).then(function (accountedidocument) {
                                    rpc.query({
                                        model: 'account.edi.document',
                                        method: 'search_read',
                                        args: [[['move_id', '=', account_move]], ['claveacceso']],
                                    }).then(function (edidocument) {
                                        access_key = edidocument[0]['claveacceso'];

                                    });


                        });


                        });


                    }).catch(function (error) {
                        return result;
                    });
                });
            });
            return result;

        },

    });
    pos_model.Order = pos_model.Order.extend({
        get_base_ec_by_tax: function () {
                var base_by_tax = {};
                this.get_orderlines().forEach(function (line) {
                    var tax_detail = line.get_tax_details();
                    var base_price = line.get_price_without_tax();
                    if (tax_detail) {
                        Object.keys(tax_detail).forEach(function (tax) {
                            if (Object.keys(base_by_tax).includes(tax)) {
                                base_by_tax[tax] += base_price;
                            } else {
                                base_by_tax[tax] = base_price;
                            }
                        });
                    }
                });
                console.log('BASE X IMPUESTO');
                console.log(base_by_tax);
                return base_by_tax;
            },
        export_for_printing: function () {
            var self = this;
            var receipt = SuperOrder.export_for_printing.call(this);
            if (self.invoice_id) {
                var invoice_id = self.invoice_id;
                var invoice = invoice_id.split("(")[0];
                var invoice = invoice.replace(/[^0-9]/g, '');
                if (invoice.length === 15) {
                        var invoice = invoice.substring(0,3)+"-"+invoice.substring(3,6)+"-"+invoice.substring(6);
                    }


                var invoice_number = "";
                var invoice_letter = "";
                invoice_number = invoice_id.split("(")[0];
                invoice_letter = invoice_id.split("(")[0].substring(3, 4);
                //invoice_letter = orders[0]['account_move'][1].split(" ")[0].substring(3, 4);

                receipt.access_key = access_key;
                receipt.street = street;
                receipt.city = city;
                receipt.invoice_id = invoice;
                receipt.country=country;
                receipt.l10n_latam_document_type_id = l10n_latam_document_type_id;
                receipt.invoice_date_due = invoice_date_due;
                var base_by_tax = this.get_base_ec_by_tax();
                for (const tax of receipt.tax_details) {
                    tax.base = base_by_tax[tax.tax.id];
                    console.log('>>>');
                    console.log(base_by_tax[tax.tax.id]);
                }


            }
            return receipt;
        }
    });


});
