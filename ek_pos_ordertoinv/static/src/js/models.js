odoo.define('ek_pos_ordertoinv.models', function (require) {
"use strict";


var field_utils = require('web.field_utils');
var rpc = require('web.rpc');
var session = require('web.session');
var time = require('web.time');
var utils = require('web.utils');

var models = require('point_of_sale.models');


var posmodel_super = models.PosModel.prototype;

var _super_order_model = models.Order.prototype;
models.Order = models.Order.extend({
    initialize: function(attributes,options){
        var result = _super_order_model.initialize.apply(this, arguments);
        var partner_default =  this.pos.config.partner_default;

        if (partner_default && this.pos.config.invoice_background){        	
        	var client = this.pos.db.get_partner_by_id(partner_default[0]);        	
        	this.set_client(client);
        	//this.set_to_invoice(true);
        }     
        
        return result;
    },
       

});




});

