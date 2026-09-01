/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class PsUtilities extends Component {
    setup() {
        this.orm = useService("orm");

        // Which screen to show is set by the menu action's context.
        const screen = this.props.action?.context?.screen || "invoice";

        this.state = useState({
            view: screen,          // invoice | parts

            // Invoice Select
            invoices: [],
            selectedInvoiceId: null,
            designs: [],

            // Parts Update
            parts: [],
            partsModel: "",
            partsFilterPartId: "",
            partRows: [],
            partsTargetId: "",
            selectedRowIds: {},    // product-part id -> bool
        });

        onWillStart(async () => {
            if (this.state.view === "invoice") {
                this.state.invoices = await this.orm.call("ps.utilities", "get_invoices", []);
            } else {
                this.state.parts = await this.orm.call("ps.utilities", "get_parts", []);
            }
        });
    }

    // ── Invoice Select ─────────────────────────────────────────────────────
    onInvoiceChange(ev) {
        const v = parseInt(ev.target.value);
        this.state.selectedInvoiceId = isNaN(v) ? null : v;
        this.state.designs = [];
    }

    async onSelectDesigns() {
        if (!this.state.selectedInvoiceId) return;
        this.state.designs = await this.orm.call(
            "ps.utilities", "get_invoice_designs", [this.state.selectedInvoiceId]);
    }

    // ── Parts Update ───────────────────────────────────────────────────────
    onModelInput(ev) {
        this.state.partsModel = ev.target.value;
    }

    onPartFilterChange(ev) {
        this.state.partsFilterPartId = ev.target.value;
    }

    onTargetChange(ev) {
        this.state.partsTargetId = ev.target.value;
    }

    async onSearchParts() {
        const partId = this.state.partsFilterPartId
            ? parseInt(this.state.partsFilterPartId) : null;
        this.state.partRows = await this.orm.call(
            "ps.utilities", "search_product_parts",
            [this.state.partsModel || null, partId]);
        this.state.selectedRowIds = {};
    }

    toggleRow(id, ev) {
        this.state.selectedRowIds[id] = ev.target.checked;
    }

    get selectedRowCount() {
        return this.state.partRows.filter(r => this.state.selectedRowIds[r.id]).length;
    }

    async onUpdateParts() {
        const ids = this.state.partRows
            .filter(r => this.state.selectedRowIds[r.id])
            .map(r => r.id);
        if (ids.length === 0 || !this.state.partsTargetId) return;
        await this.orm.call("ps.utilities", "update_product_parts",
            [ids, parseInt(this.state.partsTargetId)]);
        await this.onSearchParts();
    }
}

PsUtilities.template = "ps_utilities.PsUtilities";

registry.category("actions").add("ps_utilities_action", PsUtilities);
