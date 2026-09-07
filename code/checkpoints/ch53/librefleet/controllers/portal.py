from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request, route


class LibreFleetPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "service_order_count" in counters:
            partner = request.env.user.partner_id
            values["service_order_count"] = request.env[
                "librefleet.service.order"
            ].search_count([("customer_id", "=", partner.id)])
        return values

    @route(
        ["/my/service-orders", "/my/service-orders/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_service_orders(self, page=1, **kwargs):
        partner = request.env.user.partner_id
        ServiceOrder = request.env["librefleet.service.order"]
        domain = [("customer_id", "=", partner.id)]

        order_count = ServiceOrder.search_count(domain)
        pager = portal_pager(
            url="/my/service-orders",
            total=order_count,
            page=page,
            step=self._items_per_page,
        )
        orders = ServiceOrder.search(
            domain,
            limit=self._items_per_page,
            offset=pager["offset"],
            order="scheduled_start desc",
        )

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "orders": orders,
                "page_name": "service_order",
                "pager": pager,
                "default_url": "/my/service-orders",
            }
        )
        return request.render("librefleet.portal_my_service_orders", values)

    @route(
        ["/my/service-orders/<int:order_id>"], type="http", auth="public", website=True
    )
    def portal_service_order_page(self, order_id, access_token=None, **kwargs):
        # auth="public", not "user": a share link (?access_token=...) has to
        # work for someone who isn't logged in at all. _document_check_access
        # is what actually decides, session-based read access first, the
        # token as a fallback only if that fails.
        try:
            order_sudo = self._document_check_access(
                "librefleet.service.order", order_id, access_token=access_token
            )
        except Exception:
            return request.redirect("/my")

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "order": order_sudo,
                "page_name": "service_order",
            }
        )
        return request.render("librefleet.portal_service_order_page", values)

    @route(["/my/service-orders/<int:order_id>/report"], type="http", auth="public")
    def portal_service_order_report(self, order_id, access_token=None, **kwargs):
        order_sudo = self._document_check_access(
            "librefleet.service.order", order_id, access_token=access_token
        )
        report = (
            request.env["ir.actions.report"]
            .sudo()
            ._get_report("librefleet.report_service_order")
        )
        pdf_content, _report_type = report._render_qweb_pdf(
            "librefleet.report_service_order", order_sudo.ids
        )
        # reference is "SO/2026/0001": a bare slash in Content-Disposition's
        # filename breaks the header (and some browsers read it as a path).
        filename = order_sudo.reference.replace("/", "_")
        return request.make_response(
            pdf_content,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Disposition", "attachment; filename=%s.pdf" % filename),
            ],
        )
