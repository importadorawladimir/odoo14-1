# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class account_payment_wizard(models.TransientModel):
    _name = "ek.account.payment.wizard"

    date = fields.Date(string="Fecha de Corte", required=True, default=lambda self: fields.Date.context_today(self))

    journal_id = fields.Many2one('account.journal', string='Diario', readonly=True, required=False)


    def print_report(self):
        self.ensure_one()
        #data = {'ids': [self.journal_id.id]}
        data = {
            'payment_history_ids' : self.journal_id.payment_history_ids,
            'ids': self.ids,
            'docs': self.ids
        }
        #action = self.env.ref("ek_bank_payment_move_report.report_account_journal_payment_report").report_action(self)
        return self.env.ref("ek_bank_payment_move_report.report_account_journal_payment_report").report_action(self)

    def get_payment_history_lines(self):
        return self.journal_id.payment_history_ids.filtered(lambda rec: rec.date == self.date and rec.journal_id.type in ['bank'])


    def get_payment_history_initial_balance(self):
        return sum(mo.debit - mo.credit for mo in self.journal_id.payment_history_ids.filtered(lambda rec: rec.date < self.date and rec.journal_id.type in ['bank']))

    def get_check_today(self):
        return sum(mo.credit - mo.debit for mo in
                   self.journal_id.payment_history_ids.filtered(lambda rec: rec.date == self.date and rec.check_type == 'issue_check'))

    def get_deposit_today(self):
        return sum(mo.debit - mo.credit for mo in
                   self.journal_id.payment_history_ids.filtered(lambda rec: rec.date == self.date and rec.payment_type == 'inbound' and rec.doc_type == 'deposit'and rec.journal_id.type in ['bank']))

    def get_bank_debit_note(self):
        return abs(sum(mo.credit - mo.debit for mo in
                   self.journal_id.payment_history_ids.filtered(
                       lambda rec: rec.date == self.date and rec.is_bank_note == True and rec.type_bank_note == 'ndb')))

    def get_bank_credit_note(self):
        return abs(sum(mo.credit - mo.debit for mo in
                       self.journal_id.payment_history_ids.filtered(
                           lambda
                               rec: rec.date == self.date and rec.is_bank_note == True and rec.type_bank_note == 'ncb')))
