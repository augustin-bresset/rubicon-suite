/** @odoo-module **/
/**
 * Tour 5: pdp_tour_workspace_nav — Workspace navigation + labor cost
 *   Select model TOUR-MDL → click product TOUR-PROD → switch tabs
 *   Labor tab: add a model-level labor cost row
 *   Save all
 *
 * Tour 6: pdp_tour_workspace_invalid_stone — Invalid stone code warning
 *   Navigate to workspace → Stones tab → enter invalid code → blur → verify warning
 *
 * Tour 7: pdp_tour_margin_create — Margin creation via Manage > Margins
 *   Create margin TOUR-MAR-01 → verify in list
 */
import { registry } from "@web/core/registry";

// ── Shared helpers ────────────────────────────────────────────────────────────

function goToPdpRoot() {
    return [
        // Odoo 18 community: apps live in a navbar dropdown, not a separate home screen
        { trigger: ".o_navbar_apps_menu .dropdown-toggle", run: "click" },
        { trigger: ".o-dropdown--menu .o_app[data-menu-xmlid='pdp_frontend.menu_pdp_frontend_root']", run: "click" },
        { trigger: ".pdp-workspace" },
    ];
}

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

/** Select model TOUR-MDL in the workspace model dropdown. */
function selectTourModel() {
    return [
        {
            // By the time .pdp-workspace is visible, models are already loaded in the select
            trigger: ".pdp-workspace .shadow-sm .form-select",
            run: "selectByLabel TOUR-MDL",
        },
    ];
}

/** Click the TOUR-PROD row in the products table (waits for actual data rows). */
function selectTourProduct() {
    return [
        // td:not([colspan]) = real data cell (not the "No products" placeholder)
        {
            trigger: ".pdp-workspace .border-end.overflow-auto tbody tr td:not([colspan])",
            run: "click",
        },
    ];
}

/** Click a workspace tab by its visible text. */
function clickWorkspaceTab(text) {
    return {
        trigger: ".pdp-workspace .nav-tabs .nav-link",
        run: () => {
            for (const a of document.querySelectorAll(".pdp-workspace .nav-tabs .nav-link")) {
                if (a.textContent.trim() === text) { a.click(); return; }
            }
        },
    };
}

// ── Tour 5: Workspace Navigation + Labor ─────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_workspace_nav", {
    url: "/web",
    steps: () => [
        ...goToPdpRoot(),
        ...selectTourModel(),
        ...selectTourProduct(),

        // Default tab "Costing" is active
        { trigger: ".pdp-workspace .nav-tabs .nav-link.fw-bold" },

        // Switch to Stones tab, verify it loads
        clickWorkspaceTab("Stones"),
        { trigger: ".pdp-workspace .nav-tabs .nav-link.fw-bold" },

        // Switch to Labor etc. tab
        clickWorkspaceTab("Labor etc."),
        { trigger: ".pdp-workspace .nav-tabs .nav-link.fw-bold" },

        // Add a labor cost at model level
        { trigger: ".pdp-workspace .btn-outline-success:first-of-type", run: "click" },

        // Fill cost field in new row
        {
            trigger: ".pdp-workspace [class*='row'] table tbody tr:last-child input[type='number']:first-of-type",
            run: "edit 120",
        },

        // Save all via the main Save button
        { trigger: ".pdp-workspace .btn-primary.fw-bold:not(:disabled)", run: "click" },
        { trigger: ".o_notification" },
    ],
});

// ── Tour 6: Invalid Stone Warning ─────────────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_workspace_invalid_stone", {
    url: "/web",
    steps: () => [
        ...goToPdpRoot(),
        ...selectTourModel(),
        ...selectTourProduct(),

        clickWorkspaceTab("Stones"),

        // Add a new stone row
        { trigger: ".pdp-workspace .btn-outline-success", run: "click" },

        // Type an invalid stone code
        { trigger: ".pdp-workspace input[placeholder='Code...']", run: "edit INVALID-STONE-XXXX" },

        // Blur triggers validateStoneCode (async ORM lookup)
        { trigger: ".pdp-workspace input[placeholder='Code...']", run: "press Tab" },

        // Warning notification: 'Pierre "INVALID-STONE-XXXX" introuvable.'
        { trigger: ".o_notification" },
    ],
});

// ── Tour 7: Margin Creation ───────────────────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_margin_create", {
    url: "/web",
    steps: () => [
        ...goToPdpManage("pdp_frontend.menu_pdp_manage_margins"),

        // Click "+ New Margin" (btn-outline-secondary in topbar)
        { trigger: ".pdp-manage-topbar .btn-outline-secondary", run: "click" },

        // Fill code and name in the inline form
        { trigger: ".pdp-manage input[placeholder='Code']", run: "edit TOUR-MAR-01" },
        { trigger: ".pdp-manage input[placeholder='Name']", run: "edit Tour Margin Test" },

        // Click Create
        { trigger: ".pdp-manage .btn-primary", run: "click" },

        // Verify the new margin is selected in the list (selected item gets bg-primary class)
        { trigger: ".pdp-margins-list .pdp-list-item.bg-primary" },
    ],
});
