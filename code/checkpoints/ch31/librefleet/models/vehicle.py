from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Vehicle(models.Model):
    _name = "librefleet.vehicle"
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
                    "Model year %s is out of range (1900 to next year)."
                    % vehicle.year)
