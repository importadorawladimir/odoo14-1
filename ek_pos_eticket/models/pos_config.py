# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class pos_config(models.Model):

    _inherit = "pos.config"

    pos_auto_invoice = fields.Boolean('Facturacion Automatica',
                                      help='Activa automaticamente el boton Factura',
                                      default=1)
    receipt_invoice_number = fields.Boolean('Mostrar el numero de factura', default=1)
    receipt_customer_vat = fields.Boolean('Mostrar Identificacion de Cliente', default=1)
    partner_default = fields.Many2one('res.partner', string = 'Cliente Defecto')
    print_pdf_invoice = fields.Boolean('Imprimir Factura', default=1)


