/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class AlloyManage extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        // Non-reactive lookups
        this.currencies = [];

        // Non-reactive deleted-ID trackers
        this._deletedMetalIds = [];
        this._deletedAlloyIds = [];
        this._deletedComponentIds = [];
        this._deletedTypeIds = [];
        this._deletedPurityIds = [];

        this.state = useState({
            activeTab: "raw_metals",
            metals: [],
            types: [],
            purities: [],
            alloys: [],
            selectedAlloyKey: null,
            components: [],
            config: { id: null, reference_alloy_id: false, _dirty: false },
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

    get componentTotal() {
        return this.state.components.reduce((s, c) => s + (c.ratio || 0), 0);
    }

    // ── Load ───────────────────────────────────────────────────────

    async _loadAll() {
        await this.orm.call('pdp.config', 'get_singleton', []);
        const [metals, types, purities, alloys, currencies, configs] = await Promise.all([
            this.orm.searchRead(
                'pdp.raw.metal', [],
                ['id', 'code', 'name', 'density', 'price', 'currency_id'],
                { order: 'code' }
            ),
            this.orm.searchRead(
                'pdp.alloy.type', [],
                ['id', 'code', 'name', 'main_metal_id', 'purity_system'],
                { order: 'code' }
            ),
            this.orm.searchRead(
                'pdp.alloy.purity', [],
                ['id', 'code', 'percent', 'purity_system'],
                { order: 'percent desc' }
            ),
            this.orm.searchRead(
                'pdp.alloy', [],
                ['id', 'code', 'name', 'type_id', 'purity_id', 'variant', 'density', 'total_ratio'],
                { order: 'code' }
            ),
            this.orm.searchRead(
                'res.currency', [['active', '=', true]],
                ['id', 'name'],
                { order: 'name' }
            ),
            this.orm.searchRead(
                'pdp.config', [],
                ['id', 'reference_alloy_id'],
                { limit: 1 }
            ),
        ]);

        this.currencies = currencies;

        if (configs.length) {
            const c = configs[0];
            this.state.config = { id: c.id, reference_alloy_id: c.reference_alloy_id, _dirty: false };
        }

        this.state.metals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.types = types.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.purities = purities.map(r => ({ ...r, _key: r.id, _dirty: false }));
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
        this.state.metals.splice(this.state.metals.indexOf(row), 1);
        this.state.isDirty = true;
    }

    // ── Alloy Types ────────────────────────────────────────────────

    onTypeFieldChange(row, field, ev) {
        if (field === 'main_metal_id') {
            row[field] = parseInt(ev.target.value) || false;
        } else {
            row[field] = ev.target.value;
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    addType() {
        this.state.types.push({
            id: null, _key: -Date.now(), _dirty: true,
            code: '', name: '', main_metal_id: false, purity_system: 'millesimal',
        });
        this.state.isDirty = true;
    }

    removeType(row) {
        if (row.id) this._deletedTypeIds.push(row.id);
        this.state.types.splice(this.state.types.indexOf(row), 1);
        this.state.isDirty = true;
    }

    // ── Purities ───────────────────────────────────────────────────

    onPurityFieldChange(row, field, ev) {
        if (field === 'percent') {
            row[field] = parseFloat(ev.target.value) || 0;
        } else {
            row[field] = ev.target.value;
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    addPurity() {
        this.state.purities.push({
            id: null, _key: -Date.now(), _dirty: true,
            code: '', percent: 0.0, purity_system: 'millesimal',
        });
        this.state.isDirty = true;
    }

    removePurity(row) {
        if (row.id) this._deletedPurityIds.push(row.id);
        this.state.purities.splice(this.state.purities.indexOf(row), 1);
        this.state.isDirty = true;
    }

    // ── Alloys ─────────────────────────────────────────────────────

    onConfigChange(ev) {
        this.state.config.reference_alloy_id = parseInt(ev.target.value) || false;
        this.state.config._dirty = true;
        this.state.isDirty = true;
    }

    filteredPuritiesForAlloy(row) {
        const typeId = this.m2oId(row.type_id);
        if (!typeId) return this.state.purities;
        const type = this.state.types.find(t => t.id === typeId);
        if (!type || !type.purity_system) return this.state.purities;
        return this.state.purities.filter(p => p.purity_system === type.purity_system);
    }

    onAlloyFieldChange(row, field, ev) {
        if (field === 'variant') {
            row[field] = ev.target.value;
        } else {
            row[field] = parseInt(ev.target.value) || false;
        }
        // If type changed, clear purity if incompatible with new type's system
        if (field === 'type_id' && row.purity_id) {
            const purityId = this.m2oId(row.purity_id);
            const allowed = this.filteredPuritiesForAlloy(row);
            if (!allowed.find(p => p.id === purityId)) {
                row.purity_id = false;
            }
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    addAlloy() {
        this.state.alloys.push({
            id: null, _key: -Date.now(), _dirty: true,
            code: '', name: '', type_id: false, purity_id: false, variant: '', total_ratio: 0,
        });
        this.state.isDirty = true;
    }

    removeAlloy(row) {
        if (row.id) this._deletedAlloyIds.push(row.id);
        this.state.alloys.splice(this.state.alloys.indexOf(row), 1);
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
        this.state.components.splice(this.state.components.indexOf(row), 1);
        this.state.isDirty = true;
    }

    // ── Save / Discard ─────────────────────────────────────────────

    async saveAll() {
        // Block save if any composition exceeds 1.0
        const total = this.componentTotal;
        if (total > 1.0 + 1e-9) {
            this.notification.add(
                `Composition total is ${total.toFixed(4)} — cannot exceed 1.0.`,
                { type: "danger" }
            );
            return;
        }

        try {
            if (this.state.config._dirty && this.state.config.id) {
                await this.orm.write('pdp.config', [this.state.config.id], {
                    reference_alloy_id: this.m2oId(this.state.config.reference_alloy_id) || false,
                });
                this.state.config._dirty = false;
            }

            if (this._deletedComponentIds.length) {
                await this.orm.unlink('pdp.alloy.component', this._deletedComponentIds);
                this._deletedComponentIds = [];
            }
            if (this._deletedAlloyIds.length) {
                await this.orm.unlink('pdp.alloy', this._deletedAlloyIds);
                this._deletedAlloyIds = [];
            }
            if (this._deletedTypeIds.length) {
                await this.orm.unlink('pdp.alloy.type', this._deletedTypeIds);
                this._deletedTypeIds = [];
            }
            if (this._deletedPurityIds.length) {
                await this.orm.unlink('pdp.alloy.purity', this._deletedPurityIds);
                this._deletedPurityIds = [];
            }
            if (this._deletedMetalIds.length) {
                await this.orm.unlink('pdp.raw.metal', this._deletedMetalIds);
                this._deletedMetalIds = [];
            }

            for (const row of this.state.metals) {
                if (!row._dirty) continue;
                const vals = {
                    code: row.code, name: row.name,
                    density: row.density || 0.0, price: row.price || 0.0,
                    currency_id: this.m2oId(row.currency_id) || false,
                };
                if (row.id) {
                    await this.orm.write('pdp.raw.metal', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.raw.metal', [vals]);
                    row.id = newId; row._key = newId;
                }
                row._dirty = false;
            }

            for (const row of this.state.types) {
                if (!row._dirty) continue;
                const vals = {
                    code: row.code,
                    name: row.name,
                    main_metal_id: this.m2oId(row.main_metal_id) || false,
                    purity_system: row.purity_system || false,
                };
                if (row.id) {
                    await this.orm.write('pdp.alloy.type', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.alloy.type', [vals]);
                    row.id = newId; row._key = newId;
                }
                row._dirty = false;
            }

            for (const row of this.state.purities) {
                if (!row._dirty) continue;
                const vals = {
                    code: row.code,
                    percent: row.percent || 0.0,
                    purity_system: row.purity_system || 'millesimal',
                };
                if (row.id) {
                    await this.orm.write('pdp.alloy.purity', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.alloy.purity', [vals]);
                    row.id = newId; row._key = newId;
                }
                row._dirty = false;
            }

            for (const row of this.state.alloys) {
                if (!row._dirty) continue;
                const vals = {
                    type_id: this.m2oId(row.type_id) || false,
                    purity_id: this.m2oId(row.purity_id) || false,
                    variant: row.variant || '',
                };
                if (row.id) {
                    await this.orm.write('pdp.alloy', [row.id], vals);
                } else {
                    const newId = await this.orm.create('pdp.alloy', [vals]);
                    row.id = newId; row._key = newId;
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
                    row.id = newId; row._key = newId;
                }
                row._dirty = false;
            }

            // Warn (but don't block) if composition is incomplete
            if (this.state.components.length > 0 && total < 1.0 - 1e-9) {
                this.notification.add(
                    `Saved. Composition total is ${total.toFixed(4)} — not yet complete.`,
                    { type: "warning" }
                );
            } else {
                this.notification.add("Saved.", { type: "success" });
            }
            this.state.isDirty = false;
            await this._loadAll();
        } catch (e) {
            this.notification.add(
                "Error: " + (e.data && e.data.message || e.message || e),
                { type: "danger" }
            );
        }
    }

    async discardAll() {
        this._deletedMetalIds = [];
        this._deletedAlloyIds = [];
        this._deletedComponentIds = [];
        this._deletedTypeIds = [];
        this._deletedPurityIds = [];
        this.state.isDirty = false;
        await this._loadAll();
    }
}

AlloyManage.template = "pdp_frontend.alloy_manage";
registry.category("actions").add("pdp_frontend.alloy_manage", AlloyManage);
