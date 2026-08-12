from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

DAYS_BETWEEN_SERVICES = 180


class Vehicle(models.Model):
    _name = "librefleet.vehicle"
    # ch35: both of mail's mixins. activity.mixin alone looks tempting (vehicles
    # only need reminder activities, no discussion), but action_feedback() logs
    # its completion note through message_post_with_source(), which lives on
    # mail.thread, so marking a reminder done throws AttributeError without it.
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Workshop Vehicle"
    _rec_name = "license_plate"

    _license_plate_unique = models.Constraint(
        "unique(license_plate)",
        "That license plate is already registered on another vehicle.",
    )

    license_plate = fields.Char(required=True)
    owner_id = fields.Many2one("res.partner", string="Owner")
    service_order_ids = fields.One2many("librefleet.service.order", "vehicle_id")
    vin = fields.Char(string="VIN", help="17-character vehicle identification number")
    model_name = fields.Char()
    year = fields.Integer()
    mileage_km = fields.Float(string="Mileage (km)")
    notes = fields.Text()
    active = fields.Boolean(default=True)
    service_count = fields.Integer(compute="_compute_service_count")

    @api.depends("service_order_ids")
    def _compute_service_count(self):
        for vehicle in self:
            vehicle.service_count = len(vehicle.service_order_ids)

    def action_view_service_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Service Orders",
            "res_model": "librefleet.service.order",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {"default_vehicle_id": self.id},
        }

    @api.constrains("year")
    def _check_year(self):
        current_year = fields.Date.today().year
        for vehicle in self:
            if vehicle.year and not (1900 <= vehicle.year <= current_year + 1):
                raise ValidationError(
                    self.env._("Model year %s is out of range (1900 to next year).")
                    % vehicle.year
                )

    def action_send_maintenance_reminders(self):
        # ch35: the scheduled action and the "Send reminders now" server action
        # both call this, so the two triggers (time-based, on-demand) can never
        # drift into two different definitions of "overdue".
        reminded = self.env["librefleet.vehicle"]
        activity_type = self.env.ref("mail.mail_activity_data_todo")
        # activity_schedule() leaves user_id empty unless told otherwise (the
        # "Assigned to" default you see in the UI is a client-side fill-in, not
        # something the ORM does), so an unassigned reminder is a real bug and
        # not just a cosmetic one: nobody's activity list would ever show it.
        manager = self.env.ref("librefleet.group_librefleet_manager").user_ids[:1]
        assignee_id = manager.id if manager else self.env.user.id
        cutoff = fields.Datetime.now() - relativedelta(days=DAYS_BETWEEN_SERVICES)
        for vehicle in self:
            done_orders = vehicle.service_order_ids.filtered(
                lambda o: o.stage == "done"
            )
            last_service = max(done_orders.mapped("scheduled_end"), default=False)
            if last_service and last_service >= cutoff:
                continue
            has_open_reminder = vehicle.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type
            )
            if has_open_reminder:
                continue
            vehicle.activity_schedule(
                activity_type_id=activity_type.id,
                summary="Schedule maintenance",
                note="No completed service order in the last %d days."
                % DAYS_BETWEEN_SERVICES,
                user_id=assignee_id,
            )
            reminded += vehicle
        return reminded

    def _clear_maintenance_reminder(self):
        # ch35: the automated action's payload. Marks any open reminder done
        # once a service actually happened, instead of leaving it to rot.
        activity_type = self.env.ref("mail.mail_activity_data_todo")
        for vehicle in self:
            open_reminders = vehicle.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type
                and a.summary == "Schedule maintenance"
            )
            open_reminders.action_feedback(feedback="Service completed.")
