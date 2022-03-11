# -*- coding: utf-8 -*-
#    Copyright (C) 2007  pronexo.com  (https://www.pronexo.com)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################## # 
{
	'name': 'Pos Invoice Auto-Background',
	'summary': 'Creacion de facturas automaticas',
	'version': '14.0.3',
	'author': 'Groupsolitions',
    	'maintainer': 'Groupsolutions',
	'license': "AGPL-3",
	'maintainer': 'Cristhian Luzon Groupsolutions',
	'category': 'sale',
	'website': 'h',
	'depends': [
		'point_of_sale'
	],
	'data': [
		
		'views/pos_config_view.xml',
		# 'views/templates.xml'
	],
	'external_dependencies': {
   
    },
	'auto_install': False,
	'installable': True,
}
