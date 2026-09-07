from odoo import api, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.constrains("discount_fixed", "price_unit")
    def _check_discount_fixed_not_above_unit_price(self):
        """A fixed discount above the unit price makes the line negative.

        sale_fixed_discount converts the amount to a percentage and does not
        cap it, which is a deliberate choice upstream. This is our policy, so
        it lives here rather than in a fork of theirs.
        """
        for line in self:
            if line.discount_fixed > line.price_unit:
                raise ValidationError(
                    self.env._(
                        "A fixed discount of %(discount)s is larger than the "
                        "unit price of %(price)s, which would make the line "
                        "negative.",
                        discount=line.discount_fixed,
                        price=line.price_unit,
                    )
                )
