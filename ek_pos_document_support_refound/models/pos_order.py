from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError



class PosOrder(models.Model):
	_inherit = 'pos.order'

	l10n_latam_document_sustento_id = fields.Many2one('account.move', string='Doc. Sustento', copy=False, readonly=True)

	def _prepare_invoice_vals(self):
		self.ensure_one()
		rec = super(PosOrder, self)._prepare_invoice_vals()

		rec.update({
			'l10n_latam_document_sustento_id': self.l10n_latam_document_sustento_id.id
		})

		return rec

	def _prepare_refund_values(self, current_session):
		self.ensure_one()
		rec = super(PosOrder, self)._prepare_refund_values(current_session)

		if not self.account_move:
			raise UserError("Antes debe generar la factura asociada a este pedido.")

		rec.update({
			'l10n_latam_document_sustento_id': self.account_move.id
		})

		return rec