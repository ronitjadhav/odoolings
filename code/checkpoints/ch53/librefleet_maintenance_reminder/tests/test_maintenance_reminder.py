from odoo.fields import Datetime
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMaintenanceReminder(TransactionCase):
    """Every fixture is built here, on purpose: this module installs with
    --without-demo, so a test that reaches for a demo record instead is a
    test that only passes on the author's machine."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_type = cls.env["librefleet.service.type"].create(
            {"name": "Test Service", "flat_fee": 100.0}
        )

    def test_maintenance_reminder_is_idempotent(self):
        """Chapter 35: running the reminder twice must not create two activities."""
        vehicle = self.env["librefleet.vehicle"].create({"license_plate": "TEST-002"})
        vehicle.action_send_maintenance_reminders()
        vehicle.action_send_maintenance_reminders()
        reminders = vehicle.activity_ids.filtered(
            lambda a: a.summary == "Schedule maintenance"
        )
        self.assertEqual(len(reminders), 1)

    def test_reminder_cleared_when_service_completes(self):
        """The automation half: a done service order should clear the open
        reminder on its vehicle, not just stop new ones from being created."""
        vehicle = self.env["librefleet.vehicle"].create({"license_plate": "TEST-003"})
        vehicle.action_send_maintenance_reminders()
        open_reminder = vehicle.activity_ids.filtered(
            lambda a: a.summary == "Schedule maintenance"
        )
        self.assertEqual(len(open_reminder), 1)

        order = self.env["librefleet.service.order"].create(
            {
                "vehicle_id": vehicle.id,
                "service_type_id": self.service_type.id,
                "scheduled_start": Datetime.to_datetime("2026-09-04 09:00:00"),
                "scheduled_end": Datetime.to_datetime("2026-09-04 10:00:00"),
            }
        )
        order.write({"stage": "confirmed"})
        order.write({"stage": "in_progress"})
        order.write({"stage": "done"})

        self.assertFalse(
            vehicle.activity_ids.filtered(
                lambda a: a.summary == "Schedule maintenance"
            ),
            "the base.automation should have called _clear_maintenance_reminder",
        )
