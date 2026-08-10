from odoo import fields, models


class Vehicle(models.Model):
    """Classic extension: no _name, so this IS librefleet.vehicle.

    The fields below land on the existing model and the existing table. This is
    the same mechanism chapter 32 uses to add fields to core models.
    """

    _inherit = "librefleet.vehicle"

    is_loanable = fields.Boolean(
        help="Can this vehicle be lent out while a customer's own car is in "
             "the workshop?")


class Consumable(models.Model):
    """Prototype: _inherit plus a new _name copies the fields into a new model.

    librefleet.consumable gets its own table and its own records. Nothing links
    it back to librefleet.part; the two are independent from here on.
    """

    _name = "librefleet.consumable"
    _inherit = "librefleet.part"
    _description = "Workshop Consumable"

    unit = fields.Char(default="litre", help="Litres, metres, whatever it is sold in.")


class Loaner(models.Model):
    """Delegation: a loaner IS a vehicle, plus rental attributes.

    _inherits (note the s) keeps two tables and links them with a required
    many2one. Vehicle fields are readable and writable straight off a loaner
    record, but they live in, and are shared with, the vehicle row.
    """

    _name = "librefleet.loaner"
    _inherits = {"librefleet.vehicle": "vehicle_id"}
    _description = "Loaner Car"

    vehicle_id = fields.Many2one(
        "librefleet.vehicle", required=True, ondelete="cascade", index=True)
    daily_rate = fields.Float(help="What the customer is charged per day.")
    available = fields.Boolean(default=True)
