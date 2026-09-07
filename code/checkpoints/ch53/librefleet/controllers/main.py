from odoo import http
from odoo.http import request


class LibreFleetPublic(http.Controller):
    @http.route("/librefleet/services", type="http", auth="public", website=False)
    def services_page(self, **kwargs):
        service_types = request.env["librefleet.service.type"].sudo().search([])
        return request.render(
            "librefleet.services_page", {"service_types": service_types}
        )

    @http.route("/librefleet/vehicles/lookup", type="jsonrpc", auth="public")
    def vehicle_lookup(self, license_plate, **kwargs):
        vehicle = (
            request.env["librefleet.vehicle"]
            .sudo()
            .search([("license_plate", "=", license_plate)], limit=1)
        )
        if not vehicle:
            return {"found": False}
        return {
            "found": True,
            "model_name": vehicle.model_name,
            "service_count": vehicle.service_count,
        }
