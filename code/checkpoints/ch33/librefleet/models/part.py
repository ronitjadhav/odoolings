from odoo import fields, models


class Part(models.Model):
    _name = "librefleet.part"
    _description = "Spare Part"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(help="Internal reference printed on the shelf label.")
    standard_cost = fields.Float(help="What the workshop pays for it.")
    list_price = fields.Float(help="What the customer pays for it.")
    # ch22: the bridge out of our self-contained world into core's catalogue.
    # Optional on purpose: a workshop can shelve a part long before anyone
    # decides it deserves a product record.
    product_id = fields.Many2one(
        "product.product",
        string="Catalogue Product",
        domain="[('librefleet_is_part', '=', True)]",
        help="Link to the real product, once this part is sold or stocked.")
