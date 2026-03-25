/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class StoneManage extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        // Non-reactive lookups loaded once
        this.stoneCategories = [];
        this.stoneTypes = [];
        this.stoneShapes = [];
        this.stoneSizes = [];
        this.stoneShades = [];
        this.currencies = [];

        // Non-reactive deleted-ID trackers
        this._deletedCatIds = [];
        this._deletedTypeIds = [];
        this._deletedShapeIds = [];
        this._deletedShadeIds = [];
        this._deletedSizeIds = [];
        this._deletedStoneIds = [];
        this._deletedWeightIds = [];

        this.state = useState({
            activeTab: "cats_types",

            // Tab 1: Categories & Types
            categories: [],
            selectedCatKey: null,
            types: [],

            // Tab 2: Other Info
            shapes: [],
            shades: [],
            sizes: [],

            // Tab 3: Unit Costs
            costFilterTypeId: "",
            costFilterShapeId: "",
            costFilterShadeId: "",
            stones: [],

            // Tab 4: Unit Weights
            weightFilterTypeId: "",
            weightFilterShapeId: "",
            weightFilterShadeId: "",
            weights: [],

            isDirty: false,
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

    get selectedCategory() {
        return this.state.categories.find(c => c._key === this.state.selectedCatKey) || null;
    }

    get filteredTypes() {
        if (!this.state.selectedCatKey) return this.state.types;
        const cat = this.state.categories.find(c => c._key === this.state.selectedCatKey);
        if (!cat || !cat.id) return this.state.types;
        return this.state.types.filter(t => this.m2oId(t.category_id) === cat.id);
    }

    // ── Tab 1 dirty count ──────────────────────────────────────────

    get dirtyCatsTypesCount() {
        return (
            this.state.categories.filter(r => r._dirty).length +
            this.state.types.filter(r => r._dirty).length +
            this._deletedCatIds.length +
            this._deletedTypeIds.length
        );
    }

    // ── Tab 2 dirty count ──────────────────────────────────────────

    get dirtyOtherInfoCount() {
        return (
            this.state.shapes.filter(r => r._dirty).length +
            this.state.shades.filter(r => r._dirty).length +
            this.state.sizes.filter(r => r._dirty).length +
            this._deletedShapeIds.length +
            this._deletedShadeIds.length +
            this._deletedSizeIds.length
        );
    }

    // ── Tab 3/4 dirty counts ───────────────────────────────────────

    get dirtyStonesCount() {
        return this.state.stones.filter(r => r._dirty).length + this._deletedStoneIds.length;
    }

    get dirtyWeightsCount() {
        return this.state.weights.filter(r => r._dirty).length + this._deletedWeightIds.length;
    }

    // ── Load All ───────────────────────────────────────────────────

    async _loadAll() {
        const [cats, types, shapes, shades, sizes, currencies] = await Promise.all([
            this.orm.searchRead(
                "pdp.stone.category",
                [],
                ["id", "code", "name"],
                { order: "code asc" }
            ),
            this.orm.searchRead(
                "pdp.stone.type",
                [],
                ["id", "code", "name", "density", "category_id"],
                { order: "code asc" }
            ),
            this.orm.searchRead(
                "pdp.stone.shape",
                [],
                ["id", "code", "shape"],
                { order: "code asc" }
            ),
            this.orm.searchRead(
                "pdp.stone.shade",
                [],
                ["id", "code", "shade"],
                { order: "code asc" }
            ),
            this.orm.searchRead(
                "pdp.stone.size",
                [],
                ["id", "name"],
                { order: "name asc" }
            ),
            this.orm.searchRead(
                "res.currency",
                [["active", "=", true]],
                ["id", "name", "symbol"],
                { order: "name asc" }
            ),
        ]);

        this.stoneCategories = cats.map(c => ({ ...c }));
        this.stoneTypes = types.map(t => ({ ...t }));
        this.stoneShapes = shapes.map(s => ({ ...s }));
        this.stoneShades = shades.map(s => ({ ...s }));
        this.stoneSizes = sizes.map(s => ({ ...s }));
        this.currencies = currencies;

        this.state.categories = cats.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.types = types.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.shapes = shapes.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.shades = shades.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.sizes = sizes.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    // ── Tab switch ─────────────────────────────────────────────────

    async setTab(tab) {
        this.state.activeTab = tab;
        if (tab === "costs" && this.state.stones.length === 0) {
            await this.loadStones();
        }
        if (tab === "weights" && this.state.weights.length === 0) {
            await this.loadWeights();
        }
    }

    // ── Stone domain helpers ───────────────────────────────────────

    _stoneDomain() {
        const d = [];
        if (this.state.costFilterTypeId) {
            d.push(["type_id", "=", parseInt(this.state.costFilterTypeId)]);
        }
        if (this.state.costFilterShapeId) {
            d.push(["shape_id", "=", parseInt(this.state.costFilterShapeId)]);
        }
        if (this.state.costFilterShadeId) {
            d.push(["shade_id", "=", parseInt(this.state.costFilterShadeId)]);
        }
        return d;
    }

    _weightDomain() {
        const d = [];
        if (this.state.weightFilterTypeId) {
            d.push(["type_id", "=", parseInt(this.state.weightFilterTypeId)]);
        }
        if (this.state.weightFilterShapeId) {
            d.push(["shape_id", "=", parseInt(this.state.weightFilterShapeId)]);
        }
        if (this.state.weightFilterShadeId) {
            d.push(["shade_id", "=", parseInt(this.state.weightFilterShadeId)]);
        }
        return d;
    }

    // ── Load stones / weights ──────────────────────────────────────

    async loadStones() {
        this._deletedStoneIds = [];
        const records = await this.orm.searchRead(
            "pdp.stone",
            this._stoneDomain(),
            ["id", "code", "type_id", "shape_id", "shade_id", "size_id", "cost", "currency_id"],
            { order: "code asc", limit: 500 }
        );
        this.state.stones = records.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    async loadWeights() {
        this._deletedWeightIds = [];
        const records = await this.orm.searchRead(
            "pdp.stone.weight",
            this._weightDomain(),
            ["id", "type_id", "shape_id", "shade_id", "size_id", "weight"],
            { order: "id asc", limit: 500 }
        );
        this.state.weights = records.map(r => ({ ...r, _key: r.id, _dirty: false }));
    }

    // ── Tab 1: Category methods ────────────────────────────────────

    selectCategory(row) {
        this.state.selectedCatKey = row._key;
    }

    addCategory() {
        this.state.categories.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            name: "",
        });
        this.state.isDirty = true;
    }

    removeCategory(row) {
        if (row.id) {
            this._deletedCatIds.push(row.id);
        }
        const idx = this.state.categories.indexOf(row);
        if (idx !== -1) {
            this.state.categories.splice(idx, 1);
        }
        if (this.state.selectedCatKey === row._key) {
            this.state.selectedCatKey = null;
        }
        this.state.isDirty = true;
    }

    onCatFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab 1: Type methods ────────────────────────────────────────

    addType() {
        const cat = this.selectedCategory;
        this.state.types.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            name: "",
            density: 0,
            category_id: cat && cat.id ? [cat.id, cat.code] : false,
        });
        this.state.isDirty = true;
    }

    removeType(row) {
        if (row.id) {
            this._deletedTypeIds.push(row.id);
        }
        const idx = this.state.types.indexOf(row);
        if (idx !== -1) {
            this.state.types.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onTypeFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab 2: Shape methods ───────────────────────────────────────

    addShape() {
        this.state.shapes.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            shape: "",
        });
        this.state.isDirty = true;
    }

    removeShape(row) {
        if (row.id) {
            this._deletedShapeIds.push(row.id);
        }
        const idx = this.state.shapes.indexOf(row);
        if (idx !== -1) {
            this.state.shapes.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onShapeFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab 2: Shade methods ───────────────────────────────────────

    addShade() {
        this.state.shades.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            shade: "",
        });
        this.state.isDirty = true;
    }

    removeShade(row) {
        if (row.id) {
            this._deletedShadeIds.push(row.id);
        }
        const idx = this.state.shades.indexOf(row);
        if (idx !== -1) {
            this.state.shades.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onShadeFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab 2: Size methods ────────────────────────────────────────

    addSize() {
        this.state.sizes.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            name: "",
        });
        this.state.isDirty = true;
    }

    removeSize(row) {
        if (row.id) {
            this._deletedSizeIds.push(row.id);
        }
        const idx = this.state.sizes.indexOf(row);
        if (idx !== -1) {
            this.state.sizes.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onSizeFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab 3: Stone methods ───────────────────────────────────────

    addStoneRow() {
        const defCurrency = this.currencies.length
            ? [this.currencies[0].id, this.currencies[0].name]
            : false;
        const typeId = this.state.costFilterTypeId
            ? parseInt(this.state.costFilterTypeId)
            : (this.stoneTypes.length ? this.stoneTypes[0].id : null);
        const shapeId = this.state.costFilterShapeId
            ? parseInt(this.state.costFilterShapeId)
            : (this.stoneShapes.length ? this.stoneShapes[0].id : null);
        const shadeId = this.state.costFilterShadeId
            ? parseInt(this.state.costFilterShadeId)
            : (this.stoneShades.length ? this.stoneShades[0].id : null);
        const sizeId = this.stoneSizes.length ? this.stoneSizes[0].id : null;

        const typeObj = this.stoneTypes.find(t => t.id === typeId);
        const shapeObj = this.stoneShapes.find(s => s.id === shapeId);
        const shadeObj = this.stoneShades.find(s => s.id === shadeId);
        const sizeObj = this.stoneSizes.find(s => s.id === sizeId);

        this.state.stones.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            type_id: typeObj ? [typeObj.id, typeObj.code] : false,
            shape_id: shapeObj ? [shapeObj.id, shapeObj.code] : false,
            shade_id: shadeObj ? [shadeObj.id, shadeObj.code] : false,
            size_id: sizeObj ? [sizeObj.id, sizeObj.name] : false,
            cost: 0,
            currency_id: defCurrency,
        });
        this.state.isDirty = true;
    }

    removeStoneRow(row) {
        if (row.id) {
            this._deletedStoneIds.push(row.id);
        }
        const idx = this.state.stones.indexOf(row);
        if (idx !== -1) {
            this.state.stones.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onStoneFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Tab 4: Weight methods ──────────────────────────────────────

    addWeightRow() {
        const typeId = this.state.weightFilterTypeId
            ? parseInt(this.state.weightFilterTypeId)
            : (this.stoneTypes.length ? this.stoneTypes[0].id : null);
        const shapeId = this.state.weightFilterShapeId
            ? parseInt(this.state.weightFilterShapeId)
            : (this.stoneShapes.length ? this.stoneShapes[0].id : null);
        const shadeId = this.state.weightFilterShadeId
            ? parseInt(this.state.weightFilterShadeId)
            : (this.stoneShades.length ? this.stoneShades[0].id : null);
        const sizeId = this.stoneSizes.length ? this.stoneSizes[0].id : null;

        const typeObj = this.stoneTypes.find(t => t.id === typeId);
        const shapeObj = this.stoneShapes.find(s => s.id === shapeId);
        const shadeObj = this.stoneShades.find(s => s.id === shadeId);
        const sizeObj = this.stoneSizes.find(s => s.id === sizeId);

        this.state.weights.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            type_id: typeObj ? [typeObj.id, typeObj.code] : false,
            shape_id: shapeObj ? [shapeObj.id, shapeObj.code] : false,
            shade_id: shadeObj ? [shadeObj.id, shadeObj.code] : false,
            size_id: sizeObj ? [sizeObj.id, sizeObj.name] : false,
            weight: 0,
        });
        this.state.isDirty = true;
    }

    removeWeightRow(row) {
        if (row.id) {
            this._deletedWeightIds.push(row.id);
        }
        const idx = this.state.weights.indexOf(row);
        if (idx !== -1) {
            this.state.weights.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onWeightFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ── Value extractors ───────────────────────────────────────────

    _catVals(r) {
        return { code: r.code, name: r.name };
    }

    _typeVals(r) {
        return {
            code: r.code,
            name: r.name,
            density: parseFloat(r.density) || 0,
            category_id: this.m2oId(r.category_id) || false,
        };
    }

    _shapeVals(r) {
        return { code: r.code, shape: r.shape };
    }

    _shadeVals(r) {
        return { code: r.code, shade: r.shade };
    }

    _sizeVals(r) {
        return { name: r.name };
    }

    _stoneVals(r) {
        return {
            code: r.code,
            type_id: this.m2oId(r.type_id) || false,
            shape_id: this.m2oId(r.shape_id) || false,
            shade_id: this.m2oId(r.shade_id) || false,
            size_id: this.m2oId(r.size_id) || false,
            cost: parseFloat(r.cost) || 0,
            currency_id: this.m2oId(r.currency_id) || false,
        };
    }

    _weightVals(r) {
        return {
            type_id: this.m2oId(r.type_id) || false,
            shape_id: this.m2oId(r.shape_id) || false,
            shade_id: this.m2oId(r.shade_id) || false,
            size_id: this.m2oId(r.size_id) || false,
            weight: parseFloat(r.weight) || 0,
        };
    }

    // ── Generic save helper ────────────────────────────────────────

    async _saveSection(model, rows, deletedIds, valsFunc) {
        if (deletedIds.length) {
            await this.orm.unlink(model, deletedIds);
            deletedIds.length = 0;
        }

        const dirtyExisting = rows.filter(r => r._dirty && r.id);
        await Promise.all(
            dirtyExisting.map(r => this.orm.write(model, [r.id], valsFunc(r)))
        );
        for (const r of dirtyExisting) {
            r._dirty = false;
        }

        const newRows = rows.filter(r => r.id === null);
        for (const r of newRows) {
            const [newId] = await this.orm.create(model, [valsFunc(r)]);
            r.id = newId;
            r._key = newId;
            r._dirty = false;
        }
    }

    // ── Save Tab 1 ─────────────────────────────────────────────────

    async saveCatsTypes() {
        try {
            await this._saveSection(
                "pdp.stone.category",
                this.state.categories,
                this._deletedCatIds,
                r => this._catVals(r)
            );
            // Refresh non-reactive lookup
            this.stoneCategories = this.state.categories
                .filter(r => r.id)
                .map(r => ({ id: r.id, code: r.code, name: r.name }));

            await this._saveSection(
                "pdp.stone.type",
                this.state.types,
                this._deletedTypeIds,
                r => this._typeVals(r)
            );
            this.stoneTypes = this.state.types
                .filter(r => r.id)
                .map(r => ({ id: r.id, code: r.code, name: r.name, density: r.density, category_id: r.category_id }));

            this.state.isDirty = this._anyDirty();
            this.notification.add("Categories and types saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }

    // ── Save Tab 2 ─────────────────────────────────────────────────

    async saveOtherInfo() {
        try {
            await this._saveSection(
                "pdp.stone.shape",
                this.state.shapes,
                this._deletedShapeIds,
                r => this._shapeVals(r)
            );
            this.stoneShapes = this.state.shapes
                .filter(r => r.id)
                .map(r => ({ id: r.id, code: r.code, shape: r.shape }));

            await this._saveSection(
                "pdp.stone.shade",
                this.state.shades,
                this._deletedShadeIds,
                r => this._shadeVals(r)
            );
            this.stoneShades = this.state.shades
                .filter(r => r.id)
                .map(r => ({ id: r.id, code: r.code, shade: r.shade }));

            await this._saveSection(
                "pdp.stone.size",
                this.state.sizes,
                this._deletedSizeIds,
                r => this._sizeVals(r)
            );
            this.stoneSizes = this.state.sizes
                .filter(r => r.id)
                .map(r => ({ id: r.id, name: r.name }));

            this.state.isDirty = this._anyDirty();
            this.notification.add("Shapes, shades and sizes saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }

    // ── Save Tab 3 ─────────────────────────────────────────────────

    async saveStones() {
        try {
            await this._saveSection(
                "pdp.stone",
                this.state.stones,
                this._deletedStoneIds,
                r => this._stoneVals(r)
            );
            this.state.isDirty = this._anyDirty();
            this.notification.add("Stone costs saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }

    // ── Save Tab 4 ─────────────────────────────────────────────────

    async saveWeights() {
        try {
            await this._saveSection(
                "pdp.stone.weight",
                this.state.weights,
                this._deletedWeightIds,
                r => this._weightVals(r)
            );
            this.state.isDirty = this._anyDirty();
            this.notification.add("Stone weights saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }

    // ── Helpers ────────────────────────────────────────────────────

    _anyDirty() {
        return (
            this.state.categories.some(r => r._dirty) ||
            this.state.types.some(r => r._dirty) ||
            this.state.shapes.some(r => r._dirty) ||
            this.state.shades.some(r => r._dirty) ||
            this.state.sizes.some(r => r._dirty) ||
            this.state.stones.some(r => r._dirty) ||
            this.state.weights.some(r => r._dirty) ||
            this._deletedCatIds.length > 0 ||
            this._deletedTypeIds.length > 0 ||
            this._deletedShapeIds.length > 0 ||
            this._deletedShadeIds.length > 0 ||
            this._deletedSizeIds.length > 0 ||
            this._deletedStoneIds.length > 0 ||
            this._deletedWeightIds.length > 0
        );
    }

    // ── Print / Export ─────────────────────────────────────────────

    _downloadCsv(filename, headers, rows) {
        const esc = (v) => {
            const s = String(v ?? "");
            return s.includes(",") || s.includes('"') || s.includes("\n")
                ? `"${s.replace(/"/g, '""')}"` : s;
        };
        const lines = [headers.map(esc).join(",")];
        for (const row of rows) lines.push(row.map(esc).join(","));
        const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    printCosts() {
        const headers = ["Type", "Shape", "Shade", "Size", "Stock Code", "Cost", "Currency"];
        const rows = this.state.stones.map(r => {
            const type = this.stoneTypes.find(t => t.id === this.m2oId(r.type_id));
            const shape = this.stoneShapes.find(s => s.id === this.m2oId(r.shape_id));
            const shade = this.stoneShades.find(s => s.id === this.m2oId(r.shade_id));
            const size = this.stoneSizes.find(s => s.id === this.m2oId(r.size_id));
            const currency = this.currencies.find(c => c.id === this.m2oId(r.currency_id));
            return [
                type ? `[${type.code}] ${type.name}` : "",
                shape ? shape.code : "",
                shade ? shade.code : "",
                size ? size.name : "",
                r.code || "",
                r.cost || 0,
                currency ? currency.name : "",
            ];
        });
        this._downloadCsv("stone_costs.csv", headers, rows);
    }

    printWeights() {
        const headers = ["Type", "Shape", "Shade", "Size", "Weight (ct)"];
        const rows = this.state.weights.map(r => {
            const type = this.stoneTypes.find(t => t.id === this.m2oId(r.type_id));
            const shape = this.stoneShapes.find(s => s.id === this.m2oId(r.shape_id));
            const shade = this.stoneShades.find(s => s.id === this.m2oId(r.shade_id));
            const size = this.stoneSizes.find(s => s.id === this.m2oId(r.size_id));
            return [
                type ? `[${type.code}] ${type.name}` : "",
                shape ? shape.code : "",
                shade ? shade.code : "",
                size ? size.name : "",
                r.weight || 0,
            ];
        });
        this._downloadCsv("stone_weights.csv", headers, rows);
    }
}

StoneManage.template = "pdp_frontend.stone_manage";
registry.category("actions").add("pdp_frontend.stone_manage", StoneManage);
