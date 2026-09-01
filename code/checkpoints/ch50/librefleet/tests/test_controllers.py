from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestPublicControllers(HttpCase):
    """HttpCase actually starts an HTTP client against a real running server,
    the browser-less cousin of the tours chapter 39's OWL work will use."""

    def test_services_page_public(self):
        response = self.url_open("/librefleet/services")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"What we service", response.content)
