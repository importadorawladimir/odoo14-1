{
    "name": "POS multi UOM product right",
    "version": "14.0.1.1.0",
    "author": "Ganemo",
    "website": "https://www.ganemo.co/",
    "summary": "This module allows you to modify the unit of measure used in the sale of products at the point of sale.",
    "description": """
    This module allows you to modify the unit of measure used in the sale of products at the point of sale.
    """,
    "category": "Point of Sale",
    "depends": [
        "pos_restaurant_get_order_line"
    ],
    'qweb': [
        'static/src/xml/pos_multi_uom_button.xml',
        'static/src/xml/pos_multi_uom_popup.xml',
    ],
    "data": [
        "views/pos.xml",
        "views/pos_assets.xml",
        "views/product.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "currency": "USD",
    "price": 39.90,
}
