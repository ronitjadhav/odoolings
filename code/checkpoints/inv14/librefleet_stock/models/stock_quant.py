from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == "smallest_first":
            # empty the nearly empty bins first, oldest among equals
            return "quantity ASC, in_date ASC, id"
        return super()._get_removal_strategy_order(removal_strategy)
