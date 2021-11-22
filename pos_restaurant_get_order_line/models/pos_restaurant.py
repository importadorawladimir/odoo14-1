from odoo import api, fields, models
from itertools import groupby


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_order_lines(self, orders):
        """Add pos_order_lines to the orders.

        The function doesn't return anything but adds the results directly to the orders.

        :param orders: orders for which the order_lines are to be requested.
        :type orders: pos.order.
        """
        order_lines = self.env['pos.order.line'].search_read(
            domain=[('order_id', 'in', [to['id'] for to in orders])],
            fields=self._get_fields_for_order_line())

        if order_lines != []:
            self._get_pack_lot_lines(order_lines)

        extended_order_lines = []
        for order_line in order_lines:

            self.order_line_pos(order_line)

            if not 'pack_lot_ids' in order_line:
                order_line['pack_lot_ids'] = []
            extended_order_lines.append([0, 0, order_line])

        for order_id, order_lines in groupby(extended_order_lines, key=lambda x: x[2]['order_id']):
            next(order for order in orders if order['id'] == order_id[0])['lines'] = list(order_lines)


    def order_line_pos(self, order_line):
        order_line['product_id'] = order_line['product_id'][0]
        order_line['server_id'] = order_line['id']