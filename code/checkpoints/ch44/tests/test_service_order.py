from odoo.exceptions import UserError, ValidationError
from odoo.fields import Datetime
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestServiceOrder(TransactionCase):
    """Every fixture is built here, on purpose: this module installs with
    --without-demo (chapter 4's rule), so a test that reaches for a demo
    record instead is a test that only passes on the author's machine."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vehicle = cls.env["librefleet.vehicle"].create(
            {
                "license_plate": "TEST-001",
            }
        )
        cls.service_type = cls.env["librefleet.service.type"].create(
            {
                "name": "Test Service",
                "flat_fee": 100.0,
            }
        )
        cls.part = cls.env["librefleet.part"].create(
            {
                "name": "Test Part",
                "standard_cost": 10.0,
                "list_price": 20.0,
            }
        )

    def _create_order(self, start, end, **extra):
        vals = {
            "vehicle_id": self.vehicle.id,
            "service_type_id": self.service_type.id,
            "scheduled_start": start,
            "scheduled_end": end,
        }
        vals.update(extra)
        return self.env["librefleet.service.order"].create(vals)

    def test_no_overlapping_bookings(self):
        """Chapter 14's constraint: the same vehicle cannot be double-booked."""
        self._create_order(
            Datetime.to_datetime("2026-09-01 09:00:00"),
            Datetime.to_datetime("2026-09-01 11:00:00"),
        )
        with self.assertRaises(ValidationError):
            self._create_order(
                Datetime.to_datetime("2026-09-01 10:00:00"),
                Datetime.to_datetime("2026-09-01 12:00:00"),
            )

    def test_margin_computed(self):
        """Chapter 13: parts_total + labor_total, minus what the parts cost the workshop."""
        order = self._create_order(
            Datetime.to_datetime("2026-09-02 09:00:00"),
            Datetime.to_datetime("2026-09-02 10:00:00"),
            line_ids=[(0, 0, {"part_id": self.part.id, "qty": 2, "price_unit": 20.0})],
        )
        # 2 * 20.0 parts revenue + 100.0 labor - 2 * 10.0 parts cost = 120.0
        self.assertEqual(order.margin, 120.0)

    def test_approve_wizard_blocks_negative_margin(self):
        """Chapter 20: a losing order needs the manager override, not a plain confirm."""
        # A part priced far under what it costs the workshop, so the loss on
        # the part outweighs the flat labor fee: 1.0 revenue + 100.0 labor -
        # 200.0 cost = -99.0. A more realistic loss (say, one cheap part)
        # would not necessarily overcome a flat fee this high, and the point
        # of this test is the wizard's guard, not tuning a margin to the wire.
        expensive_part = self.env["librefleet.part"].create(
            {
                "name": "Expensive Part",
                "standard_cost": 200.0,
                "list_price": 1.0,
            }
        )
        order = self._create_order(
            Datetime.to_datetime("2026-09-03 09:00:00"),
            Datetime.to_datetime("2026-09-03 10:00:00"),
            line_ids=[
                (0, 0, {"part_id": expensive_part.id, "qty": 1, "price_unit": 1.0})
            ],
        )
        order.write({"stage": "confirmed"})
        order.write({"stage": "in_progress"})
        self.assertLess(
            order.margin, 0, "fixture should lose money for this test to mean anything"
        )
        wizard = self.env["librefleet.service.order.approve.wizard"].create(
            {"order_id": order.id}
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_maintenance_reminder_is_idempotent(self):
        """Chapter 35: running the reminder twice must not create two activities."""
        vehicle = self.env["librefleet.vehicle"].create({"license_plate": "TEST-002"})
        vehicle.action_send_maintenance_reminders()
        vehicle.action_send_maintenance_reminders()
        reminders = vehicle.activity_ids.filtered(
            lambda a: a.summary == "Schedule maintenance"
        )
        self.assertEqual(len(reminders), 1)
