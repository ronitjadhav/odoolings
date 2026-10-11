from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    librefleet_order_id = fields.Many2one("librefleet.service.order", string="Service Order", index="btree_not_null")
