##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
##############################################################################
#    Sistema FINAMSYS
#    2021-Manteiner Today Ekuasoft S.A
#
#    Collaborators of this module:
#    Coded by: Cristhian Luzon <@cristhian_70>
#    Planifyied by: Yordany Oliva
#
##############################################################################
from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def button_cancel_reconciliation(self):
        """ Delete operation of checks that are debited from statement
        """
        for st_line in self.filtered('move_name'):
            if st_line.journal_entry_ids.filtered(
                    lambda x:
                    x.payment_id.payment_reference == st_line.move_name):
                check_operation = self.env['account.check.operation'].search(
                    [('origin', '=',
                      'account.bank.statement.line,%s' % st_line.id)])
                check_operation.check_id._del_operation(st_line)
        return super(
            AccountBankStatementLine, self).button_cancel_reconciliation()

    def reconcile(self, lines_vals_list, to_check=False):
        """
        Si el move line de contrapartida es un cheque entregado, entonces
        registramos el debito desde el extracto en el cheque
        TODO: por ahora si se cancela la linea de extracto no borramos el
        debito, habria que ver si queremos hacer eso modificando la funcion de
        arriba directamente
        """
        check = False
        moves = super(AccountBankStatementLine, self).reconcile(
            lines_vals_list=lines_vals_list,to_check=to_check)
        payments = self.payment_ids
        if self.move_id.line_ids.full_reconcile_id.reconciled_line_ids.payment_id and self.move_id.line_ids.full_reconcile_id.reconciled_line_ids.payment_id.check_id:
            check = self.move_id.line_ids.full_reconcile_id.reconciled_line_ids.payment_id.check_id
            for ln in check:
                #HANDED PARA CHEQUES PROPIOS
                if ln.state == 'handed':
                    #TODO REVISAR SI CONCILIO CON DIARIO DE CHEQUERA
                    # ESTO MAS QUE TODO POR MANEJO
                    if ln.checkbook_id.debit_journal_id != self.statement_id.journal_id:
                        raise ValidationError(_(
                            'Para registrar el debito de un cheque desde el extracto, '
                            'el diario de la chequera y del extracto deben ser los mismos'
                        ))
                    if len(self.move_id.line_ids) != 2:
                        raise ValidationError(_(
                            'Para registrar el debito de un cheque desde el extracto '
                            'solo debe haber una linea de contrapartida'))
                    ln._add_operation('debited', self, date=self.date)
                    ln.write({'state':'debited'})
                # HOLDING PARA CHEQUES DE TERCEROS
        return moves
