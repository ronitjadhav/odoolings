from odoo import _, fields, models
from odoo.exceptions import UserError


class ServiceOrderApproveWizard(models.TransientModel):
    _name = "librefleet.service.order.approve.wizard"
    _description = "Approve & Complete Service Order"

    order_id = fields.Many2one("librefleet.service.order", required=True, readonly=True)
    margin = fields.Float(related="order_id.margin", readonly=True)
    override_negative_margin = fields.Boolean(
        string="Complete anyway (negative margin)",
        groups="librefleet.group_librefleet_manager",
    )
    note = fields.Text(string="Completion Note")

    def action_confirm(self):
        self.ensure_one()
        order = self.order_id
        if order.stage != "in_progress":
            raise UserError(_("Only an order that is in progress can be marked done."))
        if order.margin < 0 and not self.override_negative_margin:
            raise UserError(
                _(
                    "This order loses money (margin %(margin).2f). A manager must "
                    "tick the override to complete it anyway.",
                    margin=order.margin,
                )
            )
        if self.note:
            order.notes = "%s\n\nCompletion note: %s" % (order.notes or "", self.note)
        order.stage = "done"
        return {"type": "ir.actions.act_window_close"}
