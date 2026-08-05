from odoo import fields, models


class ProductTemplate(models.Model):
    """Extending a core model that arrived via a NEW dependency.

    product.template only exists because "product" is in our manifest's depends.
    Remove it there and this class cannot resolve, which is the break-it lab in
    this chapter.
    """

    _inherit = "product.template"

    librefleet_is_part = fields.Boolean(
        string="Workshop Part",
        help="Tick to offer this product as a spare part on service orders.")
