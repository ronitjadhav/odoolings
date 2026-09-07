from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestDiscountLimit(TransactionCase):
    """The guard, on a line built from a product that already exists.

    Creating a product.template here instead would make the test depend on
    every other module's opinion of what a product template requires: in a
    database with website_sale installed, that create needs a column this test
    would never think to set. Reusing a product keeps the test about our own
    constraint.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].search(
            [("sale_ok", "=", True)], limit=1
        )
        cls.order = cls.env["sale.order"].create(
            {"partner_id": cls.env["res.partner"].search([], limit=1).id}
        )

    def _line(self, discount_fixed):
        return self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "discount_fixed": discount_fixed,
            }
        )

    def test_discount_below_unit_price_is_allowed(self):
        self.assertEqual(self._line(25.0).price_subtotal, 150.0)

    def test_discount_equal_to_unit_price_is_allowed(self):
        self.assertEqual(self._line(100.0).price_subtotal, 0.0)

    def test_discount_above_unit_price_is_refused(self):
        with self.assertRaises(ValidationError):
            self._line(150.0)
