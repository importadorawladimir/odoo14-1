# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class L10nLatamDocumentType(models.Model):
    _inherit = 'l10n_latam.document.type'


    electronic_code = fields.Char(string=u'Código Electrónico',
                                      help=u'Código para la facturación eletrónica ecuatoriana')