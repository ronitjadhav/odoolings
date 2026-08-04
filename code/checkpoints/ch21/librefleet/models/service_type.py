from odoo import fields, models


class ServiceType(models.Model):
    _name = "librefleet.service.type"
    _description = "Service Type"
    _order = "name"

    name = fields.Char(required=True)
    flat_fee = fields.Float(help="Fixed price charged for this service, parts excluded.")
    default_duration_h = fields.Float(string="Default Duration (h)")
