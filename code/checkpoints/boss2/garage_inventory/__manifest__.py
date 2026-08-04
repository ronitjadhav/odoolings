{
    "name": "Garage Inventory",
    "summary": "Track workshop parts stock: the Part 2 boss challenge.",
    "version": "19.0.1.0.0",
    "category": "Services",
    "author": "Odoolings reader",
    "website": "https://odoolings.ronit.io/",
    "license": "AGPL-3",
    "application": True,
    "depends": ["base"],
    "data": [
        "security/garage_security.xml",
        "security/ir.model.access.csv",
        "views/inventory_item_views.xml",
    ],
}
