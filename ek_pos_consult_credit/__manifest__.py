# Copyright 2021 Denis Mudarisov <https://github.com/trojikman>
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
        # "security/pos_debt_notebook_security.xml",

        "views/custom_pos_view.xml",
        # "views.xml",
        # "views/pos_credit_update.xml",
        # "wizard/pos_credit_invoices_views.xml",
        # "wizard/pos_credit_company_invoices_views.xml",
        "data.xml",
        # "security/ir.model.access.csv",
    ],
    "qweb": [
        # "static/src/xml/CreditNote.xml",
        # "static/src/xml/OrderReceipt.xml",
        # "static/src/xml/PaymentMethodButton.xml",
        "static/src/xml/ek_consultcreditWidget.xml",
        "static/src/xml/pos.xml",
    ],
    "demo": [],
    "installable": True,

}
