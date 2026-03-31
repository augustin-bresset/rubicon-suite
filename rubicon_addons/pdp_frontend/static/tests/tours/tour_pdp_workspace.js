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
 *
 * Tour 8: pdp_tour_picture_manage — Upload + delete (model scope)
 *   Select TOUR-MDL (no product) → inject 1×1 PNG → verify displayed →
 *   open manager → verify 1 photo → close manager → delete via trash → placeholder returns
 *
 * Tour 9: pdp_tour_picture_switch — Switch active photo in manager
 *   TOUR-PIX-MDL / TOUR-PIX-PROD has 2 pre-existing photos
 *   Open manager → click non-active photo → eye icon moves → close
 *
 * Tour 10: pdp_tour_picture_delete_manager — Delete photo via manager trash
 *   TOUR-PIX-MDL / TOUR-PIX-PROD has 2 pre-existing photos
 *   Open manager → trash non-active photo → 1 remains → close
 */
import { registry } from "@web/core/registry";

// ── Shared helpers ────────────────────────────────────────────────────────────

function goToPdpRoot() {
    return [
        { trigger: ".o_navbar_apps_menu .dropdown-toggle", run: "click" },
        { trigger: ".o-dropdown--menu .o_app[data-menu-xmlid='pdp_frontend.menu_pdp_frontend_root']", run: "click" },
        { trigger: ".pdp-workspace" },
    ];
}

function goToPdpManage(subMenuXmlId) {
    return [
        { trigger: ".o_navbar_apps_menu .dropdown-toggle", run: "click" },
        { trigger: ".o-dropdown--menu .o_app[data-menu-xmlid='pdp_frontend.menu_pdp_frontend_root']", run: "click" },
        { trigger: "[data-menu-xmlid='pdp_frontend.menu_pdp_frontend_manage']", run: "click" },
        { trigger: `[data-menu-xmlid='${subMenuXmlId}']`, run: "click" },
        { trigger: ".pdp-manage" },
    ];
}

function selectModel(code) {
    return [{
        trigger: ".pdp-workspace .shadow-sm .form-select",
        run: `selectByLabel ${code}`,
    }];
}

/** Click the first (only) product row in the products table. */
function selectFirstProduct() {
    return [{
        trigger: ".pdp-workspace .border-end.overflow-auto tbody tr td:not([colspan])",
        run: "click",
    }];
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

/** Inject a minimal 1×1 PNG into the hidden file input and fire the change event. */
function injectPhoto(inputId) {
    const b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
    const raw = atob(b64);
    const buf = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) buf[i] = raw.charCodeAt(i);
    const file = new File([buf], "tour_photo.png", { type: "image/png" });
    const dt = new DataTransfer();
    dt.items.add(file);
    const input = document.getElementById(inputId);
    input.files = dt.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
}

// ── Tour 5: Workspace Navigation + Labor ─────────────────────────────────────

registry.category("web_tour.tours").add("pdp_tour_workspace_nav", {
    url: "/web",
    steps: () => [
        ...goToPdpRoot(),
        ...selectModel("TOUR-MDL"),
        ...selectFirstProduct(),

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
        ...selectModel("TOUR-MDL"),
        ...selectFirstProduct(),

        clickWorkspaceTab("Stones"),

        // Add a new stone row
        { trigger: ".pdp-workspace .btn-outline-success", run: "click" },

        // Type an invalid stone code
        { trigger: ".pdp-workspace input[placeholder='Code...']", run: "edit INVALID-STONE-XXXX" },

        // Blur triggers validateStoneCode (async ORM lookup)
        { trigger: ".pdp-workspace input[placeholder='Code...']", run: "press Tab" },

        // Warning notification
        { trigger: ".o_notification" },
    ],
});

// ── Tour 8: Picture Upload + Delete (model scope, no product selected) ────────

