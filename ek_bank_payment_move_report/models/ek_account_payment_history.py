from odoo import fields, models, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'
    #bank_report_day
    def bank_report_day(self):
        active_id = self._context.get('active_id')

        return {
            'name': 'Reporte Bancario Detallado',
            'type': 'ir.actions.act_window',
            'res_model': 'ek.account.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_journal_id': self.id
            },
        }

    payment_history_ids = fields.One2many(
        comodel_name='ek.account.payment.history',
        inverse_name='journal_id',
        string='Historial',
        required=False)


class ek_bank_notes(models.Model):
    _inherit = 'ek.bank.notes'

    def action_confirmed(self):
        for rec in self:
            _acction_previos = rec.state
            res = super(ek_bank_notes, rec).action_confirmed()
            rec._register_payment_history('posted')

    def action_cancel(self):
        for rec in self:
            _acction_previos = rec.state

            res = super(ek_bank_notes, rec).action_cancel()
            if _acction_previos != 'draft':
                rec._register_payment_history('cancel')

    def _register_payment_history(self,state):
        obj_history = self.env['ek.account.payment.history']
        for rec in self:
            obj_history.create({
                'name': rec.name,
                'partner_id': False,
                'date': rec.date,
                'payment_type': rec.type == 'ndb' and 'outbound' or 'inbound',
                'company_id': rec.company_id.id,
                'state': state,
                'amount': rec.amount_total,
                'ref': rec.reference,
                'journal_id': rec.journal_id.id,
                'payment_method_id': False,
                'payment_method_name': False,
                'is_bank_note': True,
                'type_bank_note': rec.type,
                'is_internal_transfer': False,
                'is_check': False,
                'check_type': False,
                'check_number': False,
                'check_bank_id': False,
                'check_payment_date': False,
                'check_id': False,
                'cancel_date': state == 'cancel' and fields.Date.context_today(self) or False,
                'doc_type': 'note'
            })

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_draft(self):
        for rec in self:
            _acction_previos = rec.state

            res  = super(AccountPayment, rec).action_draft()

            if _acction_previos != 'cancel':
                rec._register_payment_history('cancel')

        return
    def action_cancel(self):
        for rec in self:
            _acction_previos = rec.state

            res = super(AccountPayment, self).action_cancel()
            if _acction_previos != 'draft':
                rec._register_payment_history('cancel')


    def action_post(self):
        for rec in self:
            res = super(AccountPayment, rec).action_post()
            rec._register_payment_history('posted')



    def _register_payment_history(self,state):
        obj_history = self.env['ek.account.payment.history']
        for rec in self:
            obj_history.create({
                'name': rec.name,
                'partner_id': rec.partner_id and rec.partner_id.id or False,
                'date': rec.date,
                'payment_type': rec.payment_type,
                'company_id': rec.company_id.id,
                'state': state,
                'amount': rec.amount,
                'ref': rec.ref,
                'journal_id': rec.journal_id.id,
                'payment_method_id': rec.payment_method_id.id,
                'payment_method_name': rec.payment_method_id.name,
                'is_internal_transfer': rec.is_internal_transfer,
                'is_check': rec.check_id and True or False,
                'check_type': rec.check_id and rec.check_id.type or False,
                'check_number': rec.check_id and rec.check_id.name or False,
                #'check_state': rec.check_id and rec.check_id.state or False,
                'check_bank_id': rec.check_id and rec.check_id.bank_id.id or False,
                'check_payment_date': rec.check_id and rec.check_id.payment_date or False,
                'check_id': rec.check_id and rec.check_id.id or False,
                'cancel_date': state == 'cancel' and fields.Date.context_today(self) or False,
                'doc_type': rec.check_id and 'check' or 'deposit'
            })

