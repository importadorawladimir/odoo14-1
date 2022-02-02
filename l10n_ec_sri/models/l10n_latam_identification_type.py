# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.osv import expression


class L10nLatamIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    electronic_code = fields.Char(
        string=u'Código Electrónico',
        required=False)