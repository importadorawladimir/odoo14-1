# -*- coding: utf-8 -*-
#
#    Sistema FINAMSYS
#    Copyright (C) 2016-Today Ekuasoft S.A All Rights Reserved
#    Ing. Yordany Oliva Mateos <yordanyoliva@ekuasoft.com>
#    Ing. Wendy Alvarez Chavez <wendyalvarez@ekuasoft.com>
#    EkuaSoft Software Development Group Solution
#    http://www.ekuasoft.com
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

{
    'name' : 'Ekuasoft Purchase Import Liquidation',
    'version' : '15.0.1.0',
    'author' : 'EkuaSoft Software Development Group Solution',
    'category': 'Import',
    'complexity': 'normal',
    'website': 'http://www.ekuasoft.com',
    'license': 'OPL-1',
    'data': [
        'data/ek_purchase_import_liquidation.xml',
        'data/data_import_liquidation.xml',
        'data/ek.country.port.csv',
        'security/purchase_import_liquidation_security.xml',
        'view/menu_config.xml',
        'view/tariff_heading_view.xml',
        'view/product_product.xml',
        'view/incoterms_view.xml',
        'wizard/ek_asigned_remove_invoice_view.xml',
        'wizard/ek_import_generate_invoice_view.xml',
        'view/ek_import_liquidation_view.xml',
        'view/purchase_view.xml',
        'view/partner_view.xml',
        'view/account_move_view.xml',
        'wizard/ek_import_generate_order_view.xml',
        #'report/report_purchaseorder.xml',
        'report/consolidate_tariff_report.xml',
        'security/ir.model.access.csv',
    ],
    'depends' : [
        'base',
        'stock',
        'stock_account',
        'purchase',
        'purchase_stock',
        'purchase_discount',
    ],
    'js': [
    ],
    'qweb': [
    ],
    'css': [
    ],
    'test': [
    ],
    'demo' : [
        #'demo/authorization_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
