# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Ekuasoft Retentions for Ecuador',
    'version': '3.5',
    'description': '''


Authors:
    Yordany Oliva Mateos <yomateo870130@gmail.com>
    ''',
    'author': 'Ekuasoft Group Solutions',
    'category': 'Localization',
    'maintainer': 'Ekuasoft Group Solutions S.A',
    'website': 'http://www.ekuasoft.com',
    'license': 'OEEL-1',
    'depends': [
        'ek_l10n_ec',
        'account',
        'l10n_latam_invoice_document',
        'ek_l10n_latam_invoice_document'
    ],   
    'data': [
        'data/account_ats_sustento.xml',
        'views/account_retention_view.xml',
        'views/account_move_view.xml',
        'views/account_journal_view.xml',
        'views/account_retention_client_view.xml',
        'views/account_ats_sustento_view.xml',
        'wizards/account_move_reversal_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_ec_withdrawing_security.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
