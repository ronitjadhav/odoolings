from dateutil.relativedelta import relativedelta
from odoo import fields, models

DAYS_BETWEEN_SERVICES = 180


class Vehicle(models.Model):
    _inherit = "librefleet.vehicle"

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
