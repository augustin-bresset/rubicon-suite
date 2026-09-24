"""
Odoo tour tests for pdp_frontend.

Uses a dedicated test database (rubicon_test). The tours need Chrome and
websocket-client, which the rubicon-odoo image (ops/docker/odoo) adds to
odoo:18.0; without them every tour is skipped, and CI fails on that.

Create the test DB once:
    make test-db-init

Then run all tours:
    make test-tours

Or a single tour:
    make test-tours TAGS=/pdp_frontend:TestPdpTours.test_tour_stone_manage
"""
import base64
from odoo.tests import HttpCase, tagged

# Minimal 1×1 transparent PNG — same pixel used by the JS tour DataTransfer injection
_MINIMAL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


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
        if not env["pdp.currency.setting"].search([("currency_id", "=", usd.id)], limit=1):
            env["pdp.currency.setting"].create(
                {"currency_id": usd.id, "rate": 1.0, "sequence": 1}
            )

        # Stone picker tour: a type with exactly one priced stone, so picking
        # the type resolves the line without narrowing shade/shape/size.
        stone_type = env["pdp.stone.type"].create({"code": "TOURSTN", "name": "Tour Stone"})
        env["pdp.stone"].create({
            "code": "TOUR-STN-01",
            "type_id": stone_type.id,
            "shape_id": env["pdp.stone.shape"].create({"code": "TSH", "shape": "Tour Shape"}).id,
            "size_id": env["pdp.stone.size"].create({"name": "1X1"}).id,
            "cost": 10.0,
            "currency_id": usd.id,
        })

        # ── Picture tours (Tours 9 & 10) — separate model/product with 2 photos ─
        # Using a dedicated model so Tours 8 (upload from scratch) still sees an
        # empty state when navigating to TOUR-MDL.
        cls.pix_model = env["pdp.product.model"].create({"code": "TOUR-PIX-MDL"})
        cls.pix_product = env["pdp.product"].create(
            {"model_id": cls.pix_model.id, "code": "TOUR-PIX-PROD", "active": True}
        )
        cls.tour_pic_1 = env["pdp.picture"].create({
            "scope": "product",
            "filename": "tour_pic_1.png",
            "product_ids": [(4, cls.pix_product.id)],
            "image_1920": _MINIMAL_PNG_B64,
        })
        cls.tour_pic_2 = env["pdp.picture"].create({
            "scope": "product",
            "filename": "tour_pic_2.png",
            "product_ids": [(4, cls.pix_product.id)],
            "image_1920": _MINIMAL_PNG_B64,
        })

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

    def test_tour_workspace_stone_picker(self):
        """Unknown stone type finds nothing; the tour type resolves its stone."""
        self.start_tour("/web", "pdp_tour_workspace_stone_picker", login="admin")

    def test_tour_margin_create(self):
        """Create a new margin via Manage > Margins and verify it in the list."""
        self.start_tour("/web", "pdp_tour_margin_create", login="admin")

    def test_tour_picture_manage(self):
        """Upload model-scope photo via DataTransfer, verify in manager, delete."""
        self.start_tour("/web", "pdp_tour_picture_manage", login="admin", timeout=60)

    def test_tour_picture_switch(self):
        """With 2 pre-existing product photos, switch active photo via manager."""
        self.start_tour("/web", "pdp_tour_picture_switch", login="admin", timeout=60)

    def test_tour_picture_delete_manager(self):
        """Delete a photo via the manager trash button; verify 1 photo remains."""
        self.start_tour("/web", "pdp_tour_picture_delete_manager", login="admin", timeout=60)
