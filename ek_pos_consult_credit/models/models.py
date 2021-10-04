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

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def get_credit_notes_by_client(self, client):
        """
        Get debt details

        :param int limit: max number of records to return
        :return: dictionary with keys:
             * partner_id: partner identification
             * debt: current debt
             * debts: dictionary with keys:

                 * balance
                 * journal_id: list

                    * id
                    * name
                    * code

             * records_count: total count of records
             * history: list of dictionaries

                 * date
                 * config_id
                 * balance
                 * journal_code

        """
        print(client)
        return {'creditlines': [{'name':'CREDITO','date':'26/06/1989','balance':40},
                                {'name':'CREDITO 2','date':'27/06/1989','balance':60}
                                ],
                                'total_balance':100}
        fields = [
            "date",
            "config_id",
            "order_id",
            "move_id",
            "balance",
            "product_list",
            "journal_id",
            "partner_id",
        ]
        debt_journals = self.env["account.journal"].search([("debt", "=", True)])
        data = {
            id: {
                "history": [],
                "partner_id": id,
                "debt": 0,
                "records_count": 0,
                "debts": {
                    dj.id: {
                        "balance": 0,
                        "journal_id": [dj.id, dj.name],
                        "journal_code": dj.code,
                    }
                    for dj in debt_journals
                },
            }
            for id in self.ids
        }

        records = self.env["report.pos.debt"].read_group(
            domain=[
                ("partner_id", "in", self.ids),
                ("journal_id", "in", debt_journals.ids),
            ],
            fields=fields,
            groupby=["partner_id", "journal_id"],
            lazy=False,
        )
        for rec in records:
            partner_id = rec["partner_id"][0]
            data[partner_id]["debts"][rec["journal_id"][0]]["balance"] = rec["balance"]
            data[partner_id]["records_count"] += rec["__count"]
            # -= due to it's debt, and balances per journals are credits
            data[partner_id]["debt"] -= rec["balance"]


        for partner_id in self.ids:
            data[partner_id]["history"] = self.env["report.pos.debt"].search_read(
                domain=[("partner_id", "=", partner_id)],
                fields=fields
            )
            for rec in data[partner_id]["history"]:
                rec["date"] = self._get_date_formats(rec["date"])
                rec["journal_code"] = data[partner_id]["debts"][
                    rec["journal_id"][0]
                ]["journal_code"]

        return data
