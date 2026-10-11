# LibreFleet Stock: service orders take their parts from real stock.
# Written in the Inventory deep dive, chapters 13 and 14.
{
    "name": "LibreFleet Stock",
    "summary": "Consume spare parts from stock when a service order is done",
    "version": "19.0.1.1.0",
    "category": "Services",
    "author": "Odoolings readers",
    "website": "https://odoolings.ronit.io/",
    "license": "AGPL-3",
    "development_status": "Beta",
    # the bridge pattern: librefleet keeps working without stock, this module joins them
    "depends": ["librefleet", "stock"],
    "data": [
        "data/stock_location.xml",
        "data/product_removal.xml",
        "report/report_deliveryslip.xml",
        "views/product_template_views.xml",
        "views/part_views.xml",
        "views/service_order_views.xml",
    ],
    "installable": True,
}
