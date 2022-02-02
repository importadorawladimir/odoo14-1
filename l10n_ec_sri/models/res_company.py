# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    firma_id = fields.Many2one(
        'l10n_ec_sri.firma', string='Firma electrónica', )
    ambiente_id = fields.Many2one(
        'l10n_ec_sri.ambiente', string='Ambiente', )

    takes_accounting = fields.Boolean('Obligado a llevar Contabilidad', default=True)

    agent_retention = fields.Boolean('Agente de Retención?', default=False)
    ar_number_resolution = fields.Char(u'Número de Resolución', help=u"Colocar numero completo\n "
                                                                      u"Sistema selecciona sección que necesita para xml", )
    regime_micro = fields.Boolean(u'Regimen Microempresas?', default=False)

    is_special_taxpayer_number = fields.Boolean('contribuyente especial?', default=False)
    special_taxpayer_number = fields.Char(
        string=u'Número contribuyente especial',
        required=False)

    date = fields.Date(
        string='Fecha Inicio',
        required=False)