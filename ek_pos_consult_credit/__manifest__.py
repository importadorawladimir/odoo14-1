# Copyright 2021 Groupsolitions
# License MIT (https://opensource.org/licenses/MIT).
{
    "name": "POS: Consulta de Deuda",
    "summary": "Consulta de Deuda POS",
    "category": "Point Of Sale",
    "images": ["images/debt_notebook.png"],
    "version": "14.0.5.3.4",
    "author": "Groupsolutions",
    "support": "cristhianclv70",
    "website": "/",
    "license": "",  # MIT
    "external_dependencies": {"python": [], "bin": []},
    "depends": ["point_of_sale"],
    "data": [
        "views/custom_pos_view.xml",
        "data.xml",
    ],
    "qweb": [

        "static/src/xml/ek_consultcreditWidget.xml",
        "static/src/xml/pos.xml",
    ],
    "demo": [],
    "installable": True,

}
