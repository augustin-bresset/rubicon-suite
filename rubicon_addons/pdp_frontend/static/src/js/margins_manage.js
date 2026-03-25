/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class MarginsManage extends Component {
    static template = "pdp_frontend.margins_manage";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        // Non-reactive lookups
        this.laborTypes = [];
        this.addonTypes = [];
        this.purities = [];
        this.stoneCategories = [];
        this.stoneTypes = [];
        this.currencies = [];

        // Deleted ID trackers
        this._deletedLaborIds = [];
        this._deletedAddonIds = [];
        this._deletedMetalIds = [];
        this._deletedStoneCondIds = [];
        this._deletedStoneNormIds = [];

        this.state = useState({
            margins: [],
            selectedMarginId: null,

            marginCode: "",
            marginName: "",
            marginHeaderDirty: false,

            activeTab: "misc",
            stoneSubTab: "conditional",
            stoneCatFilter: "",

            partRate: null,
            labors: [],
            addons: [],
            metals: [],
            stonesConditional: [],
            stonesNormal: [],

            isDirty: false,

            showNewMarginForm: false,
            newMarginCode: "",
            newMarginName: "",
        });

        onWillStart(async () => {
            await this._loadAll();
        });
    }

    async _loadAll() {
        const [margins, laborTypes, addonTypes, purities, stoneCategories, stoneTypes, currencies] =
            await Promise.all([
                this.orm.searchRead("pdp.margin", [], ["id", "code", "name"], { order: "code asc" }),
                this.orm.searchRead("pdp.labor.type", [], ["id", "code", "name"], { order: "code asc" }),
                this.orm.searchRead("pdp.addon.type", [], ["id", "code", "name"], { order: "code asc" }),
                this.orm.searchRead("pdp.metal.purity", [], ["id", "code", "percent"], { order: "percent desc" }),
                this.orm.searchRead("pdp.stone.category", [], ["id", "code", "name"], { order: "code asc" }),
                this.orm.searchRead("pdp.stone.type", [], ["id", "code", "name", "category_id"], { order: "code asc" }),
                this.orm.searchRead("res.currency", [["active", "=", true]], ["id", "name", "symbol"]),
            ]);
        this.state.margins = margins;
        this.laborTypes = laborTypes;
        this.addonTypes = addonTypes;
        this.purities = purities;
        this.stoneCategories = stoneCategories;
        this.stoneTypes = stoneTypes;
        this.currencies = currencies;
        if (margins.length) {
            await this.selectMargin(margins[0].id);
        }
    }

    get selectedMargin() {
        return this.state.margins.find(m => m.id === this.state.selectedMarginId) || null;
    }

    get filteredStoneNormal() {
        if (!this.state.stoneCatFilter) return this.state.stonesNormal;
        const catId = parseInt(this.state.stoneCatFilter);
        return this.state.stonesNormal.filter(row => {
            const typeId = this.m2oId(row.stone_type_id);
            const type = this.stoneTypes.find(t => t.id === typeId);
            return type && this.m2oId(type.category_id) === catId;
        });
    }

    m2oId(f) { return Array.isArray(f) ? f[0] : f; }

    async selectMargin(marginId) {
        this._deletedLaborIds = [];
        this._deletedAddonIds = [];
        this._deletedMetalIds = [];
        this._deletedStoneCondIds = [];
        this._deletedStoneNormIds = [];

        this.state.selectedMarginId = marginId;
        this.state.isDirty = false;
        this.state.marginHeaderDirty = false;
        this.state.stoneCatFilter = "";

        const [partRates, labors, addons, metals, stonesConditional, stonesNormal] = await Promise.all([
            this.orm.searchRead("pdp.margin.part", [["margin_id", "=", marginId]], ["id", "margin_id", "rate"], { limit: 1 }),
            this.orm.searchRead("pdp.margin.labor", [["margin_id", "=", marginId]], ["id", "margin_id", "labor_id", "rate"]),
            this.orm.searchRead("pdp.margin.addon", [["margin_id", "=", marginId]], ["id", "margin_id", "addon_id", "rate"]),
            this.orm.searchRead("pdp.margin.metal", [["margin_id", "=", marginId]], ["id", "margin_id", "metal_purity_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone.conditional", [["margin_id", "=", marginId]], ["id", "margin_id", "stone_cat_id", "operator", "comparative_cost", "currency_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", marginId]], ["id", "margin_id", "stone_type_id", "rate"]),
        ]);

        const margin = this.state.margins.find(m => m.id === marginId);
        this.state.marginCode = margin ? margin.code : "";
        this.state.marginName = margin ? margin.name : "";

        this.state.partRate = partRates.length
            ? { ...partRates[0], _key: partRates[0].id, _dirty: false }
            : null;
        this.state.labors = labors.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.addons = addons.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.metals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.stonesConditional = stonesConditional.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.stonesNormal = stonesNormal.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    onHeaderFieldChange(field, value) {
        this.state[field] = value;
        this.state.marginHeaderDirty = true;
        this.state.isDirty = true;
    }

    onFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    onPartRateChange(value) {
        const rate = parseFloat(value) || 0;
        if (this.state.partRate) {
            this.state.partRate.rate = rate;
            this.state.partRate._dirty = true;
        } else {
            this.state.partRate = {
                id: null,
                _key: -Date.now(),
                _dirty: true,
                margin_id: [this.state.selectedMarginId, ""],
                rate,
            };
        }
        this.state.isDirty = true;
    }

    addLabor() {
        this.state.labors.push({ id: null, _key: -Date.now(), _dirty: true, margin_id: [this.state.selectedMarginId, ""], labor_id: false, rate: 1.0 });
        this.state.isDirty = true;
    }
    removeLabor(row) {
        if (row.id) this._deletedLaborIds.push(row.id);
        this.state.labors.splice(this.state.labors.indexOf(row), 1);
        this.state.isDirty = true;
    }

    addAddon() {
        this.state.addons.push({ id: null, _key: -Date.now(), _dirty: true, margin_id: [this.state.selectedMarginId, ""], addon_id: false, rate: 1.0 });
        this.state.isDirty = true;
    }
    removeAddon(row) {
        if (row.id) this._deletedAddonIds.push(row.id);
        this.state.addons.splice(this.state.addons.indexOf(row), 1);
        this.state.isDirty = true;
    }

    addMetal() {
        this.state.metals.push({ id: null, _key: -Date.now(), _dirty: true, margin_id: [this.state.selectedMarginId, ""], metal_purity_id: false, rate: 1.0 });
        this.state.isDirty = true;
    }
    removeMetal(row) {
        if (row.id) this._deletedMetalIds.push(row.id);
        this.state.metals.splice(this.state.metals.indexOf(row), 1);
        this.state.isDirty = true;
    }

    addStoneCond() {
        const defCurrency = this.currencies.length ? [this.currencies[0].id, this.currencies[0].name] : false;
        this.state.stonesConditional.push({ id: null, _key: -Date.now(), _dirty: true, margin_id: [this.state.selectedMarginId, ""], stone_cat_id: false, operator: "<", comparative_cost: 0, currency_id: defCurrency, rate: 1.0 });
        this.state.isDirty = true;
    }
    removeStoneCond(row) {
        if (row.id) this._deletedStoneCondIds.push(row.id);
        this.state.stonesConditional.splice(this.state.stonesConditional.indexOf(row), 1);
        this.state.isDirty = true;
    }

    addStoneNorm() {
        this.state.stonesNormal.push({ id: null, _key: -Date.now(), _dirty: true, margin_id: [this.state.selectedMarginId, ""], stone_type_id: false, rate: 1.0 });
        this.state.isDirty = true;
    }
    removeStoneNorm(row) {
        if (row.id) this._deletedStoneNormIds.push(row.id);
        this.state.stonesNormal.splice(this.state.stonesNormal.indexOf(row), 1);
        this.state.isDirty = true;
    }

    async _saveRows(model, rows, deletedIds, valsFunc, marginId) {
        if (deletedIds.length) {
            await this.orm.unlink(model, [...deletedIds]);
            deletedIds.length = 0;
        }
        for (const row of rows) {
            if (!row._dirty) continue;
            const vals = valsFunc(row, marginId);
            if (row.id) {
                await this.orm.write(model, [row.id], vals);
            } else {
                const [newId] = await this.orm.create(model, [vals]);
                row.id = newId;
                row._key = newId;
            }
            row._dirty = false;
        }
    }

    async saveMargin() {
        const marginId = this.state.selectedMarginId;
        if (!marginId) return;
        try {
            if (this.state.marginHeaderDirty) {
                await this.orm.write("pdp.margin", [marginId], { code: this.state.marginCode, name: this.state.marginName });
                this.state.marginHeaderDirty = false;
                const m = this.state.margins.find(m => m.id === marginId);
                if (m) { m.code = this.state.marginCode; m.name = this.state.marginName; }
            }
            await this._saveRows("pdp.margin.labor", this.state.labors, this._deletedLaborIds,
                (r) => ({ margin_id: marginId, labor_id: this.m2oId(r.labor_id), rate: parseFloat(r.rate) || 0 }));
            await this._saveRows("pdp.margin.addon", this.state.addons, this._deletedAddonIds,
                (r) => ({ margin_id: marginId, addon_id: this.m2oId(r.addon_id), rate: parseFloat(r.rate) || 0 }));
            await this._saveRows("pdp.margin.metal", this.state.metals, this._deletedMetalIds,
                (r) => ({ margin_id: marginId, metal_purity_id: this.m2oId(r.metal_purity_id), rate: parseFloat(r.rate) || 0 }));
            await this._saveRows("pdp.margin.stone.conditional", this.state.stonesConditional, this._deletedStoneCondIds,
                (r) => ({ margin_id: marginId, stone_cat_id: this.m2oId(r.stone_cat_id), operator: r.operator, comparative_cost: parseFloat(r.comparative_cost) || 0, currency_id: this.m2oId(r.currency_id), rate: parseFloat(r.rate) || 0 }));
            await this._saveRows("pdp.margin.stone", this.state.stonesNormal, this._deletedStoneNormIds,
                (r) => ({ margin_id: marginId, stone_type_id: this.m2oId(r.stone_type_id), rate: parseFloat(r.rate) || 0 }));
            if (this.state.partRate && this.state.partRate._dirty) {
                if (this.state.partRate.id) {
                    await this.orm.write("pdp.margin.part", [this.state.partRate.id], { rate: parseFloat(this.state.partRate.rate) || 0 });
                } else {
                    const [newId] = await this.orm.create("pdp.margin.part", [{ margin_id: marginId, rate: parseFloat(this.state.partRate.rate) || 0 }]);
                    this.state.partRate.id = newId;
                    this.state.partRate._key = newId;
                }
                this.state.partRate._dirty = false;
            }
            this.state.isDirty = false;
            this.notification.add("Saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || e), { type: "danger" });
        }
    }

    async createMargin() {
        if (!this.state.newMarginCode || !this.state.newMarginName) {
            this.notification.add("Code and Name are required.", { type: "warning" });
            return;
        }
        try {
            const [newId] = await this.orm.create("pdp.margin", [{ code: this.state.newMarginCode, name: this.state.newMarginName }]);
            const margins = await this.orm.searchRead("pdp.margin", [], ["id", "code", "name"], { order: "code asc" });
            this.state.margins = margins;
            this.state.showNewMarginForm = false;
            this.state.newMarginCode = "";
            this.state.newMarginName = "";
            await this.selectMargin(newId);
        } catch (e) {
            this.notification.add("Error: " + (e.message || e), { type: "danger" });
        }
    }

    async deleteMargin() {
        const m = this.selectedMargin;
        if (!m) return;
        if (!window.confirm(`Delete margin "${m.code} - ${m.name}"?`)) return;
        try {
            await this.orm.unlink("pdp.margin", [m.id]);
            const margins = await this.orm.searchRead("pdp.margin", [], ["id", "code", "name"], { order: "code asc" });
            this.state.margins = margins;
            this.state.selectedMarginId = null;
            this.state.labors = [];
            this.state.addons = [];
            this.state.metals = [];
            this.state.stonesConditional = [];
            this.state.stonesNormal = [];
            this.state.partRate = null;
            this.state.isDirty = false;
            if (margins.length) await this.selectMargin(margins[0].id);
        } catch (e) {
            this.notification.add("Error: " + (e.message || e), { type: "danger" });
        }
    }
}

MarginsManage.template = "pdp_frontend.margins_manage";
registry.category("actions").add("pdp_frontend.margins_manage", MarginsManage);
