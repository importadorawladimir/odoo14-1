from odoo import fields, models, api, SUPERUSER_ID


def init_data_payments_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    bankNotes = env['ek.bank.notes'].search([('state', '=', 'confirmed')])

    for notes in bankNotes:
        notes._register_payment_history('posted')

    payments = env['account.payment'].search([('state','=','posted')])

    for payment in payments:
        payment._register_payment_history('posted')


