# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    firma_id = fields.Many2one(
        'l10n_ec_sri.firma', string='Firma electrónica', )
    ambiente_id = fields.Many2one(
        'l10n_ec_sri.ambiente', string='Ambiente', )
