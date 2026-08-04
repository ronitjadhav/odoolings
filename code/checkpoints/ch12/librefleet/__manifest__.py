# LibreFleet: the Odoolings capstone.
# Built chapter by chapter; this file is the ch12 state.
{
    "name": "LibreFleet",
    "summary": "Vehicle workshop & service booking management",
    "version": "19.0.1.4.0",
    "category": "Services",
    "author": "Odoolings readers",
    "website": "https://odoolings.ronit.io/",
    "license": "AGPL-3",
    "application": True,
    "depends": ["base"],
    "data": [
        "security/librefleet_security.xml",
        "security/ir.model.access.csv",
        "views/vehicle_views.xml",
        "views/service_type_views.xml",
        "views/service_order_views.xml",
        "views/part_views.xml",
        "views/librefleet_menus.xml",
    ],

}
