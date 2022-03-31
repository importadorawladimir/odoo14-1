# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
from odoo.tools.misc import formatLang


class AccountMove(models.Model):

    _inherit = "account.move"

    l10n_latam_amount_untaxed_zero = fields.Monetary(compute='_compute_l10n_latam_amount_untaxed_zero', string=u"Base 0%")
    l10n_latam_amount_untaxed_not_zero = fields.Monetary(compute='_compute_l10n_latam_amount_untaxed_zero',
                                                     string=u"Base distinta de 0%")


    def _compute_l10n_latam_amount_untaxed_zero(self):
        recs_invoice = self.filtered(lambda x: x.is_invoice())
        for invoice in recs_invoice:
            base_zero = 0.00
            base_not_zero = 0.00

            if invoice.is_inbound():
                sign = 1
            else:
                sign = -1

            for line in invoice.invoice_line_ids:
                if len(line.tax_ids.filtered(lambda a: a.tax_group_id.l10n_ec_type in ('zero_vat', 'not_charged_vat', 'exempt_vat'))):
                    base_zero += line.price_subtotal

                if len(line.tax_ids.filtered(lambda a: a.tax_group_id.l10n_ec_type in('vat12', 'vat14','irbpnr'))):
                    base_not_zero += line.price_subtotal

            invoice.l10n_latam_amount_untaxed_zero = base_zero * sign
            invoice.l10n_latam_amount_untaxed_not_zero = base_not_zero * sign
