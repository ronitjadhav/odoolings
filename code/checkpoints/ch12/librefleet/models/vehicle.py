from odoo import fields, models


class Vehicle(models.Model):
    _name = "librefleet.vehicle"
    _description = "Workshop Vehicle"
    _rec_name = "license_plate"

    license_plate = fields.Char(required=True)
    owner_id = fields.Many2one("res.partner", string="Owner")
    service_order_ids = fields.One2many("librefleet.service.order", "vehicle_id")
    vin = fields.Char(string="VIN", help="17-character vehicle identification number")
    model_name = fields.Char()
    year = fields.Integer()
    mileage_km = fields.Float(string="Mileage (km)")
    notes = fields.Text()
    active = fields.Boolean(default=True)
