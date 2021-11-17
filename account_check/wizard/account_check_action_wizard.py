##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
##############################################################################
#    Sistema FINAMSYS
#    2021-Manteiner Today Ekuasoft S.A
#
#    Collaborators of this module:
#    Coded by: Cristhian Luzon <@cristhian_70>
#    Planifyied by: Yordany Oliva
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountCheckActionWizard(models.TransientModel):
    _name = 'account.check.action.wizard'
    _description = 'Account Check Action Wizard'

    def _get_has_expense(self):
        checks = self.env['account.check'].browse(
            self._context.get('active_ids'))
        if checks.type and checks.type == 'issue_check':
            return False
        if checks.state not in ['deposited', 'selled']:
            return False
        return True

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )
    journal_id = fields.Many2one('account.journal', string='Diario')

    action_type = fields.Char(
        'Action type passed on the context',
        required=True,
    )
    create_debit_note = fields.Boolean(string="Crear Nota de Debito", )

    # NEW RECHAZO DE CHEQUES
    journal_reject_id = fields.Many2one('account.journal', string='Diario')
    reject_date = fields.Date(
        'Fecha de Rechazo', required=True, default=fields.Date.context_today)
    expense_account = fields.Many2one(
        'account.account',
        'Cuenta de Gasto',
        domain=[('type', 'in', ['other'])],
    )
    has_expense = fields.Boolean(
        'Tiene Gastos?', default=_get_has_expense)
    expense_amount = fields.Float(
        'Monto de Gasto')
    expense_to_customer = fields.Boolean(
        'Facturar Gastos al Cliente')

    invoice_check_value = fields.Boolean('Factura por el valor del cheque')
    # TODO ver si usar documento interno o agregar tipo de documento
    internal_invoice = fields.Boolean('Realizar documento Interno', default=False)
    internal_expense_to_doc = fields.Boolean(u'Realizar documento interno al gasto', default=False)

    # reason_id = fields.Many2one("ek.reasons.internal.documents", "Motivo/Concepto")

    l10n_latam_available_document_type_ids = fields.Many2many('l10n_latam.document.type',
                                                              compute='_compute_l10n_latam_available_document_types')

    l10n_latam_use_documents = fields.Boolean(related='journal_reject_id.l10n_latam_use_documents')

    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Tipo de Documento', readonly=False, auto_join=True, index=True,
        compute='_compute_l10n_latam_document_type', store=True)

    # @api.onchange('invoice_check_value')
    # def _onchange_check(self):
    #     if not self.invoice_check_value:
    #         self.internal_invoice = False
    #     if self.invoice_check_value:
    #         self.internal_expense_to_doc = False



    def _get_l10n_latam_documents_domain(self):
        '''
        AQUI VALIDAR SI ES OUT INVOICE O OTHER CON EL CHECK DE INTERNAL DOCUMENT

        :return:
        '''
        domain = []
        if self.internal_invoice:
            domain.append(('l10n_ec_type', 'in', ['other']))

        else:
            domain.append(('l10n_ec_type', 'in', ['out_invoice', 'in_invoice']))

        if domain:
            domain.append(('country_id', '=', self.env.user.company_id.country_id.id))

        return domain

    @api.depends('journal_reject_id')
    def _compute_l10n_latam_available_document_types(self):
        '''
        DOMAIN DE JOURNAL REVISAR para ver si solo saco los purchase and sale

        :return:
        '''
        self.l10n_latam_available_document_type_ids = False
        for rec in self.filtered(lambda x: x.journal_reject_id and x.l10n_latam_use_documents):
            rec.l10n_latam_available_document_type_ids = self.env['l10n_latam.document.type'].search(
                rec._get_l10n_latam_documents_domain())

    @api.depends('l10n_latam_available_document_type_ids')
    def _compute_l10n_latam_document_type(self):

        for rec in self:
            document_types = rec.l10n_latam_available_document_type_ids._origin
            document_types = document_types
            rec.l10n_latam_document_type_id = document_types and document_types[0].id

    def action_confirm(self):
        self.ensure_one()
        if self.action_type not in [
            'claim', 'bank_debit', 'bank_deposit', 'reject', 'customer_return']:
            raise ValidationError(_(
                'Action %s not supported on checks') % self.action_type)
        checks = self.env['account.check'].browse(
            self._context.get('active_ids'))
        for check in checks:
            if self.action_type == 'bank_deposit':
                res = check.bank_deposit(date=self.date, journal_id=self.journal_id)

            # REVISAR SI LO HACEMOS AL RECHAZAR!!!
            elif (self.action_type == 'reject' and check.type == 'third_check'):
                # TODO ENVIAR POR CONTEXT
                return getattr(
                    checks.with_context(reject_date=self.date,
                                        expense_account=self.expense_account,
                                        has_expense=self.has_expense,
                                        expense_amount=self.expense_amount,
                                        expense_to_customer=self.expense_to_customer,
                                        invoice_check_value=self.invoice_check_value,
                                        internal_invoice=self.internal_invoice,
                                        internal_expense_to_doc=self.internal_expense_to_doc,
                                        l10n_latam_document_type_id=self.l10n_latam_document_type_id,
                                        journal_reject_id=self.journal_reject_id,
                                        action_date=self.date,
                                        ), self.action_type)()


            else:
                res = getattr(
                    check.with_context(action_date=self.date,
                                       journal_id=self.journal_id,
                                       create_debit_note=self.create_debit_note),
                    self.action_type)()
        if len(checks) == 1:
            return res
        else:
            return True
