# LibreFleet: the Odoolings capstone.
# Built chapter by chapter across the tutorial.
{
    "name": "LibreFleet",
    "summary": "Vehicle workshop & service booking management",
    "version": "19.0.1.30.0",
    "category": "Services",
    "author": "Odoolings readers",
    "website": "https://odoolings.ronit.io/",
    "license": "AGPL-3",
    # ch44: honest self-assessment, not the silent default. Declare it rather
    # than let every reader of the manifest wonder whether it was forgotten.
    "development_status": "Beta",
    "application": True,
    "depends": ["base", "product", "mail", "web", "portal"],
    "data": [
        "security/librefleet_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/mail_template.xml",
        "data/service_type_master.xml",
        "report/service_order_report.xml",
        "views/website_templates.xml",
        "views/portal_templates.xml",
        "views/vehicle_views.xml",
        "views/vehicle_views_inherit.xml",
        "views/service_type_views.xml",
        "views/service_order_views.xml",
        "views/part_views.xml",
        "views/loaner_views.xml",
        "views/res_partner_views.xml",
        "views/librefleet_menus.xml",
        # after the menus file: the dashboard menu's parent lives there
        "views/dashboard_views.xml",
        "wizards/service_order_approve_views.xml",
    ],
    "demo": [
        "data/res.partner-demo.csv",
        "data/librefleet.vehicle-demo.csv",
        "data/service_order_demo.xml",
    ],
    # ch39: assets are their own manifest key, NOT part of "data". The bundle
    # name decides where the code loads: assets_backend is the web client only.
    "assets": {
        "web.assets_backend": [
            "librefleet/static/src/**/*.js",
            "librefleet/static/src/**/*.xml",
        ],
    },
}
