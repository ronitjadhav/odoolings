from odoo import api, fields, models


class ServiceOrder(models.Model):
    _name = "librefleet.service.order"
    _description = "Service Order"
    _rec_name = "vehicle_id"
    _order = "scheduled_start desc, id desc"

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
