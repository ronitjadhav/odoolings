# librefleet_maintenance_reminder: extracted from librefleet in chapter 46.
{
    "name": "LibreFleet Maintenance Reminders",
    "summary": "Automatic maintenance-due activities for LibreFleet vehicles",
    "version": "19.0.1.0.0",
    "category": "Services",
    "author": "Odoolings readers",
    "website": "https://odoolings.ronit.io/",
    "license": "AGPL-3",
    "development_status": "Beta",
    "application": False,
    "depends": ["librefleet", "base_automation"],
    "data": [
        "data/maintenance_reminder_cron.xml",
        "data/maintenance_reminder_automation.xml",
    ],
}
