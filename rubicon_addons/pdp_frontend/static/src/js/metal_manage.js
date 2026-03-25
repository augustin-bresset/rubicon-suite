/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class MetalManage extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this._deletedMetalIds = [];
        this._deletedParamIds = [];
        this._deletedPurityIds = [];

        // Non-reactive lookup loaded once
        this.currencies = [];

        this.state = useState({
            metals: [],
            parameters: [],
            purities: [],
            selectedMetalKey: null,
            activeTab: "conversion",
            isDirty: false,
        });

        onWillStart(async () => {
            await this._loadAll();
        });
    }

    async _loadAll() {
        const [metals, parameters, purities, currencies] = await Promise.all([
            this.orm.searchRead(
                "pdp.metal",
                [],
                ["id", "code", "name", "cost", "currency_id", "cost_method", "plating", "gold", "reference"],
                { order: "code asc" }
            ),
            this.orm.searchRead(
                "pdp.metal.parameter",
                [],
                ["id", "metal_id", "name", "loss_percentage", "risk_factor"],
                { order: "id asc" }
            ),
            this.orm.searchRead(
                "pdp.metal.purity",
                [],
                ["id", "code", "percent"],
                { order: "code asc" }
            ),
            this.orm.searchRead(
                "res.currency",
                [["active", "=", true]],
                ["id", "name"],
                { order: "name asc" }
            ),
        ]);

        this.currencies = currencies;

        this.state.metals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.parameters = parameters.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.purities = purities.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    m2oId(f) {
        return Array.isArray(f) ? f[0] : f;
    }

    get selectedMetal() {
        return this.state.metals.find(m => m._key === this.state.selectedMetalKey) || null;
    }

    get filteredParameters() {
        const m = this.selectedMetal;
        if (!m || !m.id) return [];
        return this.state.parameters.filter(p => this.m2oId(p.metal_id) === m.id);
    }

    get dirtyCount() {
        const dirtyMetals = this.state.metals.filter(r => r._dirty).length;
        const dirtyParams = this.state.parameters.filter(r => r._dirty).length;
        const dirtyPurities = this.state.purities.filter(r => r._dirty).length;
        return (
            dirtyMetals +
            dirtyParams +
            dirtyPurities +
            this._deletedMetalIds.length +
            this._deletedParamIds.length +
            this._deletedPurityIds.length
        );
    }

    // ── Metal methods ──────────────────────────────────────────────

    selectMetal(row) {
        this.state.selectedMetalKey = row._key;
    }

    addMetal() {
        const defaultCurrencyId = this.currencies.length ? this.currencies[0].id : null;
        this.state.metals.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            name: "",
            cost: 0,
            currency_id: defaultCurrencyId,
            cost_method: "fixed",
            plating: false,
            gold: true,
            reference: false,
        });
        this.state.isDirty = true;
    }

    removeMetal(row) {
        if (row.id) {
            this._deletedMetalIds.push(row.id);
        }
        const idx = this.state.metals.indexOf(row);
        if (idx !== -1) {
            this.state.metals.splice(idx, 1);
        }
        if (this.state.selectedMetalKey === row._key) {
            this.state.selectedMetalKey = null;
        }
        this.state.isDirty = true;
    }

    onMetalFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Parameter methods ──────────────────────────────────────────

    addParameter() {
        const m = this.selectedMetal;
        if (!m) return;
        this.state.parameters.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            metal_id: [m.id, m.code],
            name: "",
            loss_percentage: 0,
            risk_factor: 1.0,
        });
        this.state.isDirty = true;
    }

    removeParameter(row) {
        if (row.id) {
            this._deletedParamIds.push(row.id);
        }
        const idx = this.state.parameters.indexOf(row);
        if (idx !== -1) {
            this.state.parameters.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onParamFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Purity methods ─────────────────────────────────────────────

    addPurity() {
        this.state.purities.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            percent: 0,
        });
        this.state.isDirty = true;
    }

    removePurity(row) {
        if (row.id) {
            this._deletedPurityIds.push(row.id);
        }
        const idx = this.state.purities.indexOf(row);
        if (idx !== -1) {
            this.state.purities.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onPurityFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab ────────────────────────────────────────────────────────

    setTab(tab) {
        this.state.activeTab = tab;
    }

    // ── Save ───────────────────────────────────────────────────────

    _metalVals(r) {
        return {
            code: r.code,
            name: r.name,
            cost: parseFloat(r.cost) || 0,
            currency_id: this.m2oId(r.currency_id),
            cost_method: r.cost_method,
            plating: !!r.plating,
            gold: !!r.gold,
            reference: !!r.reference,
        };
    }

    _paramVals(r) {
        return {
            metal_id: this.m2oId(r.metal_id),
            name: r.name,
            loss_percentage: parseFloat(r.loss_percentage) || 0,
            risk_factor: parseFloat(r.risk_factor) || 1,
        };
    }

    _purityVals(r) {
        return {
            code: r.code,
            percent: parseFloat(r.percent) || 0,
        };
    }

    async saveAll() {
        try {
            // ── Metals ──────────────────────────────────────────
            if (this._deletedMetalIds.length) {
                await this.orm.unlink("pdp.metal", this._deletedMetalIds);
                this._deletedMetalIds = [];
            }

            const dirtyMetals = this.state.metals.filter(r => r._dirty && r.id);
            await Promise.all(
                dirtyMetals.map(r => this.orm.write("pdp.metal", [r.id], this._metalVals(r)))
            );
            for (const r of dirtyMetals) {
                r._dirty = false;
            }

            const newMetals = this.state.metals.filter(r => r.id === null);
            for (const r of newMetals) {
                const [newId] = await this.orm.create("pdp.metal", [this._metalVals(r)]);
                r.id = newId;
                r._key = newId;
                r._dirty = false;
            }

            // ── Parameters ──────────────────────────────────────
            if (this._deletedParamIds.length) {
                await this.orm.unlink("pdp.metal.parameter", this._deletedParamIds);
                this._deletedParamIds = [];
            }

            const dirtyParams = this.state.parameters.filter(r => r._dirty && r.id);
            await Promise.all(
                dirtyParams.map(r => this.orm.write("pdp.metal.parameter", [r.id], this._paramVals(r)))
            );
            for (const r of dirtyParams) {
                r._dirty = false;
            }

            const newParams = this.state.parameters.filter(r => r.id === null);
            for (const r of newParams) {
                const [newId] = await this.orm.create("pdp.metal.parameter", [this._paramVals(r)]);
                r.id = newId;
                r._key = newId;
                r._dirty = false;
            }

            // ── Purities ─────────────────────────────────────────
            if (this._deletedPurityIds.length) {
                await this.orm.unlink("pdp.metal.purity", this._deletedPurityIds);
                this._deletedPurityIds = [];
            }

            const dirtyPurities = this.state.purities.filter(r => r._dirty && r.id);
            await Promise.all(
                dirtyPurities.map(r => this.orm.write("pdp.metal.purity", [r.id], this._purityVals(r)))
            );
            for (const r of dirtyPurities) {
                r._dirty = false;
            }

            const newPurities = this.state.purities.filter(r => r.id === null);
            for (const r of newPurities) {
                const [newId] = await this.orm.create("pdp.metal.purity", [this._purityVals(r)]);
                r.id = newId;
                r._key = newId;
                r._dirty = false;
            }

            this.state.isDirty = false;

            this.notification.add("Saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }
}

MetalManage.template = "pdp_frontend.metal_manage";
registry.category("actions").add("pdp_frontend.metal_manage", MetalManage);
