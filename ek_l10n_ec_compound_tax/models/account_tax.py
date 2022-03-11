# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
import logging



class AccountCompoundTax(models.Model):
    _inherit = "account.tax"

    amount_type = fields.Selection(selection_add=[
        ('compound', 'Compuesto')
    ], ondelete={'compound': lambda recs: recs.write({'amount_type': 'percent', 'active': False})})

    compound_tax_ids = fields.Many2many('account.tax',
                                        'account_tax_compound_rel', 'parent_tax', 'child_tax',
                                        check_company=True,
                                        string='Impuestos Compuestos')

    @api.constrains('compound_tax_ids', 'type_tax_use')
    def _check_children_scope(self):
        for tax in self:
            if not tax._check_m2m_recursion('compound_tax_ids'):
                raise ValidationError(_("Recurrencia encontrada para impuestos '%s'.") % (tax.name,))
            if any(child.type_tax_use not in ('none', tax.type_tax_use) or child.tax_scope != tax.tax_scope for child in
                   tax.compound_tax_ids):
                raise ValidationError(
                    _(u'El ámbito de aplicación de los impuestos en un grupo debe ser el mismo que el del grupo o debe dejarse vacío.'))

    @api.onchange('amount_type')
    def onchange_amount_type_compound(self):
        if self.amount_type != 'compound':
            self.compound_tax_ids = [(5,)]
        if self.amount_type == 'compound':
            self.description = None

    def compute_all_compund(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False,
                    handle_price_include=True):
        tax = self
        for rec in self:
            company = self.env.company

            if rec.amount_type != 'compound':
                return super(AccountCompoundTax, rec).compute_all(price_unit, currency, quantity, product, partner,
                                                                  is_refund=is_refund,
                                                                  handle_price_include=handle_price_include)

            if product and product._name == 'product.template':
                product = product.product_variant_id

            tax_evals = rec.compound_tax_ids
           # if is_refund:
           #     tax_evals = self.refund_repartition_line_ids
           # else:
           #     tax_evals = self.invoice_repartition_line_ids
            if len(tax_evals) == 0:
                continue

            tax_init = tax_evals[0]

            compount_tax_init = tax_init.compute_all(price_unit, quantity=quantity, currency=currency, product=product, partner=partner,
                            is_refund=is_refund)

            price_unit = compount_tax_init['taxes'][0]['amount']

            result = {}
            total_excluded = 0.00
            total_included = 0.00
            total_void = 0.00
            base_tags = []
            taxes = {}
            for tax in tax_evals[1:len(tax_evals)]:

                result = tax.compute_all(price_unit,quantity=1, currency=currency, product=product, partner=partner, is_refund=is_refund)
                price_unit = result['taxes'][0]['amount']
                total_excluded = result['total_excluded']
                total_included = result['total_included']
                total_void = result['total_void']
                base_tags = result['base_tags']
                taxes = result['taxes']

            return taxes

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        self.ensure_one()
        if product and product._name == 'product.template':
            product = product.product_variant_id
        if self.amount_type == 'compound':
            company = self.env.company
            currency = company.currency_id

            resultx = self.compute_all_compund(price_unit, currency, quantity, product,partner,False,False)
            base_amount = resultx[0]['base']
            localdict = {'compund_amount': resultx[0]['amount'],'base_amount': base_amount, 'price_unit': price_unit, 'quantity': quantity, 'product': product,
                         'partner': partner, 'company': company}
            safe_eval("result = compund_amount", localdict, mode="exec", nocopy=True)
            return localdict['result']
        return super(AccountCompoundTax, self)._compute_amount(base_amount, price_unit, quantity, product, partner)

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False,
                    handle_price_include=True):
        taxes = self.filtered(lambda r: r.amount_type != 'compound')
        company = self.env.company
        if product and product._name == 'product.template':
            product = product.product_variant_id
        for tax in self.filtered(lambda r: r.amount_type == 'compound'):
            localdict = self._context.get('tax_computation_context', {})
            localdict.update({'price_unit': price_unit, 'quantity': quantity, 'product': product, 'partner': partner,
                              'company': company})
            safe_eval("result = True", localdict, mode="exec", nocopy=True)
            if localdict.get('result', False):
                taxes += tax
        return super(AccountCompoundTax, taxes).compute_all(price_unit, currency, quantity, product, partner,
                                                          is_refund=is_refund,
                                                          handle_price_include=handle_price_include)


