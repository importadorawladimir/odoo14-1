# -*- coding: utf-8 -*-
##############################################################################
#    Sistema FINAMSYS
#    Copyright (C) 2019-Today Ekuasoft S.A All Rights Reserved
#
#    Collaborators of this module:
#    Coded by: Cristhian Luzon <@cristhian_70>
#    Planifyied by: Yordany Oliva
#   This project is mantained by Ekuasoft Group Solutions
##############################################################################
{
    'name': "Impresor Matricial via Proxy",

    'summary': 'Impresion desde la Web a Matricial',
    'description': """Este modulo permite imprimir desde la Web a una Maticial""",
    "author": "Cristhian Luzon",
    "company": 'Ekuasoft',
    "website": "https://ekuasoft.com",
    'maintainer': 'Ekuasoft',
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web',],

    # always loaded
    'data': [
        'views/assets.xml',

    ],

}