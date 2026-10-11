from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        # copy the service order from the procurement values onto the move the rule creates
        return super()._get_custom_move_fields() + ["librefleet_order_id"]
