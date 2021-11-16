from odoo import api, fields, models
from odoo.tools import float_is_zero, float_compare
from itertools import groupby


class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_multi_uom = fields.Boolean('Product multi UOM', default=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_multi_uom = fields.Boolean('Has multi UOM')
    show_all_uom = fields.Boolean('Show All UOM in POS')
    allow_uoms = fields.Many2many("uom.uom", "product_tmpl_uom", "product_tmpl_id", "product_uom_id", string="Allow UOMS")
    uom_category_id = fields.Many2one("uom.category", related='uom_id.category_id')


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    product_uom = fields.Many2one('uom.uom', 'Unit of measure')

    def _order_line_fields(self, line, session_id=None):
        line = super(PosOrderLine, self)._order_line_fields(line, session_id)
        if line[2].get("product_uom", False) and isinstance(line[2]["product_uom"], dict):
            line[2]["product_uom"] = line[2]["product_uom"]["id"]
        return line


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_fields_for_order_line(self):
        res = super(PosOrder, self)._get_fields_for_order_line()
        res += ['product_uom']
        return res

    def order_line_pos(self, order_line):
        if order_line['product_uom']:
            product_uom = self.env['uom.uom'].browse(order_line['product_uom'][0])
            product_uom_fields = {
                "id": product_uom.id,
                "name": product_uom.name,
                "category_id": [product_uom.category_id.id, product_uom.category_id.name],
                "factor": product_uom.factor,
                "factor_inv": product_uom.factor_inv,
            }
            order_line['product_uom'] = product_uom_fields
        res = super(PosOrder, self).order_line_pos(order_line)
        return res

    def _prepare_invoice_line(self, order_line):
        values = super(PosOrder, self)._prepare_invoice_line(order_line)
        values['product_uom_id'] = order_line.product_uom.id or order_line.product_uom_id.id
        return values


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        return {
            'name': first_line.name,
            'product_uom': first_line.product_uom.id or first_line.product_id.uom_id.id,
            'picking_id': self.id,
            'picking_type_id': self.picking_type_id.id,
            'product_id': first_line.product_id.id,
            'product_uom_qty': abs(sum(order_lines.mapped('qty'))),
            'state': 'draft',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'company_id': self.company_id.id,
        }

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda d: d.product_uom.id or d.product_id.id)
        for product, lines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*lines)
            first_line = order_lines[0]
            current_move = self.env['stock.move'].create(
                self._prepare_stock_move_vals(first_line, order_lines)
            )
            confirmed_moves = current_move._action_confirm()
            for move in confirmed_moves:
                if first_line.product_id == move.product_id and first_line.product_id.tracking != 'none':
                    if self.picking_type_id.use_existing_lots or self.picking_type_id.use_create_lots:
                        for line in order_lines:
                            sum_of_lots = 0
                            for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                                if line.product_id.tracking == 'serial':
                                    qty = 1
                                else:
                                    qty = abs(line.qty)
                                ml_vals = move._prepare_move_line_vals()
                                ml_vals.update({'qty_done': qty})
                                if self.picking_type_id.use_existing_lots:
                                    existing_lot = self.env['stock.production.lot'].search([
                                        ('company_id', '=', self.company_id.id),
                                        ('product_id', '=', line.product_id.id),
                                        ('name', '=', lot.lot_name)
                                    ])
                                    if not existing_lot and self.picking_type_id.use_create_lots:
                                        existing_lot = self.env['stock.production.lot'].create({
                                            'company_id': self.company_id.id,
                                            'product_id': line.product_id.id,
                                            'name': lot.lot_name,
                                        })
                                    quant = existing_lot.quant_ids.filtered(
                                        lambda q: q.quantity > 0.0 and q.location_id.parent_path.startswith(move.location_id.parent_path))[-1:]
                                    ml_vals.update({
                                        'lot_id': existing_lot.id,
                                        'location_id': quant.location_id.id or move.location_id.id
                                    })
                                else:
                                    ml_vals.update({
                                        'lot_name': lot.lot_name,
                                    })
                                self.env['stock.move.line'].create(ml_vals)
                                sum_of_lots += qty
                            if abs(line.qty) != sum_of_lots:
                                difference_qty = abs(line.qty) - sum_of_lots
                                ml_vals = current_move._prepare_move_line_vals()
                                if line.product_id.tracking == 'serial':
                                    ml_vals.update({'qty_done': 1})
                                    for i in range(int(difference_qty)):
                                        self.env['stock.move.line'].create(ml_vals)
                                else:
                                    ml_vals.update({'qty_done': difference_qty})
                                    self.env['stock.move.line'].create(ml_vals)
                    else:
                        move._action_assign()
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                        if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=move.product_uom.rounding) > 0:
                            remaining_qty = move.product_uom_qty - move.quantity_done
                            ml_vals = move._prepare_move_line_vals()
                            ml_vals.update({'qty_done': remaining_qty})
                            self.env['stock.move.line'].create(ml_vals)

                else:
                    move._action_assign()
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                    if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=move.product_uom.rounding) > 0:
                        remaining_qty = move.product_uom_qty - move.quantity_done
                        ml_vals = move._prepare_move_line_vals()
                        ml_vals.update({'qty_done': remaining_qty})
                        self.env['stock.move.line'].create(ml_vals)
                    move.quantity_done = move.product_uom_qty
