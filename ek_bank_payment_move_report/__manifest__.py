# -*- coding: utf-8 -*-
{
    'name': 'EkuaSoft Bank Payment Move Report',
    'version': '0.1',
    "category": 'Generic Modules/Accounting',
    'author': 'Ekuasoft Group Solutions',
    'summary': 'Internal notes of debit and credit',
    "website": "http://www.ekuasoft.com",
    "description": """
Reporte de movimientos bancarios
""",

    'depends': ['base','account','account_check','ek_bank_notes'],
    'data': [
        'views/assets.xml',
        'report/payment_history_detail_report.xml',
        'wizard/account_payment_wizard_view.xml',
        'views/bank_payment_move_view.xml',
        'security/ir.model.access.csv',
        #'security/ek_bank_notes_security.xml'
    ],
    'qweb': [
        "static/src/xml/payment_history_dashboard.xml",
    ],
    'test': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'init_data_payments_hook'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
