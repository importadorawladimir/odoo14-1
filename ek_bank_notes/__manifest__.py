# -*- coding: utf-8 -*-
{
    'name': 'EkuaSoft Bank Notes',
    'version': '0.1',
    "category": 'Generic Modules/Accounting',
    'author': 'Ekuasoft Group Solutions',
    'summary': 'Internal notes of debit and credit',
    "website": "http://www.ekuasoft.com",
    "description": """
EkuaSoft Bank Notes (debit and credit)
""",

    'depends': ['base','account'],
    'data': [

        'views/bank_notes_view.xml',
        'security/ir.model.access.csv',
        'security/ek_bank_notes_security.xml'
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
