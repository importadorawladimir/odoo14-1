from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError



class PosOrder(models.Model):
	_inherit = 'pos.order'

	@api.model
	def _process_order(self, order, draft, existing_order):

		result = super(PosOrder, self)._process_order(order, draft, existing_order)
		pos_order = self.browse(result)
		print('_process_order id: ', result)
		if pos_order.config_id.invoice_background and pos_order.partner_id and not pos_order.is_invoiced and pos_order.state == 'paid':
			pos_order.action_pos_order_invoice()
		return result


	@api.model
	def proccess_orders_to_invoices(self, limit=50, date=False, config=False):

		if date:
			date_init = "%s 00:00:00" % date
			date_end = "%s 23:59:59" % date

			if config:
				orders = self.search([('partner_id', '!=', False),
									  ('amount_total', '>', 0),
									  ('state', 'in', ['paid']),
									  ('is_invoiced', '=', False),
									  ('date_order', '>=', date_init),
									  ('date_order', '<=', date_end),
									  ('session_id.config_id', '=', config)], limit=limit, order="date_order asc")
			else:
				orders = self.search([('partner_id', '!=', False),
									  ('amount_total', '>', 0),
									  ('state', 'in', ['paid']),
									  ('is_invoiced', '=', False),
									  ('date_order', '>=', date_init),
									  ('date_order', '<=', date_end)], limit=limit, order="date_order asc")
		else:
			if config:
				orders = self.search([('partner_id', '!=', False),
									  ('amount_total', '>', 0),
									  ('state', 'in', ['paid']),
									  ('is_invoiced', '=', False),
									  ('session_id.config_id', '=', config)], limit=limit)
			else:
				orders = self.search([('partner_id', '!=', False),
									  ('amount_total', '>',0),
									  ('state', 'in', ['paid']),
									  ('is_invoiced', '=', False),], limit=limit, order="date_order asc")

		for ord in orders:
			ord.action_pos_order_invoice()
