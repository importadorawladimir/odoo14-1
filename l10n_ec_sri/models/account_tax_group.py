# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    l10n_ec_electronic_code = fields.Char(string=u'Código Electrónico',
                                          help=u'Código para la facturación eletrónica ecuatoriana')

