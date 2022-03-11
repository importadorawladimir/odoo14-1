# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    l10n_latam_document_sustento = fields.Many2one(
        comodel_name='account.ats.sustento',
        string='Sustento',
        required=False)

    l10n_latam_document_auth = fields.Char(
        string=u'Número de Autorización')

    def _prepare_default_reversal(self, move):
        """ Set the default document type and number in the new revsersal move taking into account the ones selected in
        the wizard """
        res = super()._prepare_default_reversal(move)
        res.update({
            'l10n_latam_document_sustento': self.l10n_latam_document_sustento.id,
            'l10n_latam_document_auth': self.l10n_latam_document_auth,
            'l10n_latam_document_sustento_id': len(self.move_ids) and self.move_ids[0].id or False
        })
        return res