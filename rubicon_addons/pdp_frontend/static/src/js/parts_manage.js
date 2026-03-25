/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class PartsManage extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        // Non-reactive lookups loaded once
        this.currencies = [];
        this.purities = [];

        // Non-reactive deleted-ID tracking
        this._deletedPartIds = [];
        this._deletedCostIds = [];

        this.state = useState({
            parts: [],
            costs: [],
            selectedPartId: null,
            isDirtyParts: false,
            isDirtyCosts: false,
        });

        onWillStart(async () => {
            await this._loadAll();
        });
    }

    // ── Helpers ────────────────────────────────────────────────────

    m2oId(f) {
        return Array.isArray(f) ? f[0] : f;
    }

    m2oName(f) {
        return Array.isArray(f) ? f[1] : "";
    }

    get selectedPart() {
        return this.state.parts.find(p => p.id === this.state.selectedPartId) || null;
    }

    get dirtyPartsCount() {
        return this.state.parts.filter(r => r._dirty).length + this._deletedPartIds.length;
    }

    get dirtyCostsCount() {
        return this.state.costs.filter(r => r._dirty).length + this._deletedCostIds.length;
    }

    // ── Load ───────────────────────────────────────────────────────

    async _loadAll() {
        const [parts, purities, currencies] = await Promise.all([
            this.orm.searchRead(
                "pdp.part",
                [],
                ["id", "code", "name"],
                { order: "name asc" }
            ),
            this.orm.searchRead(
                "pdp.metal.purity",
                [],
                ["id", "code", "percent"],
                { order: "percent desc" }
            ),
            this.orm.searchRead(
                "res.currency",
                [["active", "=", true]],
                ["id", "name", "symbol"],
                { order: "name asc" }
            ),
        ]);

        this.purities = purities;
        this.currencies = currencies;

        this.state.parts = parts.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    async _loadCostsForPart(partId) {
        const records = await this.orm.searchRead(
            "pdp.part.cost",
            [["part_id", "=", partId]],
            ["id", "part_id", "purity_id", "cost", "currency_id"],
            { order: "id asc" }
        );
        this.state.costs = records.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this._deletedCostIds = [];
        this.state.isDirtyCosts = false;
    }

    // ── Parts ──────────────────────────────────────────────────────

    async selectPart(partId) {
        this.state.selectedPartId = partId;
        await this._loadCostsForPart(partId);
    }

    addPart() {
        this.state.parts.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            name: "",
        });
        this.state.isDirtyParts = true;
    }

    removePart(row) {
        if (row.id) {
            this._deletedPartIds.push(row.id);
        }
        const idx = this.state.parts.indexOf(row);
        if (idx !== -1) {
            this.state.parts.splice(idx, 1);
        }
        if (this.state.selectedPartId === row.id) {
            this.state.selectedPartId = null;
            this.state.costs = [];
            this._deletedCostIds = [];
            this.state.isDirtyCosts = false;
        }
        this.state.isDirtyParts = true;
    }

    onPartFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirtyParts = true;
    }

    // ── Costs ──────────────────────────────────────────────────────

    addCostRow() {
        const defCurrency = this.currencies.length
            ? [this.currencies[0].id, this.currencies[0].name]
            : false;
        this.state.costs.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            part_id: [this.state.selectedPartId, ""],
            purity_id: this.purities.length ? [this.purities[0].id, this.purities[0].code] : false,
            cost: 0,
            currency_id: defCurrency,
        });
        this.state.isDirtyCosts = true;
    }

    removeCostRow(row) {
        if (row.id) {
            this._deletedCostIds.push(row.id);
        }
        const idx = this.state.costs.indexOf(row);
        if (idx !== -1) {
            this.state.costs.splice(idx, 1);
        }
        this.state.isDirtyCosts = true;
    }

    onCostFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirtyCosts = true;
    }

    // ── Save ───────────────────────────────────────────────────────

    _partVals(r) {
        return {
            code: r.code,
            name: r.name,
        };
    }

    _costVals(r) {
        return {
            part_id: this.m2oId(r.part_id) || this.state.selectedPartId,
            purity_id: this.m2oId(r.purity_id) || false,
            cost: parseFloat(r.cost) || 0,
            currency_id: this.m2oId(r.currency_id) || false,
        };
    }

    async saveParts() {
        try {
            if (this._deletedPartIds.length) {
                await this.orm.unlink("pdp.part", this._deletedPartIds);
                this._deletedPartIds = [];
            }

            const dirtyExisting = this.state.parts.filter(r => r._dirty && r.id);
            await Promise.all(
                dirtyExisting.map(r => this.orm.write("pdp.part", [r.id], this._partVals(r)))
            );
            for (const r of dirtyExisting) {
                r._dirty = false;
            }

            const newRows = this.state.parts.filter(r => r.id === null);
            for (const r of newRows) {
                const [newId] = await this.orm.create("pdp.part", [this._partVals(r)]);
                r.id = newId;
                r._key = newId;
                r._dirty = false;
            }

            this.state.isDirtyParts = false;
            this.notification.add("Parts saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }

    async saveCosts() {
        try {
            if (this._deletedCostIds.length) {
                await this.orm.unlink("pdp.part.cost", this._deletedCostIds);
                this._deletedCostIds = [];
            }

            const dirtyExisting = this.state.costs.filter(r => r._dirty && r.id);
            await Promise.all(
                dirtyExisting.map(r => this.orm.write("pdp.part.cost", [r.id], this._costVals(r)))
            );
            for (const r of dirtyExisting) {
                r._dirty = false;
            }

            const newRows = this.state.costs.filter(r => r.id === null);
            for (const r of newRows) {
                const vals = this._costVals(r);
                vals.part_id = this.state.selectedPartId;
                const [newId] = await this.orm.create("pdp.part.cost", [vals]);
                r.id = newId;
                r._key = newId;
                r._dirty = false;
            }

            this.state.isDirtyCosts = false;
            this.notification.add("Costs saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }
}

PartsManage.template = "pdp_frontend.parts_manage";
registry.category("actions").add("pdp_frontend.parts_manage", PartsManage);