class ek_account_payment_history(models.Model):
    _name = 'ek.account.payment.history'
    _description = 'Historial de transacciónes bancarias'
    _order = "date asc, id"

    @api.depends('amount','state','payment_type')
    def _compute_credit_and_debit(self):
        for rec in self:
            debit = 0
            credit = 0

            if rec.payment_type == 'outbound':
                if rec.state == 'posted':
                    credit = rec.amount
                else:
                    debit = rec.amount
            else:
                if rec.state == 'posted':
                    debit = rec.amount
                else:
                    credit = rec.amount

            rec.debit = debit
            rec.credit = credit
            rec.balance = 0


    name = fields.Char('No.',readonly=True, required=False)

    partner_id = fields.Many2one('res.partner', u'Cliente/Proveedor', readonly=True, required=False)

    date = fields.Date(string="Fecha",readonly=True, required=False)
    company_id = fields.Many2one('res.company', u'Compañía', default=lambda self: self.env.company,readonly=True, required=False)

    state = fields.Selection(string="Estado",
                             selection=[('posted', 'Publicado'), ('cancel', 'Cancelado')],
                             readonly=True, required=False, default='confirmed')

    cancel_date = fields.Date(
        string='Fecha de Anulación',readonly=True, required=False)
    amount = fields.Monetary(string='Importe', digits_compute='Account',readonly=True, required=False)

    credit = fields.Monetary(string='Credito', digits_compute='Account', compute="_compute_credit_and_debit",readonly=True, required=False, store=True)
    debit = fields.Monetary(string='Debito', digits_compute='Account', compute="_compute_credit_and_debit",readonly=True, required=False, store=True)
    balance = fields.Monetary(string='Saldo', digits_compute='Account', compute="_compute_credit_and_debit",readonly=True, required=False, store=True)

    currency_id = fields.Many2one(
        'res.currency',readonly=True, required=False, string="Moneda",
        default=lambda self: self.env.user.company_id.currency_id.id
    )

    payment_type = fields.Selection(
        string='Tipo',
        selection=[('outbound', 'Pago'),
                   ('inbound', 'Cobro'), ],readonly=True, required=False )

    doc_type = fields.Selection(
        string='Tipo Doc.',
        selection=[('deposit', 'Deposito'),
                   ('check', 'Cheque'),
                   ('note', 'Nota Bancaria'), ], readonly=True, required=False, default='deposit')
        
    ref = fields.Char(
        string='Memo',readonly=True, required=False)

    journal_id = fields.Many2one('account.journal', string='Diario',readonly=True, required=False)

    payment_method_id = fields.Many2one('account.payment.method', string=u'Ref. Método de pago',readonly=True, required=False)
    payment_method_name = fields.Char(string=u'Método de pago',readonly=True, required=False)

    is_internal_transfer = fields.Boolean(
        string='Es transferencia interna',readonly=True, required=False)

    is_check = fields.Boolean(
        string='Es Cheque',readonly=True, required=False)

    is_bank_note = fields.Boolean(
        string='Es Nota Bancaria', readonly=True, required=False)

    type_bank_note = fields.Selection(string="Tipo Nota Bancaria",
                            selection=[('ndb', u'Nota de Débito Bancaria'), ('ncb', u'Nota de Crédito Bancaria'), ],
                            required=False, readonly=True)

    check_number = fields.Char(
        string='No. Cheque',readonly=True, required=False)

    check_type = fields.Selection([('issue_check', 'Cheque Propio'),
                             ('third_check', 'Cheque de Terceros')],readonly=True, required=False,
                            index=True, string='Tipo de Cheque'
                            )
    check_state = fields.Selection([
        ('draft', 'Borrador'),
        ('holding', 'En Mano'),
        ('deposited', 'Depositado'),
        ('selled', 'Vendido'),
        ('delivered', 'Entregado/Endoso'),  # Endoso
        ('transfered', 'Transferido'),
        ('reclaimed', 'Reclamado'),
        ('withdrawed', 'Retirado'),
        ('handed', 'Entregado'),
        ('rejected', 'Rechazado'),
        ('debited', 'Debitado'),
        ('returned', 'Devuelto'),
        ('changed', 'Cambiado'),
        ('cancel', 'Cancelado'),

    ],
        string='Estado de Cheque', index=True,readonly=True, required=False,
        related="check_id.state"
    )
    check_bank_id = fields.Many2one(
        'res.bank', 'Banco',readonly=True, required=False
    )

    check_payment_date = fields.Date(
        string='Fecha de Pago',readonly=True, required=False,
        index=True,
    )

    check_id = fields.Many2one(
        'account.check',
        'Cheque',
        readonly=True, required=False,
        ondelete='cascade',
        auto_join=True,
        index=True,
    )

    user = fields.Char(
        comodel_name="res.users",
        default = lambda self: self.env.user.name,
        string='Usuario'
    )

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        self.check_access_rights('read')

        result = {
            'nc': 0,
            'nd': 0,
            'check_today': 0,
            'check_issue': 0,
            'initial_balance': 0,
            'balance': 0,
            'my_waiting': 0,
            'my_late': 0,
            'all_avg_order_value': 0,
            'today': fields.Date.from_string(fields.Date.context_today(self)),
            'all_total_last_7_days': 0,
            'all_sent_rfqs': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }

        history = self.env['ek.account.payment.history']

        nc = 0
        nd = 0
        check_today = 0.00
        deposit = 0.00
        initial_balance = 0
        balance=0
        data_history = history.search([('journal_id.type','in',['bank'])],order='date asc')
        for rec in data_history:
            balance+= (rec.debit - rec.credit)
            #Calculos del dia
            if rec.date >= fields.Date.context_today(self):
                if rec.is_bank_note:
                    if rec.type_bank_note == 'ndb':
                        nd+=(rec.credit - rec.debit)
                    else:
                        nc+=(rec.credit - rec.debit)
                elif rec.is_check:
                    if rec.check_type == 'issue_check' and rec.date == fields.Date.context_today(self):
                        check_today+=(rec.credit - rec.debit)
                else:
                    if rec.payment_type == 'inbound':
                        deposit+=(rec.debit - rec.credit)
            else:
                initial_balance += (rec.debit - rec.credit)
        result.update({
            'nc': '{:.2f}'.format(abs(nc)),
            'nd': '{:.2f}'.format(abs(nd)),
            'check_today': '{:.2f}'.format(check_today),
            'deposit': '{:.2f}'.format(deposit),
            'initial_balance': '{:.2f}'.format(initial_balance),
            'balance': '{:.2f}'.format(balance),
        })
        check_handed_count = 0.00
        check_handed_amount = 0.00
        check_holding_count = 0.00
        check_holding_amount = 0.00
        for check in self.env['account.check'].search([('state','in',['handed','holding'])]):
            if check.state == 'handed':
                check_handed_count +=1
                check_handed_amount += check.amount
            else:
                check_holding_count +=1
                check_holding_amount  += check.amount

        result.update({
            'check_handed_count': check_handed_count,
            'check_handed_amount': '{:.2f}'.format(check_handed_amount),
            'check_holding_count': check_holding_count,
            'check_holding_amount': '{:.2f}'.format(check_holding_amount)
        })

        return result


    def action_duplicate(self):
        return True