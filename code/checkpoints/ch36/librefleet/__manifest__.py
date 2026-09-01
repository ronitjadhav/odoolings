# LibreFleet: the Odoolings capstone.
# Built chapter by chapter across the tutorial.
{
    "name": "LibreFleet",
    "summary": "Vehicle workshop & service booking management",
    "version": "19.0.1.22.0",
    "category": "Services",
    "author": "Odoolings readers",
    "website": "https://odoolings.ronit.io/",
    "license": "AGPL-3",
    "application": True,
    "depends": ["base", "product", "mail", "base_automation", "web"],
    "data": [
        "security/librefleet_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/mail_template.xml",
        "data/service_type_master.xml",
        "data/maintenance_reminder_cron.xml",
        "data/maintenance_reminder_automation.xml",
        "report/service_order_report.xml",
        "views/vehicle_views.xml",
        "views/vehicle_views_inherit.xml",
        "views/service_type_views.xml",
        "views/service_order_views.xml",
        "views/part_views.xml",
        "views/loaner_views.xml",
        "views/res_partner_views.xml",
        "views/librefleet_menus.xml",
        "wizards/service_order_approve_views.xml",
    ],
    "demo": [
        "data/res.partner-demo.csv",
        "data/librefleet.vehicle-demo.csv",
        "data/service_order_demo.xml",
    ],

}
