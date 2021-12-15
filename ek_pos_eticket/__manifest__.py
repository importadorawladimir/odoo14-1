# -*- coding: utf-8 -*-
{
    "name": "POS eticket",
    "version": "14.0.1.0.0",
    "author": "Cristhian Luzon Ekuasoft.com",
    "license": "LGPL-3",
    "sequence": 14,
    "category": "Point Of Sale",
    "website": "https://www.ekuasoft.com",
    "depends": ["point_of_sale", "ek_l10n_ec",'l10n_ec_sri'],
    "data": [
        "views/pos_eticket.xml",
        "views/pos_config.xml",
    ],
    "qweb": [
        "static/src/xml/pos_ticket.xml",
    ],
    "installable": True,
}
