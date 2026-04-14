/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class AlloyManage extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.currencies = [];
        this._rawMetals = [];   // non-reactive lookup for component selects

        this._deletedMetalIds = [];
        this._deletedAlloyIds = [];
        this._deletedComponentIds = [];

        this.state = useState({
            activeTab: "raw_metals",
            metals: [],
            alloys: [],
            selectedAlloyKey: null,
            components: [],
            isDirty: false,
        });

        onWillStart(async () => {
            await this._loadAll();
        });
    }

    // ── Helpers ────────────────────────────────────────────────────

    m2oId(f) {
        return Array.isArray(f) ? f[0] : (f || false);
    }

    m2oName(f) {
        return Array.isArray(f) ? f[1] : '';
    }

    // ── Load ───────────────────────────────────────────────────────

    async _loadAll() {
        const [metals, alloys, currencies] = await Promise.all([
            this.orm.searchRead(
                'pdp.raw.metal', [],
                ['id', 'code', 'name', 'density', 'price', 'currency_id'],
                { order: 'code' }
            ),
            this.orm.searchRead(
                'pdp.alloy', [],
                ['id', 'code', 'name', 'purity', 'main_metal_id', 'total_ratio'],
                { order: 'code' }
            ),
            this.orm.searchRead(
                'res.currency', [['active', '=', true]],
                ['id', 'name'],
                { order: 'name' }
            ),
        ]);

        this.currencies = currencies;
        this._rawMetals = metals;

        this.state.metals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.alloys = alloys.map(r => ({ ...r, _key: r.id, _dirty: false }));

        if (this.state.selectedAlloyKey) {
            await this._loadComponents(this.state.selectedAlloyKey);
        } else {
            this.state.components = [];
        }
    }

    async _loadComponents(alloyKey) {
        const alloy = this.state.alloys.find(a => a._key === alloyKey);
        if (!alloy || !alloy.id) {
            this.state.components = [];
            return;
        }
        const comps = await this.orm.searchRead(
            'pdp.alloy.component',
            [['alloy_id', '=', alloy.id]],
            ['id', 'metal_id', 'ratio'],
            { order: 'ratio desc' }
        );
        this.state.components = comps.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    // ── Tab ────────────────────────────────────────────────────────

    setTab(tab) {
        if (this.state.isDirty) {
            this.notification.add("Save or discard changes first.", { type: "warning" });
            return;
        }
        this.state.activeTab = tab;
    }

    // ── Raw Metals ─────────────────────────────────────────────────

    onMetalFieldChange(row, field, ev) {
        if (field === 'density' || field === 'price') {
            row[field] = parseFloat(ev.target.value) || 0;
        } else if (field === 'currency_id') {
            row[field] = parseInt(ev.target.value) || false;
        } else {
            row[field] = ev.target.value;
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    addMetal() {
        const defaultCur = this.currencies.length ? this.currencies[0].id : false;
        this.state.metals.push({
            id: null, _key: -Date.now(), _dirty: true,
            code: '', name: '', density: 0.0, price: 0.0,
            currency_id: defaultCur || false,
        });
        this.state.isDirty = true;
    }

    removeMetal(row) {
        if (row.id) this._deletedMetalIds.push(row.id);
        const idx = this.state.metals.indexOf(row);
        if (idx !== -1) this.state.metals.splice(idx, 1);
        this.state.isDirty = true;
    }

    // ── Alloys ─────────────────────────────────────────────────────

    onAlloyFieldChange(row, field, ev) {
        if (field === 'main_metal_id') {
            row[field] = parseInt(ev.target.value) || false;
        } else {
            row[field] = ev.target.value;
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    addAlloy() {
        this.state.alloys.push({
            id: null, _key: -Date.now(), _dirty: true,
            code: '', name: '', purity: '', main_metal_id: false, total_ratio: 0,
        });
        this.state.isDirty = true;
    }

    removeAlloy(row) {
        if (row.id) this._deletedAlloyIds.push(row.id);
        const idx = this.state.alloys.indexOf(row);
        if (idx !== -1) this.state.alloys.splice(idx, 1);
        if (this.state.selectedAlloyKey === row._key) {
            this.state.selectedAlloyKey = null;
            this.state.components = [];
        }
        this.state.isDirty = true;
    }

    async selectAlloy(row) {
        if (this.state.isDirty) {
            this.notification.add("Save or discard changes first.", { type: "warning" });
            return;
        }
        this.state.selectedAlloyKey = row._key;
        await this._loadComponents(row._key);
    }

    get selectedAlloy() {
        return this.state.alloys.find(a => a._key === this.state.selectedAlloyKey) || null;
    }

    // ── Components ─────────────────────────────────────────────────

    onComponentFieldChange(row, field, ev) {
        if (field === 'metal_id') {
            row[field] = parseInt(ev.target.value) || false;
        } else if (field === 'ratio') {
            row[field] = parseFloat(ev.target.value) || 0;
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    addComponent() {
        const alloy = this.selectedAlloy;
        if (!alloy) return;
        this.state.components.push({
            id: null, _key: -Date.now(), _dirty: true,
            alloy_id: alloy.id || null,
            metal_id: false,
            ratio: 0.0,
        });
        this.state.isDirty = true;
    }

    removeComponent(row) {
        if (row.id) this._deletedComponentIds.push(row.id);
        const idx = this.state.components.indexOf(row);
        if (idx !== -1) this.state.components.splice(idx, 1);
        this.state.isDirty = true;
    }

    // ── Save / Discard ─────────────────────────────────────────────

    async saveAll() {
        try {
            if (this._deletedComponentIds.length) {
                await this.orm.unlink('pdp.alloy.component', this._deletedComponentIds);
                this._deletedComponentIds = [];
            }
            if (this._deletedAlloyIds.length) {
                await this.orm.unlink('pdp.alloy', this._deletedAlloyIds);
                this._deletedAlloyIds = [];
            }
            if (this._deletedMetalIds.length) {
                await this.orm.unlink('pdp.raw.metal', this._deletedMetalIds);
                this._deletedMetalIds = [];
            }

            for (const row of this.state.metals) {
                if (!row._dirty) continue;
                const vals = {
                    code: row.code,
                    name: row.name,
                    density: row.density || 0.0,
                    price: row.price || 0.0,
                    currency_id: this.m2oId(row.currency_id) || false,
                };
                if (row.id) {
                    await this.orm.write('pdp.raw.metal', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.raw.metal', [vals]);
                    row.id = newId;
                    row._key = newId;
                }
                row._dirty = false;
            }

            for (const row of this.state.alloys) {
                if (!row._dirty) continue;
                const vals = {
                    code: row.code,
                    name: row.name,
                    purity: row.purity || '',
                    main_metal_id: this.m2oId(row.main_metal_id) || false,
                };
                if (row.id) {
                    await this.orm.write('pdp.alloy', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.alloy', [vals]);
                    row.id = newId;
                    row._key = newId;
                }
                row._dirty = false;
            }

            const alloy = this.selectedAlloy;
            for (const row of this.state.components) {
                if (!row._dirty) continue;
                const vals = {
                    alloy_id: alloy ? alloy.id : (row.alloy_id || false),
                    metal_id: this.m2oId(row.metal_id) || false,
                    ratio: row.ratio || 0.0,
                };
                if (row.id) {
                    await this.orm.write('pdp.alloy.component', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.alloy.component', [vals]);
                    row.id = newId;
                    row._key = newId;
                }
                row._dirty = false;
            }

            this.state.isDirty = false;
            this.notification.add("Saved.", { type: "success" });
            await this._loadAll();
        } catch (e) {
            this.notification.add("Error: " + (e.data && e.data.message || e.message || e), { type: "danger" });
        }
    }

    async discardAll() {
        this._deletedMetalIds = [];
        this._deletedAlloyIds = [];
        this._deletedComponentIds = [];
        this.state.isDirty = false;
        await this._loadAll();
    }
}

AlloyManage.template = "pdp_alloy.alloy_manage";
registry.category("actions").add("pdp_alloy.alloy_manage", AlloyManage);
