# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class pos_config(models.Model):
    _inherit = 'pos.config'

    journal_credit_id = fields.Many2one('account.journal','Diario de Credito')
    allow_by_credit = fields.Boolean('Permitir visualizar credito')

	
	

