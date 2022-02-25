from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    dir_establecimiento = fields.Char('Direccion de Establecimiento')

