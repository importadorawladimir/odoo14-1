
# -*- coding: utf-8 -*-
#
#    Sistema FINAMSYS
#    Copyright (C) 2016-Today Ekuasoft S.A All Rights Reserved
#    Ing. Yordany Oliva Mateos <yordanyoliva@ekuasoft.com>
#    Ing. Wendy Alvarez Chavez <wendyalvarez@ekuasoft.com>
#    EkuaSoft Software Development Group Solution
#    http://www.ekuasoft.com
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ek_bank_notes_operations(models.Model):
    _name = 'ek.bank.notes.operations'
    _description = u'Operaciones Bancarias'

    name = fields.Char("Motivo")

    _sql_constraints = [
        ('model_unique',
         'unique(name)',
         u'La operación bancaria debe ser única.'),
    ]

class ek_bank_notes_lines(models.Model):
    _name = 'ek.bank.notes.lines'
    _description = u'Notas de débitos y créditos internas'

    bank_note_id = fields.Many2one('ek.bank.notes', string=u"Nota Bancaria", required=True, ondelete="cascade")
    account_id = fields.Many2one('account.account', string='Cuenta', required=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string=u"Cuenta Analítica",
                                                       ondelete="cascade")
    name = fields.Char(string=u"Descripción", required=False, )
    amount = fields.Float(string='Monto')

class ek_bank_notes(models.Model):
    _name = 'ek.bank.notes'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']
    _description = u'Notas de débitos y créditos bancarias'
    _mail_post_access = 'read'
    _check_company_auto = True
    _sequence_index = "journal_id"

    @property
    def _sequence_monthly_regex(self):
        return self.journal_id.sequence_override_regex or super()._sequence_monthly_regex

    @property
    def _sequence_yearly_regex(self):
        return self.journal_id.sequence_override_regex or super()._sequence_yearly_regex

    @property
    def _sequence_fixed_regex(self):
        return self.journal_id.sequence_override_regex or super()._sequence_fixed_regex


    journal_id = fields.Many2one("account.journal", "Banco", required=True, ondelete="cascade", states={'confirmed':[('readonly',True)]})
    operations_id = fields.Many2one("ek.bank.notes.operations", u"Operación", required=True, states={'confirmed':[('readonly',True)]})
    type = fields.Selection(string="Tipo", selection=[('ndb', u'Nota de Débito Bancaria'), ('ncb', u'Nota de Crédito Bancaria'), ], required=True, states={'confirmed':[('readonly',True)]} )
    name = fields.Char(string=u"Número", required=True, states={'confirmed':[('readonly',True)]}, copy=False, default='/')
    reference = fields.Char(string=u"Referencia", required=False, states={'confirmed': [('readonly', True)]})
    amount_total = fields.Float(string="Total",  required=False, digits=(18,2), readonly=True, compute="compute_amount_total")
    date = fields.Date(string="Fecha", required=True, states={'confirmed':[('readonly',True)]})
    company_id = fields.Many2one('res.company', u'Compañía', default=lambda self: self.env.company, required=True, readonly=True)
    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'),('confirmed', 'Confirmado'), ('canceled', 'Cancelado')], required=False, default='draft')
    notes = fields.Text(string="Notas/Comentarios", required=False, )

    move_id = fields.Many2one("account.move", u"Asiento", required=False, ondelete="cascade",
                                       states={'confirmed': [('readonly', True)]})

    bank_notes_lines_ids = fields.One2many(comodel_name="ek.bank.notes.lines", inverse_name="bank_note_id", string=u"Líneas", required=False, readonly=True, states={'draft':[('readonly',False)]})


    def action_confirmed(self):

        account_move = self.env['account.move']

        for doc in self:
            amount_total = 0.0
            for line in doc.bank_notes_lines_ids:
                amount_total += line.amount

            total = amount_total

            if total == 0:
                raise ValidationError(u'El valor total del documento no puede ser igual a cero.')


            name = doc.name or '/'

            if not doc.journal_id :
                raise ValidationError('No existe el diario contable o no le ha configurado una secuencia.')

            #if name == '/':
            #    name = self._get_last_sequence()

            journal = doc.journal_id
            vals = {'state': 'confirmed', 'name': name, 'amount_total': total}


            line = []

            if doc.type == 'ndb':
                line = [(0, 0, {
                    'name': doc.reference,
                    'credit': total,
                    'account_id': journal.payment_credit_account_id.id,
                    'ref': doc.reference and doc.reference or doc.name
                })]
                for move_line in doc.bank_notes_lines_ids:
                    line += [(0, 0, {
                        'name': move_line.name or doc.reference,
                        'debit': move_line.amount,
                        'account_id': move_line.account_id.id,
                        'ref': doc.reference or move_line.name,
                        'analytic_account_id': move_line.account_analytic_id and move_line.account_analytic_id.id or False,
                    })]

            else:
                line = [(0, 0, {
                    'name': doc.reference,
                    'debit': total,
                    'account_id': journal.payment_debit_account_id.id,
                    'ref': doc.reference and doc.reference or doc.name,
                })]
                for move_line in doc.bank_notes_lines_ids:
                    line += [(0, 0, {
                        'name': move_line.name or doc.reference,
                        'credit': move_line.amount,
                        'account_id': move_line.account_id.id,
                        'ref': doc.reference or move_line.name,
                        'analytic_account_id': move_line.account_analytic_id and move_line.account_analytic_id.id or False,
                    })]

            if doc.move_id:
                doc.move_id.line_ids.unlink()
                doc.move_id.write({'line_ids':line})
                move = doc.move_id
            else:
                move_vals = {
                    'ref': doc.reference and doc.reference or doc.name,
                    'line_ids': line,
                    'journal_id': journal.id,
                    'date': doc.date,
                    'narration': doc.operations_id.name,

                }

                move = account_move.create(move_vals)
                vals.update({'move_id': move.id})


            move.action_post()
            vals.update({'name': move.name})
            doc.write(vals)

        return True


    def action_cancel_draft(self):
        """
        Metodo que se ejecuta cuando el registro ha sido anulado
        y el usuario decide volver al estado borrador.
        """
        for rec in self:
            rec.write({'state': 'draft'})
            if rec.move_id and rec.move_id.state == 'cancel':
                rec.move_id.button_draft()
        return True


    def action_cancel(self):
        """
        Método para cambiar de estado a cancelado el documento
        """
        for doc in self:
            move = doc.move_id
            data = {'state': 'canceled'}
            if (doc.move_id and doc.move_id.state == 'posted'):
                raise ValidationError(
                    u'No se permiten anular transacciones con asientos contables publicados. Por favor anule antes el asiento contable correspondiente.')

            doc.write(data)
            move.button_cancel()
        return True



    def unlink(self):
        for obj in self:
            if obj.state in ['confirmed']:
                raise ValidationError('No se permite borrar transacciones confirmadas.')
            if obj.move_id:
                raise ValidationError('No se permite borrar transacciones que fueron confirmadas en algun momento.')
        res = super(ek_bank_notes, self).unlink()
        return res

    def compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.bank_notes_lines_ids.mapped('amount'))



