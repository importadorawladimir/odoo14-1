# Copyright 2014-2020 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2015 Alexis de Lattre <https://github.com/alexis-via>
# Copyright 2016-2017 Stanislav Krotov <https://it-projects.info/team/ufaks>
# Copyright 2016 Florent Thomas <https://it-projects.info/team/flotho>
# Copyright 2017 iceship <https://github.com/iceship>
# Copyright 2017 gnidorah <https://github.com/gnidorah>
# Copyright 2018-2020 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
# License MIT (https://opensource.org/licenses/MIT).

import copy
import logging

import pytz
from pytz import timezone

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def get_credit_notes_by_client(self, journal,partner):
        """

        """

        if not partner or  not partner.get('id',False) or partner is None:
            raise UserError("Es necesario definir un Cliente")

        domain = [('move_type', '=', 'out_refund'),
                  ("partner_id", "=", partner.get('id',False)),
                  # ("journal_id", "=", self.id),
                  ("payment_state","=","not_paid")]
        if journal:
            domain.append(("journal_id", "=", journal))
        credit_lines = []
        total_balance = 0.00
        credits = self.env["account.move"].search(domain)
        for line in credits:
            total_balance+=line.amount_total
            credit_lines.append({
                'name': line.name, 'date': line.invoice_date, 'balance': line.amount_total
            })

        return {'creditlines': credit_lines,
                                'total_balance':total_balance}
