from odoo import fields, models


class ServiceOrder(models.Model):
    _name = "librefleet.service.order"
    _description = "Service Order"
    _rec_name = "vehicle_id"
    _order = "scheduled_start desc, id desc"

    vehicle_id = fields.Many2one(
        "librefleet.vehicle", required=True, ondelete="restrict", index=True)
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


class ServiceOrderLine(models.Model):
    _name = "librefleet.service.order.line"
    _description = "Service Order Line"

    order_id = fields.Many2one(
        "librefleet.service.order", required=True, ondelete="cascade", index=True)
    part_id = fields.Many2one("librefleet.part")
    qty = fields.Float(string="Quantity", default=1.0)
    price_unit = fields.Float(string="Unit Price")