registry.category("web_tour.tours").add("pdp_tour_picture_manage", {
    url: "/web",
    steps: () => [
        ...goToPdpRoot(),
        ...selectModel("TOUR-MDL"),
        // No product selected → model-scope upload

        // Placeholder "+" button appears when no picture exists
        {
            trigger: ".pdp-workspace .btn-outline-secondary.rounded-circle",
            run() { injectPhoto("pdp-upload-image_1920"); },
        },

        // Image is now displayed
        { trigger: ".pdp-workspace img[src*='pdp.picture']", timeout: 10000 },

        // Open picture manager (button with title "Manage photos")
        { trigger: ".pdp-workspace button[title='Manage photos']", run: "click" },

        // Modal is open — 1 photo with "Model" badge
        { trigger: ".pdp-picture-manager .pdp-pic-item" },
        { trigger: ".pdp-picture-manager .badge", run() {
            const badge = document.querySelector(".pdp-picture-manager .badge");
            if (!badge?.textContent.includes("Model")) throw new Error("Expected Model badge");
        }},

        // Close manager
        { trigger: ".pdp-picture-manager .btn-close", run: "click" },

        // Delete via the trash button below the image
        {
            trigger: ".pdp-workspace .btn.btn-sm.btn-light.border.text-danger",
            run: "click",
        },

        // Placeholder returns after deletion
        { trigger: ".pdp-workspace .btn-outline-secondary.rounded-circle", timeout: 5000 },
    ],
});

// ── Tour 9: Switch Active Photo in Manager ────────────────────────────────────
/**
 * TOUR-PIX-MDL / TOUR-PIX-PROD has 2 pre-existing product photos (from setUpClass).
 * Opens the manager, clicks the non-active photo, verifies the eye icon moves.
 */

registry.category("web_tour.tours").add("pdp_tour_picture_switch", {
    url: "/web",
    steps: () => [
        ...goToPdpRoot(),
        ...selectModel("TOUR-PIX-MDL"),
        ...selectFirstProduct(),

        // At least one photo is displayed (pre-created in setUpClass)
        { trigger: ".pdp-workspace img[src*='pdp.picture']", timeout: 8000 },

        // Open picture manager
        { trigger: ".pdp-workspace button[title='Manage photos']", run: "click" },

        // Modal open — at least 2 photos
        { trigger: ".pdp-picture-manager .pdp-pic-item" },

        // Click the non-active photo (no border-primary class)
        {
            trigger: ".pdp-picture-manager .pdp-pic-item:not(.border-primary)",
            run: "click",
        },

        // Eye icon now on the newly-selected photo
        { trigger: ".pdp-picture-manager .pdp-pic-item.border-primary .fa-eye" },

        // Close manager
        { trigger: ".pdp-picture-manager .btn-close", run: "click" },

        // Photo still displayed
        { trigger: ".pdp-workspace img[src*='pdp.picture']" },
    ],
});

// ── Tour 10: Delete Photo via Manager Trash Button ────────────────────────────
/**
 * TOUR-PIX-MDL / TOUR-PIX-PROD has 2 pre-existing product photos.
 * Opens manager, deletes the non-active photo via its trash button,
 * verifies only 1 remains, then closes the manager.
 */

registry.category("web_tour.tours").add("pdp_tour_picture_delete_manager", {
    url: "/web",
    steps: () => [
        ...goToPdpRoot(),
        ...selectModel("TOUR-PIX-MDL"),
        ...selectFirstProduct(),

        // Photo is displayed
        { trigger: ".pdp-workspace img[src*='pdp.picture']", timeout: 8000 },

        // Open picture manager
        { trigger: ".pdp-workspace button[title='Manage photos']", run: "click" },

        // Modal open — 2 photos visible
        { trigger: ".pdp-picture-manager .pdp-pic-item:not(.border-primary)" },

        // Click trash on the non-active photo (t-on-click.stop prevents row activation)
        {
            trigger: ".pdp-picture-manager .pdp-pic-item:not(.border-primary) .btn-outline-danger",
            run: "click",
        },

        // Only the active photo remains (border-primary) — non-active is gone
        { trigger: ".pdp-picture-manager .pdp-pic-item.border-primary .fa-eye" },

        // Close manager
        { trigger: ".pdp-picture-manager .btn-close", run: "click" },

        // Active photo still displayed
        { trigger: ".pdp-workspace img[src*='pdp.picture']" },
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

        // Verify the new margin is selected in the list
        { trigger: ".pdp-margins-list .pdp-list-item.bg-primary" },
    ],
});
