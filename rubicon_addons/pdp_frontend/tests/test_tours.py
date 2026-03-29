"""
Odoo tour tests for pdp_frontend.

Uses a dedicated test database (rubicon_test).

Create the test DB once:
    make test-db-init

Then run all tours:
    make test-tours

Or a single tour:
    make test-tours TAGS=/pdp_frontend:TestPdpTours.test_tour_stone_manage
"""
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestPdpTours(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        # ── Reference data needed by workspace tours ──────────────────────────
        cls.tour_model = env["pdp.product.model"].create({"code": "TOUR-MDL"})
        cls.tour_product = env["pdp.product"].create(
            {"model_id": cls.tour_model.id, "code": "TOUR-PROD", "active": True}
        )

        # Labor type for the workspace labor tab tour
        cls.labor_type = env["pdp.labor.type"].create(
            {"code": "LABOR1", "name": "Tour Labor"}
        )

        # Currency setting so stone/metal cost dropdowns are populated
        usd = env.ref("base.USD")
        env["pdp.currency.setting"].create(
            {"currency_id": usd.id, "rate": 1.0, "sequence": 1}
        )

    # ── Stone manage tours ────────────────────────────────────────────────────

    def test_tour_stone_manage(self):
        """Complete stone data lifecycle: category, type, shape, shade, size,
        unit cost, unit weight."""
        self.start_tour("/web", "pdp_tour_stone_manage", login="admin", timeout=180)

    def test_tour_ornament_categories(self):
        """Add an ornament category via Manage > Ornament Categories."""
        self.start_tour("/web", "pdp_tour_ornament_categories", login="admin")

    # ── Metal & Parts tours ───────────────────────────────────────────────────

    def test_tour_metal_manage(self):
        """Add a metal, edit its cost, add a purity, add a conversion parameter."""
        self.start_tour("/web", "pdp_tour_metal_manage", login="admin")

    def test_tour_parts_manage(self):
        """Add a part and a cost row for that part."""
        self.start_tour("/web", "pdp_tour_parts_manage", login="admin")

    # ── Workspace tours ───────────────────────────────────────────────────────

    def test_tour_workspace_nav(self):
        """Select model/product, switch tabs, add a labor cost, save."""
        self.start_tour("/web", "pdp_tour_workspace_nav", login="admin")

    def test_tour_workspace_invalid_stone(self):
        """Enter an invalid stone code and verify the warning notification."""
        self.start_tour("/web", "pdp_tour_workspace_invalid_stone", login="admin")

    def test_tour_margin_create(self):
        """Create a new margin via Manage > Margins and verify it in the list."""
        self.start_tour("/web", "pdp_tour_margin_create", login="admin")
