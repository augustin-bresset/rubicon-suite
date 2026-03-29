/** @odoo-module **/
/**
 * Tour 1: pdp_tour_stone_manage — Complete Stones & Diamonds management
 *   Cats & Types: add category TCAT → save → add type TTYP (assigned to TCAT) → save
 *   Other Info:   add shape TSHP, shade TSHN, size 1.00T → save
 *   Unit Costs:   add stone cost row (TTYP / TOUR-01 / 100.00) → save
 *   Unit Weights: add stone weight row (TTYP / TSHP / TSHN / 1.00T / 0.5000) → save
 *
 * Tour 2: pdp_tour_ornament_categories — Ornament Categories management
 *   Add category code=ORNT, name=Tour Ornament → save
 */
import { registry } from "@web/core/registry";

// ── Shared helpers ────────────────────────────────────────────────────────────

function goToPdpManage(subMenuXmlId) {
    return [
        // Odoo 18 community: apps live in a navbar dropdown, not a separate home screen
        { trigger: ".o_navbar_apps_menu .dropdown-toggle", run: "click" },
        { trigger: ".o-dropdown--menu .o_app[data-menu-xmlid='pdp_frontend.menu_pdp_frontend_root']", run: "click" },
        { trigger: "[data-menu-xmlid='pdp_frontend.menu_pdp_frontend_manage']", run: "click" },
        { trigger: `[data-menu-xmlid='${subMenuXmlId}']`, run: "click" },
        { trigger: ".pdp-manage" },
    ];
}

/** Click a tab link by its visible text. */
function clickTab(text) {
    return {
        trigger: ".pdp-manage .nav-link",
        run: () => {
            for (const a of document.querySelectorAll(".pdp-manage .nav-link")) {
                if (a.textContent.trim() === text) { a.click(); return; }
            }
        },
    };
}

/** Click "Add" (btn-secondary) in a panel identified by its heading text. */
function clickPanelAdd(headingText) {
    return {
        trigger: ".pdp-manage .fw-semibold.me-auto",
        run: () => {
            for (const h of document.querySelectorAll(".pdp-manage .fw-semibold.me-auto")) {
                if (h.textContent.trim() === headingText) {
                    h.parentElement.querySelector(".btn-secondary").click();
                    return;
                }
            }
        },
    };
}

/** Select an <option> in a <select> by matching option text (partial match). */
function selectByText(text) {
    return function(helpers) {
        const sel = helpers.anchor;
        const opt = [...sel.options].find(o => o.text.trim().includes(text));
        if (!opt) throw new Error(`Option containing "${text}" not found`);
        sel.value = opt.value;
        sel.dispatchEvent(new Event("change", { bubbles: true }));
    };
}

