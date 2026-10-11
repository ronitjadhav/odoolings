from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceOrder(models.Model):
    _inherit = "librefleet.service.order"

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Parts From",
        help="The warehouse whose rules supply the parts when the order is done.",
    )
    move_ids = fields.One2many("stock.move", "librefleet_order_id", string="Stock Moves")
    picking_count = fields.Integer(compute="_compute_picking_count")

    @api.depends("move_ids.picking_id")
    def _compute_picking_count(self):
        for order in self:
            order.picking_count = len(order.move_ids.picking_id)

    def write(self, vals):
        finishing = self.filtered(lambda o: o.stage != "done") if vals.get("stage") == "done" else self.browse()
        res = super().write(vals)
        finishing._consume_parts()
        return res

    def _consume_parts(self):
        """Ask the stock rules for every stocked part, as a sale order asks for a delivery."""
        workshop = self.env.ref("librefleet_stock.location_workshop")
        procurements = []
        for order in self:
            lines = order.line_ids.filtered(lambda line: line.part_id.product_id.is_storable and line.qty > 0)
            if not lines:
                continue
            if not order.warehouse_id:
                raise UserError(_("Set Parts From on %s before marking it done.", order.reference))
            for line in lines:
                product = line.part_id.product_id
                procurements.append(self.env["stock.rule"].Procurement(
                    product, line.qty, product.uom_id, workshop,
                    order.reference, order.reference, order.warehouse_id.company_id,
                    {"warehouse_id": order.warehouse_id, "librefleet_order_id": order.id,
                     "partner_id": order.customer_id.id},
                ))
        if procurements:
            self.env["stock.rule"].run(procurements)

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("stock.action_picking_tree_all")
        action["domain"] = [("id", "in", self.move_ids.picking_id.ids)]
        action["context"] = {"create": False}
        return action
