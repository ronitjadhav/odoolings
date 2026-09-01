from odoo import api, fields, models


class ResPartner(models.Model):
    """Classic extension of a CORE model.

    No _name, so this is res.partner itself: the same model and the same table
    every other Odoo app uses. Our fields are prefixed librefleet_ so they can
    never collide with core's, or with another module's.
    """

    _inherit = "res.partner"

    librefleet_vehicle_ids = fields.One2many(
        "librefleet.vehicle", "owner_id", string="Vehicles"
    )
    librefleet_vehicle_count = fields.Integer(
        compute="_compute_librefleet_vehicle_count", string="Vehicle Count"
    )

    @api.depends("librefleet_vehicle_ids")
    def _compute_librefleet_vehicle_count(self):
        for partner in self:
            partner.librefleet_vehicle_count = len(partner.librefleet_vehicle_ids)

    def action_librefleet_vehicles(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Vehicles",
            "res_model": "librefleet.vehicle",
            "view_mode": "list,form",
            "domain": [("owner_id", "=", self.id)],
            "context": {"default_owner_id": self.id},
        }
