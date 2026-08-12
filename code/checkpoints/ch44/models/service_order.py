from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ServiceOrder(models.Model):
    _name = "librefleet.service.order"
    # ch23: the list form of _inherit. Keeps _name (so this is still OUR model,
    # not an extension of a mixin) while pulling in mail's two mixins.
    # ch37 adds portal.mixin: access_token/access_url, for the customer portal's
    # share-link fallback when a portal user's own record rule is not enough.
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _description = "Service Order"
    _rec_name = "reference"
    _order = "scheduled_start desc, id desc"

    reference = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Human-readable order number, assigned from the sequence "
        "when the order is saved.",
    )
    vehicle_id = fields.Many2one(
        "librefleet.vehicle", required=True, ondelete="restrict", index=True
    )
    customer_id = fields.Many2one(
        related="vehicle_id.owner_id", store=True, string="Customer", tracking=True
    )
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
        default="draft",
        required=True,
        tracking=True,
    )
    scheduled_start = fields.Datetime()
    scheduled_end = fields.Datetime()
    notes = fields.Text()
    parts_total = fields.Float(compute="_compute_parts_labor")
    labor_total = fields.Float(compute="_compute_parts_labor")
    margin = fields.Float(
        compute="_compute_margin",
        store=True,
        help="What the order earns: parts revenue plus the flat "
        "fee, minus what the parts cost the workshop.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = (
                    self.env["ir.sequence"].next_by_code("librefleet.service.order")
                    or "New"
                )
        return super().create(vals_list)

    def _compute_access_url(self):
        # portal.mixin's default is the literal string '#'; every model that
        # uses the mixin has to point it at its own portal route.
        super()._compute_access_url()
        for order in self:
            order.access_url = "/my/service-orders/%s" % order.id

    def action_open_approve_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Approve & Complete",
            "res_model": "librefleet.service.order.approve.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_order_id": self.id},
        }

    @api.depends("line_ids.subtotal", "service_type_id.flat_fee")
    def _compute_parts_labor(self):
        for order in self:
            order.parts_total = sum(order.line_ids.mapped("subtotal"))
            order.labor_total = order.service_type_id.flat_fee

    @api.depends(
        "parts_total", "labor_total", "line_ids.qty", "line_ids.part_id.standard_cost"
    )
    def _compute_margin(self):
        for order in self:
            parts_cost = sum(
                line.qty * line.part_id.standard_cost for line in order.line_ids
            )
            order.margin = order.parts_total + order.labor_total - parts_cost

    @api.constrains("scheduled_start", "scheduled_end", "vehicle_id", "stage")
    def _check_no_overlap(self):
        for order in self:
            if not (order.scheduled_start and order.scheduled_end):
                continue
            if order.scheduled_end <= order.scheduled_start:
                raise ValidationError(
                    self.env._(
                        "An order must end after it starts (check the schedule)."
                    )
                )
            if order.stage == "cancelled":
                continue
            clash = self.search_count(
                [
                    ("id", "!=", order.id),
                    ("vehicle_id", "=", order.vehicle_id.id),
                    ("stage", "!=", "cancelled"),
                    ("scheduled_start", "<", order.scheduled_end),
                    ("scheduled_end", ">", order.scheduled_start),
                ]
            )
            if clash:
                raise ValidationError(
                    self.env._("%s is already booked during that window.")
                    % order.vehicle_id.license_plate
                )


class ServiceOrderLine(models.Model):
    _name = "librefleet.service.order.line"
    _description = "Service Order Line"

    order_id = fields.Many2one(
        "librefleet.service.order", required=True, ondelete="cascade", index=True
    )
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