// ── Tour 1: Complete Stone Management ─────────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_stone_manage", {
    url: "/web",
    steps: () => [
        ...goToPdpManage("pdp_frontend.menu_pdp_manage_stones"),

        // ── Step A: Add stone category ────────────────────────────────────────

        // "Add Category" = btn-secondary that directly follows the Save btn-primary
        { trigger: ".pdp-manage .btn-primary.btn-sm + .btn-secondary.btn-sm", run: "click" },

        // Categories panel has class "d-flex flex-column border-bottom" → unique in this tab
        {
            trigger: ".d-flex.flex-column.border-bottom .pdp-manage-table tbody tr:last-child input[placeholder='Code']",
            run: "edit TCAT",
        },
        {
            trigger: ".d-flex.flex-column.border-bottom .pdp-manage-table tbody tr:last-child input[placeholder='Name']",
            run: "edit Tour Cat",
        },

        // Save (enabled after editing)
        { trigger: ".pdp-manage .btn-primary.btn-sm:not(:disabled)", run: "click" },
        // Wait for success notification to confirm save
        { trigger: ".o_notification" },
        // Wait for notification to disappear before next action
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step B: Add stone type (TCAT is now saved with a DB id) ───────────

        // First click the TCAT category row to select it — this causes filteredTypes
        // to show ONLY types assigned to TCAT, giving a 1-row types table (no scroll needed).
        {
            trigger: ".d-flex.flex-column.border-bottom .pdp-manage-table tbody tr",
            run(helpers) {
                for (const tr of document.querySelectorAll(".d-flex.flex-column.border-bottom .pdp-manage-table tbody tr")) {
                    const inp = tr.querySelector("input[placeholder='Code']");
                    if (inp && (inp.value === "TCAT" || inp.getAttribute("value") === "TCAT")) {
                        tr.click();
                        return;
                    }
                }
                throw new Error("TCAT row not found in categories table");
            },
        },

        // Add a new type — since TCAT is selected, addType() assigns category_id = TCAT
        clickPanelAdd("Stone Types"),

        // Only TTYP row visible (filteredTypes = types assigned to TCAT = just TTYP)
        {
            trigger: ".d-flex.flex-column:not(.border-bottom) .pdp-manage-table tbody tr:last-child input[placeholder='Code']",
            run: "edit TTYP",
        },
        {
            trigger: ".d-flex.flex-column:not(.border-bottom) .pdp-manage-table tbody tr:last-child input[placeholder='Name']",
            run: "edit Tour Type",
        },
        // Category select already pre-assigned to TCAT (by addType); no need to change it.

        // Save cats & types together
        { trigger: ".pdp-manage .btn-primary.btn-sm:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step C: Other Info — shapes, shades, sizes ────────────────────────

        clickTab("Other Info"),

        // Add Shape
        clickPanelAdd("Shapes"),
        {
            trigger: ".pdp-manage input[placeholder='Shape']:last-of-type",
            run: (helpers) => {
                const row = helpers.anchor.closest("tr");
                const codeInput = row.querySelector("input[placeholder='Code']");
                codeInput.value = "TSHP";
                codeInput.dispatchEvent(new Event("input", { bubbles: true }));
            },
        },
        { trigger: ".pdp-manage input[placeholder='Shape']:last-of-type", run: "edit Tour Shape" },

        // Add Shade
        clickPanelAdd("Shades"),
        {
            trigger: ".pdp-manage input[placeholder='Shade']:last-of-type",
            run: (helpers) => {
                const row = helpers.anchor.closest("tr");
                const codeInput = row.querySelector("input[placeholder='Code']");
                codeInput.value = "TSHN";
                codeInput.dispatchEvent(new Event("input", { bubbles: true }));
            },
        },
        { trigger: ".pdp-manage input[placeholder='Shade']:last-of-type", run: "edit Tour Shade" },

        // Add Size
        clickPanelAdd("Sizes"),
        { trigger: ".pdp-manage input[placeholder='Size name']:last-of-type", run: "edit 1.00T" },

        // Save all Other Info (Save button is in the Shapes panel header)
        {
            trigger: ".pdp-manage .d-flex.flex-column.border-end .btn-primary.btn-sm:not(:disabled)",
            run: "click",
        },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step D: Unit Costs ────────────────────────────────────────────────

        clickTab("Unit Costs"),

        // Wait for initial loadStones() (no filter) to finish — avoids race with filter reload.
        // Real data rows have td without colspan; placeholder has colspan.
        // Timeout 30s: loadStones() ORM call can take ~10s on full dataset.
        { trigger: ".pdp-manage-table tbody tr td:not([colspan])", timeout: 30000 },

        // Add row (default type from stoneTypes[0] is pre-selected)
        { trigger: ".pdp-manage .ms-auto .btn-secondary.btn-sm", run: "click" },

        // Fill stock code (type pre-selected via default)
        {
            trigger: ".pdp-manage-table tbody tr:last-child input[placeholder='Code']",
            run: "edit TOUR-01",
        },
        {
            trigger: ".pdp-manage-table tbody tr:last-child input[type='number']",
            run: "edit 100",
        },

        // Save costs
        { trigger: ".pdp-manage .ms-auto .btn-primary.btn-sm:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step E: Unit Weights ──────────────────────────────────────────────

        clickTab("Unit Weights"),

        // Wait for initial loadWeights() (no filter) to finish before adding
        // Timeout 30s: loadWeights() ORM call can take ~10s on full dataset.
        { trigger: ".pdp-manage-table tbody tr td:not([colspan])", timeout: 30000 },

        // Add row (default type/shape/shade/size pre-set from DB data)
        { trigger: ".pdp-manage .ms-auto .btn-secondary.btn-sm", run: "click" },

        // Fill weight — new row has defaults; just set the weight value
        {
            trigger: ".pdp-manage-table tbody tr:last-child input[type='number']",
            run: "edit 0.5",
        },

        // Save weights
        { trigger: ".pdp-manage .ms-auto .btn-primary.btn-sm:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
    ],
});

// ── Tour 2: Ornament Categories ───────────────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_ornament_categories", {
    url: "/web",
    steps: () => [
        ...goToPdpManage("pdp_frontend.menu_pdp_manage_categories"),

        // Topbar: Save btn-primary + Add btn-secondary (same pattern as all simple manage views)
        { trigger: ".pdp-manage-topbar .btn-secondary", run: "click" },

        { trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(1) input", run: "edit ORNT" },
        { trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(2) input", run: "edit Tour Ornament" },

        { trigger: ".pdp-manage-topbar .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
    ],
});
