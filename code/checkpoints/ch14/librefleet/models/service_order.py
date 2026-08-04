from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ServiceOrder(models.Model):
    _name = "librefleet.service.order"
    _description = "Service Order"
    _rec_name = "reference"
    _order = "scheduled_start desc, id desc"

    reference = fields.Char(
        required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "librefleet.service.order") or "New",
        help="Human-readable order number, assigned from a sequence.")
    vehicle_id = fields.Many2one(
        "librefleet.vehicle", required=True, ondelete="restrict", index=True)
    customer_id = fields.Many2one(
        related="vehicle_id.owner_id", store=True, string="Customer")
    service_type_id = fields.Many2one("librefleet.service.type")
    technician_ids = fields.Many2many("res.users", string="Technicians")
    line_ids = fields.One2many("librefleet.service.order.line", "order_id")
    stage = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="draft", required=True)
    scheduled_start = fields.Datetime()
    scheduled_end = fields.Datetime()
    notes = fields.Text()
    parts_total = fields.Float(compute="_compute_totals")
    labor_total = fields.Float(compute="_compute_totals")
    margin = fields.Float(compute="_compute_totals",
                          help="What the order earns: parts revenue plus the flat "
                               "fee, minus what the parts cost the workshop.")

    @api.depends("line_ids.subtotal", "line_ids.qty",
                 "line_ids.part_id.standard_cost", "service_type_id.flat_fee")
    def _compute_totals(self):
        for order in self:
            order.parts_total = sum(order.line_ids.mapped("subtotal"))
            order.labor_total = order.service_type_id.flat_fee
            parts_cost = sum(
                line.qty * line.part_id.standard_cost for line in order.line_ids)
            order.margin = order.parts_total + order.labor_total - parts_cost

    @api.constrains("scheduled_start", "scheduled_end", "vehicle_id", "stage")
    def _check_no_overlap(self):
        for order in self:
            if not (order.scheduled_start and order.scheduled_end):
                continue
            if order.scheduled_end <= order.scheduled_start:
                raise ValidationError(
                    "An order must end after it starts (check the schedule).")
            if order.stage == "cancelled":
                continue
            clash = self.search_count([
                ("id", "!=", order.id),
                ("vehicle_id", "=", order.vehicle_id.id),
                ("stage", "!=", "cancelled"),
                ("scheduled_start", "<", order.scheduled_end),
                ("scheduled_end", ">", order.scheduled_start),
            ])
            if clash:
                raise ValidationError(
                    "%s is already booked during that window."
                    % order.vehicle_id.license_plate)


class ServiceOrderLine(models.Model):
    _name = "librefleet.service.order.line"
    _description = "Service Order Line"

    order_id = fields.Many2one(
        "librefleet.service.order", required=True, ondelete="cascade", index=True)
    part_id = fields.Many2one("librefleet.part")
    qty = fields.Float(string="Quantity", default=1.0)
    price_unit = fields.Float(string="Unit Price")
    subtotal = fields.Float(compute="_compute_subtotal", store=True)

    @api.depends("qty", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.price_unit

    @api.onchange("part_id")
    def _onchange_part_id(self):
        if self.part_id:
            self.price_unit = self.part_id.list_price
