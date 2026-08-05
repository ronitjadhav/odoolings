from odoo import fields, models


class Part(models.Model):
    _name = "librefleet.part"
    _description = "Spare Part"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(help="Internal reference printed on the shelf label.")
    standard_cost = fields.Float(help="What the workshop pays for it.")
    list_price = fields.Float(help="What the customer pays for it.")
