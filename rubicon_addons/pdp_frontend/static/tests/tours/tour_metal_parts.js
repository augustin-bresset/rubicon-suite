/** @odoo-module **/
/**
 * Tour 3: pdp_tour_metal_manage — Complete Metals management
 *   Add metal WGOLD (cost=50.00) → save → edit cost to 55.00 → save
 *   Purities tab: add purity 18K (75%) → save
 *   Conversion Parameters tab: add parameter "Casting" → save
 *
 * Tour 4: pdp_tour_parts_manage — Complete Parts management
 *   Add part TPART (name=Tour Part) → save
 *   Select it → add cost row (cost=25.00) → save
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

/** Click a tab link by its visible text (metal_manage uses nav-tabs). */
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

// ── Tour 3: Complete Metal Management ────────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_metal_manage", {
    url: "/web",
    steps: () => [
        ...goToPdpManage("pdp_frontend.menu_pdp_manage_metals"),

        // ── Step A: Add a new metal ───────────────────────────────────────────

        // Topbar: Save btn-primary + "Add Metal" btn-secondary
        { trigger: ".pdp-manage-topbar .btn-secondary", run: "click" },

        // Code
        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(1) input",
            run: "edit WGOLD",
        },
        // Name
        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(2) input",
            run: "edit White Gold",
        },
        // Cost (initial: 50.00)
        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(3) input[type='number']",
            run: "edit 50",
        },

        // Save
        { trigger: ".pdp-manage-topbar .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step B: Edit the metal cost (50 → 55) ────────────────────────────

        // Click the WGOLD row to select it (first data row)
        {
            trigger: ".pdp-manage-table tbody tr:first-child td:first-child input",
            run: "edit 55",
        },

        // Save
        { trigger: ".pdp-manage-topbar .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step C: Purities tab → add 18K ───────────────────────────────────

        // First click the metal row to select it (needed to see Conversion Parameters)
        {
            trigger: ".pdp-manage-table tbody tr:first-child",
            run: "click",
        },

        clickTab("Purities"),

        { trigger: ".pdp-manage .btn-secondary:last-of-type", run: "click" },

        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(1) input",
            run: "edit 18K",
        },
        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(2) input[type='number']",
            run: "edit 75",
        },

        // Save (topbar Save covers metals + sub-tabs)
        { trigger: ".pdp-manage-topbar .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step D: Conversion Parameters tab → add "Casting" ────────────────

        clickTab("Conversion Parameters"),

        // "Add Parameter" is the only btn-secondary visible in this tab
        { trigger: ".pdp-manage .btn-secondary", run: "click" },

        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(1) input",
            run: "edit Casting",
        },

        // Save
        { trigger: ".pdp-manage-topbar .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
    ],
});

// ── Tour 4: Complete Parts Management ────────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_parts_manage", {
    url: "/web",
    steps: () => [
        ...goToPdpManage("pdp_frontend.menu_pdp_manage_parts"),

        // ── Step A: Add a new part ────────────────────────────────────────────

        // Parts sub-topbar: Save btn-primary + "Add" btn-secondary
        { trigger: ".pdp-manage .border-end .btn-secondary", run: "click" },

        // New part row shows inline inputs — new unsaved parts have me-auto (Name) / me-1 (Code) classes
        { trigger: ".pdp-manage .border-end input[placeholder='Name'].me-auto", run: "edit Tour Part" },
        { trigger: ".pdp-manage .border-end input[placeholder='Code'].me-1", run: "edit TPART" },

        // Save parts list
        { trigger: ".pdp-manage .border-end .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
        { trigger: ".o_notification_manager :not(.o_notification), .pdp-manage", timeout: 6000 },

        // ── Step B: Select the part to open its costs panel ───────────────────

        // After saving, the part has an id. Find the saved "Tour Part" row and click its wrapper div
        // (clicking inputs is stopped; we click the me-auto wrapper that doesn't stop propagation).
        {
            trigger: ".pdp-manage .border-end .me-auto.d-flex.flex-column",
            run(helpers) {
                for (const div of document.querySelectorAll(".pdp-manage .border-end .me-auto.d-flex.flex-column")) {
                    const inp = div.querySelector("input[placeholder='Name']");
                    if (inp && inp.value === "Tour Part") { div.click(); return; }
                }
                throw new Error("Tour Part not found in saved parts list");
            },
        },

        // ── Step C: Add a cost row ────────────────────────────────────────────

        // "Add Row" button in the costs panel (right side).
        // There are two btn-secondary elements (parts topbar "Add" + costs topbar "Add Row");
        // use a JS run to click by text so we target the correct one.
        {
            trigger: ".pdp-manage .btn-secondary.btn-sm",
            run(helpers) {
                for (const btn of document.querySelectorAll(".pdp-manage .btn-secondary.btn-sm")) {
                    if (btn.textContent.trim() === "Add Row") { btn.click(); return; }
                }
                throw new Error("Add Row button not found");
            },
        },

        // Fill cost (purity select can remain empty if not required by model)
        {
            trigger: ".pdp-manage-table tbody tr:last-child td:nth-child(2) input[type='number']",
            run: "edit 25",
        },

        // Save costs — parts Save is disabled after step A; only "Save Costs" btn is enabled
        { trigger: ".pdp-manage .btn-primary:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
    ],
});
