# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError



class PosConfig(models.Model):
	_inherit = 'pos.config'

	invoice_background = fields.Boolean(string = 'Facuturar En Segundo Plano?', default=False)
