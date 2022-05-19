# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.depends('check_ids')
    def _compute_check(self):
        for rec in self:
            # we only show checks for issue checks or received thid checks
            # if len of checks is 1
            if rec.payment_method_code in (
                    'received_third_check',
                    'issue_check',) and len(rec.check_ids) == 1:
                rec.check_id = rec.check_ids[0].id

    check_deposit_type = fields.Selection(
        [('consolidated', 'Consolidated'),
         ('detailed', 'Detailed')],
        default='detailed',
        help="This option is relevant if you use bank statements. Detailed is"
             " used when the bank credits one by one the checks, consolidated is"
             " for when the bank credits all the checks in a single movement",
    )

    payment_method_code = fields.Char(
        related='payment_method_id.code',
        help="Technical field used to adapt the interface to the payment type selected.")
    check_ids = fields.Many2many(
        'account.check',
        string='Checks',
        copy=False,
        auto_join=True,
    )
    check_name = fields.Char(
        'Nombre',
        copy=False,
    )
    check_number = fields.Char(
        'Numero de Cheque',
        default=False,
        copy=False,
        compute=False,
        inverse=False,
    )
    check_issue_date = fields.Date(
        'Fecha Emision',
        copy=False,

        default=fields.Date.context_today,
    )
    check_payment_date = fields.Date(
        'Fecha Pago',

        help="Only if this check is post dated",

    )
    checkbook_id = fields.Many2one(
        'account.checkbook',
        'Chequera',
        auto_join=True,
    )
    check_subtype = fields.Selection(
        related='checkbook_id.issue_check_subtype',
    )
    check_bank_id = fields.Many2one(
        'res.bank',
        'Banco',
        copy=False,
        auto_join=True,
    )
    check_owner_vat = fields.Char(
        'CUIT del Emisor',
        copy=False,
    )
    check_owner_name = fields.Char(
        'Nombre Emisor',
        copy=False,
    )
    # this fields is to help with code and view
    check_type = fields.Char(
        compute='_compute_check_type',
        store=True
    )
    checkbook_numerate_on_printing = fields.Boolean(
        related='checkbook_id.numerate_on_printing',
    )

    '''
    **************************************************************
    **************************************************************
    CHEQUES
    **************************************************************
    **************************************************************
    '''
    # payment_difference_handling = fields.Selection(
    #     selection_add=[
    #         ("reconcile_multi_deduct", "Mark invoice as fully paid (multi deduct)")
    #     ],
    #     ondelete={"reconcile_multi_deduct": "cascade"},
    # )
    # deduct_residual = fields.Monetary(
    #     string="Remainings", compute="_compute_deduct_residual"
    # )
    # deduction_ids = fields.One2many(
    #     comodel_name="account.payment.deduction",
    #     inverse_name="payment_id",
    #     string="Deductions",
    #     copy=False,
    #     help="Sum of deduction amount(s) must equal to the payment difference",
    # )

    @api.depends('payment_method_code')
    def _compute_check_type(self):
        for rec in self:
            if rec.payment_method_code == 'issue_check':
                rec.check_type = 'issue_check'
            elif rec.payment_method_code in [
                    'received_third_check',
                    'delivered_third_check']:
                rec.check_type = 'third_check'

    @api.constrains('check_ids')
    @api.onchange('check_ids', 'payment_method_code')
    def onchange_checks(self):
        for rec in self:
            # we only overwrite if payment method is delivered
            if rec.payment_method_code == 'delivered_third_check':
                rec.amount = sum(rec.check_ids.mapped('amount'))
                currency = rec.check_ids.mapped('currency_id')

                if len(currency) > 1:
                    raise ValidationError(_(
                        'You are trying to deposit checks of difference'
                        ' currencies, this functionality is not supported'))
                elif len(currency) == 1:
                    rec.currency_id = currency.id

    def _get_namecheck_from_number(self, number):
        padding = 8
        if len(str(number)) > padding:
            padding = len(str(number))
        return ('%%0%sd' % padding % number)

    @api.onchange('check_number')
    def _change_check_number(self):
        # TODO make default padding a parameter
        for rec in self:
            if rec.payment_method_code in ['received_third_check']:
                if not rec.check_number:
                    check_name = False
                else:
                    check_name = self._get_namecheck_from_number(rec.check_number)
                rec.check_name = check_name
            elif rec.payment_method_code in ['issue_check']:
                sequence = rec.checkbook_id.sequence_id
                if not rec.check_number:
                    check_name = False
                elif sequence:
                    if rec.check_number != sequence.number_next_actual:
                        # write with sudo for access rights over sequence
                        sequence.sudo().write(
                            {'number_next_actual': rec.check_number})
                    check_name = rec.checkbook_id.sequence_id.next_by_id()
                else:
                    # in sipreco, for eg, no sequence on checkbooks
                    check_name = self._get_namecheck_from_number(rec.check_number)
                rec.check_name = check_name


    @api.onchange('partner_id', 'payment_method_code')
    def onchange_partner_check(self):
        commercial_partner = self.partner_id.commercial_partner_id
        if self.payment_method_code == 'received_third_check':
            self.check_bank_id = (
                    commercial_partner.bank_ids and
                    commercial_partner.bank_ids[0].bank_id or False)
            # en realidad se termina pisando con onchange_check_owner_vat
            # entonces llevamos nombre solo si ya existe la priemr vez
            # TODO ver si lo mejoramos o borramos esto directamente
            # self.check_owner_name = commercial_partner.name
            vat_field = 'vat'
            # to avoid needed of another module, we add this check to see
            # if l10n_ar cuit field is available
            if 'cuit' in commercial_partner._fields:
                vat_field = 'cuit'
            self.check_owner_vat = commercial_partner[vat_field]
        elif self.payment_method_code == 'issue_check':
            self.check_bank_id = self.journal_id.bank_id
            self.check_owner_name = False
            self.check_owner_vat = False
        # no hace falta else porque no se usa en otros casos

    @api.onchange('payment_method_code')
    def _onchange_payment_method_code(self):
        # Todo comento para que no cambie

        self.check_ids = False

    @api.onchange('checkbook_id')
    def _onchange_checkbook(self):
        for rec in self:
            if rec.checkbook_id and not rec.checkbook_id.numerate_on_printing:
                rec.check_number = rec.checkbook_id.next_number
            else:
                rec.check_number = False

    def action_create_payments(self):
        for rec in self:
            if rec.check_ids and not rec.currency_id.is_zero(
                    sum(rec.check_ids.mapped('amount')) - rec.amount):
                raise UserError(_(
                    'La suma del pago no coincide con la suma de los cheques '
                    'seleccionados. Por favor intente eliminar y volver a '
                    'agregar un cheque.'))
            if rec.payment_method_code == 'issue_check' and (
                    not rec.check_number or not rec.check_name):
                raise UserError(_(
                    'Para mandar a proceso de firma debe definir número '
                    'de cheque en cada línea de pago.\n'
                    '* ID del pago: %s') % rec.id)
        res = super().action_create_payments()

        return

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        check_vals = {
            'check_bank_id': self.check_bank_id.id,
            'check_owner_name': self.check_owner_name,
            'check_owner_vat': self.check_owner_vat,
            'check_number': self.check_number,
            'check_name': self.check_name,
            'check_subtype': self.check_subtype,
            'checkbook_id': self.checkbook_id.id,
            'check_issue_date': self.check_issue_date,
            'check_type': self.check_type,
            'check_payment_date': self.check_payment_date,
            'check_deposit_type':self.check_deposit_type,
            'check_ids':self.check_ids,
        }
        payment_vals.update(check_vals)
        return payment_vals

