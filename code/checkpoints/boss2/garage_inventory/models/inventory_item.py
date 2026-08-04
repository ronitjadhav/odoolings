from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InventoryItem(models.Model):
    _name = "garage.inventory.item"
    _description = "Garage Inventory Item"

    _code_unique = models.Constraint(
        "unique(code)",
        "Another item already uses that code.",
    )

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    qty_on_hand = fields.Float(string="Quantity on Hand", default=0.0)
    unit_cost = fields.Float()
    total_value = fields.Float(compute="_compute_total_value", store=True)

    @api.depends("qty_on_hand", "unit_cost")
    def _compute_total_value(self):
        for item in self:
            item.total_value = item.qty_on_hand * item.unit_cost

    @api.constrains("qty_on_hand")
    def _check_qty_on_hand(self):
        for item in self:
            if item.qty_on_hand < 0:
                raise ValidationError("Quantity on hand cannot be negative.")
