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
            invoiceSearch: "",
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
    // A visible search input backed by a datalist: the user sees what they
    // type; an exact name (or a text matching a single invoice) resolves it.

    get filteredInvoices() {
        const q = (this.state.invoiceSearch || "").trim().toLowerCase();
        const list = q
            ? this.state.invoices.filter((i) => i.name.toLowerCase().includes(q))
            : this.state.invoices;
        return list.slice(0, 300);
    }

    _resolveInvoice(text) {
        const q = (text || "").trim().toLowerCase();
        if (!q) return null;
        const exact = this.state.invoices.find((i) => i.name.toLowerCase() === q);
        if (exact) return exact.id;
        const hits = this.state.invoices.filter((i) => i.name.toLowerCase().includes(q));
        return hits.length === 1 ? hits[0].id : null;
    }

    onInvoiceSearchInput(ev) {
        this.state.invoiceSearch = ev.target.value;
        const resolved = this._resolveInvoice(ev.target.value);
        if (resolved !== this.state.selectedInvoiceId) {
            this.state.selectedInvoiceId = resolved;
            this.state.designs = [];
        }
    }

    async onInvoiceSearchChange(ev) {
        // Fires on a datalist pick (and on blur): load right away when resolved.
        this.onInvoiceSearchInput(ev);
        if (this.state.selectedInvoiceId && !this.state.designs.length) {
            await this.onSelectDesigns();
        }
    }

    onInvoiceKeydown(ev) {
        if (ev.key === "Enter" && this.state.selectedInvoiceId) {
            this.onSelectDesigns();
        }
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
