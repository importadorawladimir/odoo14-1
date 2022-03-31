# -*- coding: utf-8 -*-
__author__ = 'yordany'
import logging
from datetime import date
from odoo import models
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.safe_eval import safe_eval
import time

class AccountAtsSustento(models.Model):
    _name = 'account.ats.sustento'
    _description = 'Sustento del Comprobante'

    def name_get(self):
        return [(record.id, '%s - %s' % (record.code,record.type)) for record in self]


    #ek_l10n_ec
    code = fields.Char(u'Código', size=2, required=True)
    type = fields.Char('Tipo de Sustento', size=150, required=True)
    account_ats_doc_ids = fields.Many2many("l10n_latam.document.type", "account_ats_doc_rel", "account_ats_sustento_id",
                                           "account_ats_doc_id", string="Tipos Comprobantes")

class AccountMove(models.Model):
    _inherit = 'account.move'
    retention_id = fields.Many2one('account.retention', string='Doc. Retención', copy=False)

    l10n_latam_document_auth = fields.Char(
        string=u'Número de Autorización', readonly=True, states={'draft': [('readonly', False)]})

    l10n_latam_document_sustento = fields.Many2one(
        comodel_name='account.ats.sustento',
        string='Sustento',
        required=False)

    l10n_latam_document_sustento_id = fields.Many2one('account.move', string='Doc. Sustento', copy=False)

    def action_post(self):
        for isec in self:
            rec = super(AccountMove, isec).action_post()
            if isec.move_type == 'in_invoice':
                return isec.action_in_retention_create()

        return rec

    def button_draft(self):
        for isec in self:
            rec = super(AccountMove, isec).button_draft()
            if isec.move_type == 'in_invoice':
                return isec.action_in_retention_cancel_draft()


    def action_in_retention_cancel_draft(self):
        """
        Redefinicion de metodo para borrar la retencion asociada.
        CHECK: saber si es correcto eliminar o hacer cache del
        numero del documento.
        """
        for inv in self:
            if inv.retention_id:
                inv.retention_id.write({'state': 'draft'})
                inv.line_ids.filtered(lambda a: a.credit == 0 and a.debit == 0 and a.retention_id.id == inv.retention_id.id).unlink()
                inv.retention_id.unlink()
        return True

    def action_in_retention_create(self):
        """
        Este método genera el documento de retencion en varios escenarios
        considera casos de:
        * Generar retencion automaticamente
        * Generar retencion de reemplazo
        * Cancelar retencion generada
        """
        for inv in self:
            # if inv.create_retention_type == 'manual':
            #    continue

            wd_number = False

            #if inv.create_retention_type == 'manual':
            #    if inv.l10n_latam_manual_document_number < 0:
            #        raise UserError(_(u'El número de retención es incorrecto.'))
            #    if inv.l10n_latam_manual_document_number == 0:
            #        continue
            #    wd_number = str(inv.l10n_latam_manual_document_number).rjust(9, "0")

            if inv.retention_id:
                inv.retention_id.action_validate(wd_number)
                continue

            if inv.move_type not in ['in_invoice', 'liq_purchase']:
                continue
                #line_ids

            #line.tax_ids
            tids = [l.id for l in inv.line_ids if l.l10n_ec_type in ['withhold_income_tax', 'withhold_vat']] + self.get_tax_zero(inv)

            if tids and len(tids) > 0:
                _type = self.env['l10n_latam.document.type'].search([('l10n_ec_type','=','in_withhold'),('internal_type','=','invoice')],limit=1)
                if len(_type) == 0:
                    raise ValidationError(
                        u"No existe un tipo de documento que permita realizar las retenciones de proveedor.")

                withdrawing = self.env['account.retention'].create({
                    'invoice_id': inv.id,
                    'move_type': 'ret_in_invoice',
                    'type': inv.move_type,
                    'date': inv.date,
                    'company_id': inv.company_id.id,
                    'ref': inv.name,
                    'l10n_latam_document_type_id': _type.id,
                    'name': '/',
                    'journal_id': inv.journal_id.id
                })

                account_invoice_tax = self.env['account.move.line'].browse(tids)
                account_invoice_tax.write({'retention_id': withdrawing.id})
                inv.write({'retention_id': withdrawing.id})
                withdrawing.action_validate()
        return True

    # calculando retenciones en facturas con impuesto 0%
    def get_tax_zero(self,inv):
        tax_line = {}
        line_ids = []
        move_line_obj = self.env['account.move.line']
        for line in inv.invoice_line_ids:
            for tax in line.tax_ids.filtered(lambda a: a.amount == 0 and a.tax_group_id.l10n_ec_type in ['withhold_income_tax', 'withhold_vat']):

                if not tax.id in tax_line:
                    tax_line[tax.id] = {
                        'tax_line_id': tax.id,
                        'name': tax.name,
                        'partner_id': inv.partner_id.id,
                        'move_id': inv.id,
                        'tax_base_amount': 0.00,
                        'debit': 0.00,
                        'credit': 0.00,
                        'quantity': 1,
                        'date': inv.invoice_date,
                        'exclude_from_invoice_tab': True

                    }
                    invoice_repartition_lines = tax.mapped('invoice_repartition_line_ids').filtered(
                        lambda line: line.repartition_type == 'tax')

                    tag_ids = []
                    account_id = False
                    for inv_repartition_line in invoice_repartition_lines:
                        tag_ids += inv_repartition_line.tag_ids.ids
                        account_id = inv_repartition_line.account_id.id

                    tax_line[tax.id]['tax_tag_ids'] = [(6, 0, tag_ids)]
                    tax_line[tax.id]['account_id'] = account_id

                tax_line[tax.id]['tax_base_amount'] += line.price_subtotal

        for data in tax_line.values():
            _id = move_line_obj.create(data)

            line_ids.append(_id.id)
        return line_ids


class AccountCompoundTax(models.Model):
    _inherit = "account.tax"

    compound_tax = fields.Many2one(
        comodel_name='account.tax',
        string='Calcular desde',
        required=False)

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        self.ensure_one()
        if product and product._name == 'product.template':
            product = product.product_variant_id
        if self.tax_group_id.l10n_ec_type in ['withhold_vat']:
            company = self.env.company
            if self.compound_tax:
                base_amount = self.compound_tax._compute_amount(base_amount, price_unit, quantity, product, partner)


            localdict = {'base_amount': base_amount, 'price_unit':price_unit, 'quantity': quantity, 'product':product, 'partner':partner, 'company': company, 'compute_tax': self.amount}
            safe_eval("result = base_amount * (compute_tax/100)", localdict, mode="exec", nocopy=True)
            return localdict['result']
        return super(AccountCompoundTax, self)._compute_amount(base_amount, price_unit, quantity, product, partner)
