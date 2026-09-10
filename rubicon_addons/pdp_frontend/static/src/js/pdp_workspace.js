/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";
import { UomSelector } from "@rubicon_uom/js/rubicon_uom_selector";

// Persists across component destroy/recreate within the same page load.
let _workspaceNav = null;

export class PdpWorkspace extends Component {
    static components = { UomSelector };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.uomService = useService("rubicon_uom");

        // Non-reactive deleted-ID tracking (product workspace)
        this._deletedStoneIds = [];
        this._deletedMetalIds = [];
        this._deletedLaborModelIds = [];
        this._deletedLaborProductIds = [];
        this._deletedAddonCostIds = [];
        this._deletedPartIds = [];
        this._currentCompId = null;
        // Non-reactive deleted-ID tracking (margins modal)
        this._mDelLaborIds = [];
        this._mDelAddonIds = [];
        this._mDelMetalIds = [];
        this._mDelStoneCondIds = [];
        this._mDelStoneNormIds = [];

        // Non-reactive lookup tables (loaded once at init, never mutated after)
        this.laborTypes = [];
        this.allMetals = [];
        this.purities = [];
        this.allParts = [];
        this.addonTypes = [];
        this.stoneShapes = [];
        this.stoneSizes = [];
        this.stoneCategories = [];
        this.stoneTypes = [];
        this.settingTypes = [];
        this._defaultLaborCurrencyId = false;
        this._defaultLaborCurrencyName = '';
        this._searchTimeout = null;

        this.state = useState({
            // Collections
            models: [],
            products: [],
            margins: [],
            currencies: [],

            // Margins modal
            showMarginsModal: false,
            marginTab: 'misc',
            marginStoneTab: 'conditional',
            marginPartRecord: null,
            laborMetalRate: 1.0,
            laborStoneRate: 1.0,
            laborRateDirty: false,
            marginAddons: [],
            marginMetals: [],
            marginStonesConditional: [],
            marginStonesNormal: [],
            stoneCatFilter: '',

            // New Margin modal
            showNewMarginModal: false,
            newMarginCode: "",
            newMarginName: "",
            newMarginCopySourceId: null,

            // Topbar
            showModelList: false,
            modelListFilter: { code: '', drawing: '', quotation: '' },
            modelSearch: "",
            modelSearchResults: [],
            notation: { active: "rubicon", systems: [] },
            productSearch: "",
            productSearchResults: [],
            productFilter: "",

            // Selections
            selectedModelId: null,
            selectedProductId: null,
            activeTab: "costing",

            // Pricing Parameters
            selectedMarginId: null,
            selectedCurrencyId: null,
            usRate: 1.0,
            currencySymbol: "$",

            // Image viewer
            imageMode: "model",
            pictureId: null,        // currently displayed picture
            productPictureId: null, // non-null when the displayed picture is product-specific
            pictureUrl: null,
            drawingUrl: null,
            showFullScreenImage: false,
            showPictureManager: false,
            allPictures: [],        // all pictures for the current model (across all its products)

            // Pricing
            priceLines: [],
            priceTotals: { cost: 0, margin: 0, price: 0 },

            // Weight summary
            stoneOriginal: [],
            stoneRecut: [],
            metalWeights: [],

            // Stones tab (editable)
            stoneRows: [],
            selectedStoneKey: null,
            suggestedColors: "",
            suggestedCode: "",

            // New model modal
            showNewModel: false,
            newModel: { code: "", category_id: "", drawing: "", quotation: "" },

            // Stone picker combo (one open at a time, keyed by row)
            stoneCombo: { key: null, query: "", results: [], unpriced: 0,
                          loading: false },

            // Labor tab
            laborModelCosts: [],
            laborProductCosts: [],
            addonCosts: [],

            // Matching tab
            matchingModels: [],

            // Parts (sub-parts per product)
            parts: [],

            // Metals tab extras
            whereUsedModels: [],
            selectedPurityId: null,
            selectedConvMetal: null,

            // New product modal
            showNewModal: false,
            newCode: "",
            copySourceProductId: null,
            copyStone: true,
            copyMetals: true,
            copyLabor: true,
            copyParts: true,
            copyMisc: true,

            // Dirty state
            isDirty: false,

            // UOM version (incremented when user changes display unit)
            uomVersion: 0,
        });

        onWillStart(async () => {
            this.state.notation = await this.orm.call("emasur.code.mixin", "get_notation_ui");
            await this.uomService.load();
            await this.loadInitialData();
        });
    }

    // ==========================================
    // Initialization
    // ==========================================

    async loadInitialData() {
        try {
            const [models, margins, laborTypes, allMetals, purities, allParts, addonTypes, stoneShapes, stoneSizes, stoneShades, stoneCategories, stoneTypes, settingTypes] = await Promise.all([
                this.orm.searchRead("pdp.product.model", [], ["id", "code", "alt_code", "drawing", "quotation", "category_id"], { order: "code ASC" }),
                this.orm.searchRead("pdp.margin", [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.labor.type", [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.metal", [], ["id", "code", "name", "purity_system", "is_reference"]),
                this.orm.searchRead("pdp.metal.purity", [["percent", ">", 0]], ["id", "code", "percent", "purity_system"], { order: "percent desc" }),
                this.orm.searchRead("pdp.part", [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.addon.type", [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.stone.shape", [], ["id", "code", "shape"], { order: "shape ASC" }),
                this.orm.searchRead("pdp.stone.size", [], ["id", "name"], { order: "name ASC" }),
                this.orm.searchRead("pdp.stone.shade", [], ["id", "code", "shade"], { order: "shade ASC" }),
                this.orm.searchRead("pdp.stone.category", [], ["id", "code", "name"], { order: "name ASC" }),
                this.orm.searchRead("pdp.stone.type", [], ["id", "code", "name", "category_id"], { order: "name ASC" }),
                this.orm.searchRead("pdp.stone.setting.type", [], ["id", "name", "cost"], { order: "cost ASC" }),
            ]);
            this.productCategories = await this.orm.searchRead(
                "pdp.product.category", [], ["id", "code", "name"], { order: "code ASC" });

            this.state.models = models;
            this.state.margins = margins;
            this.laborTypes = laborTypes;
            this.allMetals = allMetals;
            this.purities = purities;
            this.allParts = allParts;
            this.addonTypes = addonTypes;
            this.stoneShapes = stoneShapes;
            this.stoneSizes = stoneSizes;
            this.stoneShades = stoneShades;
            this.stoneCategories = stoneCategories;
            this.stoneTypes = stoneTypes;
            this.settingTypes = settingTypes;

            const currSettings = await this.orm.searchRead(
                "pdp.currency.setting", [["active", "=", true]],
                ["id", "currency_id", "rate", "sequence"],
                { order: "sequence ASC, id ASC" }
            );
            if (currSettings.length > 0) {
                this.state.currencies = currSettings.map(cs => ({
                    settingId: cs.id,
                    id: cs.currency_id[0],
                    name: cs.currency_id[1],
                    rate: cs.rate || 1.0,
                    symbol: '',
                }));
                const currIds = [...new Set(this.state.currencies.map(c => c.id))];
                const currRecords = await this.orm.read("res.currency", currIds, ["id", "symbol"]);
                const symbolMap = Object.fromEntries(currRecords.map(r => [r.id, r.symbol]));
                this.state.currencies.forEach(c => c.symbol = symbolMap[c.id] || c.name);
            } else {
                this.state.currencies = await this.orm.searchRead(
                    "res.currency", [["active", "=", true]], ["id", "name", "symbol", "rate"]
                );
            }

            // Load default labor currency from pdp.config (pdp_base)
            const pdpConfigs = await this.orm.searchRead(
                'pdp.config', [], ['labor_currency_id'], { limit: 1 }
            );
            if (pdpConfigs.length && pdpConfigs[0].labor_currency_id) {
                const cur = pdpConfigs[0].labor_currency_id;
                this._defaultLaborCurrencyId = Array.isArray(cur) ? cur[0] : cur;
                this._defaultLaborCurrencyName = Array.isArray(cur) ? cur[1] : String(cur);
            }

            if (this.state.margins.length > 0) this.state.selectedMarginId = this.state.margins[0].id;

            const usd = this.state.currencies.find(c => c.name === "USD");
            if (usd) {
                this.state.selectedCurrencyId = usd.id;
                this.state.currencySymbol = usd.symbol;
                this.state.usRate = usd.rate || 1.0;
            } else if (this.state.currencies.length > 0) {
                this.state.selectedCurrencyId = this.state.currencies[0].id;
                this.state.currencySymbol = this.state.currencies[0].symbol;
                this.state.usRate = this.state.currencies[0].rate || 1.0;
            }

            if (_workspaceNav) {
                const nav = _workspaceNav;
                _workspaceNav = null;
                if (nav.selectedMarginId) this.state.selectedMarginId = nav.selectedMarginId;
                if (nav.selectedCurrencyId) {
                    const cur = this.state.currencies.find(c => c.id === nav.selectedCurrencyId);
                    if (cur) {
                        this.state.selectedCurrencyId = cur.id;
                        this.state.currencySymbol = cur.symbol;
                        this.state.usRate = cur.rate || 1.0;
                    }
                }
                if (nav.activeTab) this.state.activeTab = nav.activeTab;
                if (nav.selectedModelId) {
                    await this.selectModel(nav.selectedModelId);
                    if (nav.selectedProductId && nav.selectedProductId !== this.state.selectedProductId) {
                        await this.selectProduct(nav.selectedProductId);
                    }
                }
            }

        } catch (e) {
            console.error("Initial load failed:", e);
        }
    }

    // ==========================================
    // Computed
    // ==========================================

    // Rendering caps: the catalog holds >13k models; pushing them all into
    // the DOM (options or table rows) is what made the workspace slow.
    MODEL_LIST_RENDER_CAP = 200;

    // ── Dual notation ───────────────────────────────────────────────────
    // Display: the official code of the active system (never the computed
    // suggestion). Search: always matches every code, whatever is displayed.
    codeOf(rec) {
        if (this.state.notation.active !== "rubicon") {
            return rec.alt_code || rec.code;
        }
        return rec.code;
    }

    matchesCode(rec, needle) {
        const ql = (needle || "").toLowerCase();
        if (!ql) return true;
        return ["code", "alt_code", "legacy_code"].some(
            (f) => (rec[f] || "").toLowerCase().includes(ql));
    }

    get notationLabel() {
        const entry = this.state.notation.systems.find(
            ([key]) => key === this.state.notation.active);
        return entry ? entry[1].split(" ")[0] : "Rubicon";
    }

    async toggleNotation() {
        const keys = this.state.notation.systems.map(([key]) => key);
        if (!keys.length) return;
        const next = keys[(keys.indexOf(this.state.notation.active) + 1) % keys.length];
        this.state.notation.active = await this.orm.call(
            "emasur.code.mixin", "set_user_notation", [next]);
        const active = this.activeModel;
        if (active) this.state.modelSearch = this.codeOf(active);
    }

    _matchingModelsFor(filters) {
        const { code, drawing, quotation } = filters;
        return this.state.models.filter(m =>
            (!code      || this.matchesCode(m, code)) &&
            (!drawing   || (m.drawing   || '').toLowerCase().includes(drawing.toLowerCase())) &&
            (!quotation || (m.quotation || '').toLowerCase().includes(quotation.toLowerCase()))
        );
    }

    get modelListMatchCount() {
        return this._matchingModelsFor(this.state.modelListFilter).length;
    }

    get filteredModelList() {
        return this._matchingModelsFor(this.state.modelListFilter)
            .slice(0, this.MODEL_LIST_RENDER_CAP);
    }

    get filteredProducts() {
        if (!this.state.productFilter) return this.state.products;
        const q = this.state.productFilter.toLowerCase();
        return this.state.products.filter(p => this.matchesCode(p, q));
    }

    get activeModel() {
        return this.state.models.find(m => m.id === this.state.selectedModelId) || null;
    }

    get activeProduct() {
        return this.state.products.find(p => p.id === this.state.selectedProductId) || null;
    }

    get filteredMetalWeights() {
        if (!this.state.selectedPurityId) return this.state.metalWeights;
        return this.state.metalWeights.filter(m => {
            const pid = Array.isArray(m.purity_id) ? m.purity_id[0] : m.purity_id;
            return pid === this.state.selectedPurityId;
        });
    }

    // Returns only purities compatible with the conv metal override (if set) or the current product's metal
    get filteredPurities() {
        if (this.state.selectedConvMetal) {
            const convMetal = this.allMetals.find(m => m.code === this.state.selectedConvMetal);
            if (convMetal?.purity_system) return this.purities.filter(p => p.purity_system === convMetal.purity_system);
        }
        const product = this.activeProduct;
        if (!product?.metal) return this.purities;
        const mw = this.state.metalWeights.find(m => m.metal_version === product.metal);
        if (!mw) return this.purities;
        const metalId = Array.isArray(mw.metal_id) ? mw.metal_id[0] : mw.metal_id;
        const metal = this.allMetals.find(m => m.id === metalId);
        if (!metal?.purity_system) return this.purities;
        return this.purities.filter(p => p.purity_system === metal.purity_system);
    }

    get nonRefMetals() {
        return this.allMetals.filter(m => !m.is_reference);
    }

    get defaultCurrencyId() {
        return this.state.selectedCurrencyId || (this.state.currencies.length > 0 ? this.state.currencies[0].id : false);
    }

    get defaultLaborCurrencyId() {
        return this._defaultLaborCurrencyId || this.defaultCurrencyId;
    }

    onUomChange(categoryCode, uomId) {
        this.state.uomVersion = (this.state.uomVersion || 0) + 1;
    }

    get weightDisplay() {
        return {
            metalWeight: (value) => this.uomService.format(value, 'metal_weight', 3),
            stoneWeight: (value) => this.uomService.format(parseFloat(value) || 0, 'stone_weight', 3),
            metalSymbol: () => this.uomService.symbol('metal_weight'),
            stoneSymbol: () => this.uomService.symbol('stone_weight'),
        };
    }

    // ==========================================
    // Helpers
    // ==========================================

    m2oId(val) {
        if (!val) return false;
        if (Array.isArray(val)) return val[0];
        return val;
    }

    _getStoneTypeName(detail) {
        if (!detail || !detail.type_id) return '';
        const typeId = Array.isArray(detail.type_id) ? detail.type_id[0] : detail.type_id;
        return this.stoneTypes.find(t => t.id === typeId)?.name || detail.type_id[1] || '';
    }

    async validateStoneCode(key, code) {
        const row = this.state.stoneRows.find(r => r._key === key);
        if (!row) return;
        const trimmed = (code || '').trim().toUpperCase();
        if (!trimmed) {
            row.stone_id = false;
            row._stoneCode = '';
            row._stoneValid = false;
            row._stoneDetail = null;
            row._dirty = true;
            this.state.isDirty = true;
            this._refreshSuggestedCode();
            return;
        }
        const found = await this.orm.searchRead(
            "pdp.stone", [["code", "=", trimmed]],
            ["id", "code", "type_id", "shape_id", "shade_id", "size_id", "cost", "currency_id"],
            { limit: 1 }
        );
        if (found.length) {
            const s = found[0];
            row.stone_id = [s.id, s.code];
            row._stoneCode = s.code;
            row._stoneValid = true;
            row._stoneDetail = s;
            row._stoneTypeName = this._getStoneTypeName(s);

            if (!s.cost) {
                this.notification.add(
                    `Stone "${s.code}": unit price not set. Cost will not be computed.`,
                    { type: 'warning' }
                );
            }

            // Attempt to auto-fetch the standard stone weight
            try {
                const weights = await this.orm.searchRead(
                    "pdp.stone.weight",
                    [
                        ["type_id",  "=", s.type_id  ? s.type_id[0]  : false],
                        ["shape_id", "=", s.shape_id ? s.shape_id[0] : false],
                        ["shade_id", "=", s.shade_id ? s.shade_id[0] : false],
                        ["size_id",  "=", s.size_id  ? s.size_id[0]  : false],
                    ],
                    ["weight"], { limit: 1 }
                );
                if (weights.length > 0 && weights[0].weight) {
                    row.weight = weights[0].weight.toString().replace('.', ',');
                }
            } catch (weightError) {
                console.warn("Could not fetch stone weight:", weightError);
            }

        } else {
            row.stone_id = false;
            row._stoneCode = trimmed;
            row._stoneValid = false;
            row._stoneDetail = null;
            row._stoneTypeName = '';
            this.notification.add(`Stone "${trimmed}" not found.`, { type: 'warning' });
        }
        row._dirty = true;
        this.state.isDirty = true;
        this._refreshSuggestedCode();
    }

    setCenterStone(key) {
        const target = this.state.stoneRows.find(r => r._key === key);
        if (!target) return;
        const wasCenter = !!target.is_center;
        // Single center per composition: clear any other and mark it dirty so the
        // save payload carries the flip (the backend constraint needs both rows).
        for (const row of this.state.stoneRows) {
            if (row.is_center && row._key !== key) {
                row.is_center = false;
                row._dirty = true;
            }
        }
        // Clicking the current center clears it (no center -> None).
        target.is_center = !wasCenter;
        target._dirty = true;
        this.state.isDirty = true;
        this._refreshSuggestedCode();
    }

    _buildStoneLineData() {
        return this.state.stoneRows
            .filter(r => r._stoneValid && this.m2oId(r._stoneDetail?.type_id))
            .map(r => ({
                type_id: this.m2oId(r._stoneDetail?.type_id),
                weight: parseFloat(r.weight) || 0,
                reshaped_weight: parseFloat(r.reshaped_weight) || 0,
                is_center: !!r.is_center,
            }));
    }

    async _refreshSuggestedCode() {
        if (!this.state.selectedProductId) {
            this.state.suggestedColors = "";
            this.state.suggestedCode = "";
            return;
        }
        try {
            const res = await this.orm.call(
                "pdp.product.stone.composition", "suggest_from_line_data",
                [this._buildStoneLineData(), this.activeModel?.code || "", this.activeProduct?.metal || ""]
            );
            this.state.suggestedColors = res.colors || "";
            this.state.suggestedCode = res.product_code || "";
        } catch (e) {
            // Preview only — never block the workspace on a failed suggestion.
            this.state.suggestedColors = "";
            this.state.suggestedCode = "";
        }
    }

    async applySuggestedCode() {
        const productId = this.state.selectedProductId;
        if (!productId) return;
        if (this.state.isDirty) {
            this.notification.add("Save your changes before applying the suggested code.", { type: "warning" });
            return;
        }
        try {
            await this.orm.call("pdp.product", "apply_suggested_code", [[productId]]);
            this.notification.add("Suggested code applied.", { type: "success" });
            await this._reloadProducts(productId);
        } catch (e) {
            this.notification.add(`Apply failed: ${e.message || e}`, { type: "danger" });
        }
    }

    setStoneField(key, field, value) {
        const row = this.state.stoneRows.find(r => r._key === key);
        if (!row) return;
        if (field === 'pieces') row[field] = parseInt(value) || 0;
        else if (field === 'stone_id' || field === 'reshaped_shape_id' || field === 'reshaped_size_id')
            row[field] = parseInt(value) || false;
        else if (field === 'setting_type_id') {
            const typeId = parseInt(value) || false;
            row.setting_type_id = typeId;
            const stype = typeId ? this.settingTypes.find(t => t.id === typeId) : null;
            row.setting = stype ? stype.cost : 0;
        }
        else row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ==========================================
    // Product List Actions
    // ==========================================

    async toggleActive(productId) {
        const product = this.state.products.find(p => p.id === productId);
        if (!product) return;
        try {
            await this.orm.write("pdp.product", [productId], { active: !product.active });
            product.active = !product.active;
        } catch (e) {
            this.notification.add("Error: " + e.message, { type: "danger" });
        }
    }

    async toggleCollection(productId) {
        const product = this.state.products.find(p => p.id === productId);
        if (!product) return;
        try {
            await this.orm.write("pdp.product", [productId], { in_collection: !product.in_collection });
            product.in_collection = !product.in_collection;
        } catch (e) {
            this.notification.add("Error: " + e.message, { type: "danger" });
        }
    }

    async productNav(dir) {
        if (!this.state.products.length) return;
        const idx = this.state.products.findIndex(p => p.id === this.state.selectedProductId);
        let newIdx = idx < 0 ? 0 : idx;
        if (dir === 'first') newIdx = 0;
        else if (dir === 'prev') newIdx = Math.max(0, idx - 1);
        else if (dir === 'next') newIdx = Math.min(this.state.products.length - 1, idx + 1);
        else if (dir === 'last') newIdx = this.state.products.length - 1;
        if (newIdx !== idx) await this.selectProduct(this.state.products[newIdx].id);
    }

    showNewProductModal() {
        const modelCode = this.activeModel ? this.activeModel.code : '';
        this.state.newCode = modelCode ? modelCode + '-' : '';
        this.state.copySourceProductId = null;
        this.state.copyStone = true;
        this.state.copyMetals = true;
        this.state.copyLabor = true;
        this.state.copyParts = true;
        this.state.copyMisc = true;
        this.state.showNewModal = true;
    }

    closeNewModal() {
        this.state.showNewModal = false;
    }

    onNewCodeInput(ev) {
        this.state.newCode = ev.target.value;
    }

    async confirmMakeBlank() {
        if (!this.state.newCode.trim()) return;
        try {
            const newId = (await this.orm.create("pdp.product", [{
                code: this.state.newCode.trim(),
                model_id: this.state.selectedModelId,
                active: true,
            }]))[0];
            this.state.showNewModal = false;
            await this._reloadProducts(newId);
            this.notification.add("Blank product created.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || e), { type: "danger" });
        }
    }

    async confirmCopy() {
        if (!this.state.newCode.trim()) return;
        if (!this.state.copySourceProductId) {
            this.notification.add("Select a source design to copy from.", { type: "warning" });
            return;
        }
        try {
            const sourceId = this.state.copySourceProductId;
            const newCode = this.state.newCode.trim();

            const options = {
                'copy_stone': this.state.copyStone,
                'copy_labor': this.state.copyLabor,
                'copy_parts': this.state.copyParts,
                'copy_misc': this.state.copyMisc,
            };

            const newId = await this.orm.call(
                "pdp.product",
                "copy_product_from_ui",
                [sourceId, newCode, options]
            );

            this.state.showNewModal = false;
            await this._reloadProducts(newId);
            this.notification.add("Product copied successfully.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || e), { type: "danger" });
        }
    }

    async _copyStones(sourceProductId, newProductId, newCode) {
        const productData = await this.orm.read("pdp.product", [sourceProductId], ["stone_composition_id"]);
        const compId = productData[0] && productData[0].stone_composition_id ? productData[0].stone_composition_id[0] : null;
        if (!compId) return;

        const stones = await this.orm.searchRead(
            "pdp.product.stone", [["composition_id", "=", compId]],
            ["stone_id", "pieces", "weight", "reshaped_weight", "reshaped_shape_id", "reshaped_size_id"]
        );
        if (!stones.length) return;

        const newCompId = (await this.orm.create("pdp.product.stone.composition", [{ code: newCode }]))[0];
        for (const s of stones) {
            await this.orm.create("pdp.product.stone", [{
                composition_id: newCompId,
                stone_id: s.stone_id ? s.stone_id[0] : false,
                pieces: s.pieces || 0,
                weight: s.weight || 0,
                reshaped_weight: s.reshaped_weight || 0,
                reshaped_shape_id: s.reshaped_shape_id ? s.reshaped_shape_id[0] : false,
                reshaped_size_id: s.reshaped_size_id ? s.reshaped_size_id[0] : false,
            }]);
        }
        await this.orm.write("pdp.product", [newProductId], { stone_composition_id: newCompId });
    }

    async _reloadProducts(selectId) {
        this.state.products = await this.orm.searchRead(
            "pdp.product", [["model_id", "=", this.state.selectedModelId]],
            ["id", "code", "create_date", "in_collection", "category_id", "metal", "active"]
        );
        await this.selectProduct(selectId);
    }

    // ==========================================
    // Margins Modal
    // ==========================================

    async openMarginsModal() {
        if (!this.state.selectedMarginId) return;
        await this.loadMarginData(this.state.selectedMarginId);
        this.state.showMarginsModal = true;
    }

    async onMarginModalSelectionChange(ev) {
        const selId = parseInt(ev.target.value) || null;
        if (selId) {
            this.state.selectedMarginId = selId;
            await this.loadMarginData(selId);
        }
    }

    closeMarginsModal() {
        this.state.showMarginsModal = false;
    }

    openNewMarginModal() {
        this.state.newMarginCode = "";
        this.state.newMarginName = "";
        this.state.newMarginCopySourceId = this.state.selectedMarginId || null;
        this.state.showNewMarginModal = true;
    }

    closeNewMarginModal() {
        this.state.showNewMarginModal = false;
    }

    async confirmCreateMargin() {
        try {
            const vals = {
                code: this.state.newMarginCode.trim(),
                name: this.state.newMarginName.trim(),
            };
            const [newId] = await this.orm.create("pdp.margin", [vals]);

            // Copy rules if source is selected
            if (this.state.newMarginCopySourceId) {
                const srcId = this.state.newMarginCopySourceId;

                // Copy Parts
                const pRules = await this.orm.searchRead("pdp.margin.part", [["margin_id", "=", srcId]], ["rate"]);
                if (pRules.length) {
                    await this.orm.create("pdp.margin.part", pRules.map(r => ({ margin_id: newId, rate: r.rate })));
                }

                // Copy Labor rates (fields on pdp.margin directly)
                const srcMarginRec = await this.orm.read("pdp.margin", [srcId], ["labor_metal_rate", "labor_stone_rate"]);
                if (srcMarginRec.length) {
                    await this.orm.write("pdp.margin", [newId], {
                        labor_metal_rate: srcMarginRec[0].labor_metal_rate,
                        labor_stone_rate: srcMarginRec[0].labor_stone_rate,
                    });
                }

                // Copy Addons
                const aRules = await this.orm.searchRead("pdp.margin.addon", [["margin_id", "=", srcId]], ["addon_id", "rate"]);
                if (aRules.length) {
                    await this.orm.create("pdp.margin.addon", aRules.map(r => ({ margin_id: newId, addon_id: r.addon_id[0], rate: r.rate })));
                }

                // Copy Metals
                const mRules = await this.orm.searchRead("pdp.margin.metal", [["margin_id", "=", srcId]], ["metal_purity_id", "rate"]);
                if (mRules.length) {
                    await this.orm.create("pdp.margin.metal", mRules.map(r => ({ margin_id: newId, metal_purity_id: r.metal_purity_id[0], rate: r.rate })));
                }

                // Copy Stone Conditional
                const scRules = await this.orm.searchRead("pdp.margin.stone.conditional", [["margin_id", "=", srcId]], ["stone_cat_id", "operator", "comparative_cost", "currency_id", "rate"]);
                if (scRules.length) {
                    await this.orm.create("pdp.margin.stone.conditional", scRules.map(r => ({
                        margin_id: newId,
                        stone_cat_id: r.stone_cat_id ? r.stone_cat_id[0] : false,
                        operator: r.operator,
                        comparative_cost: r.comparative_cost,
                        currency_id: r.currency_id ? r.currency_id[0] : false,
                        rate: r.rate
                    })));
                }

                // Copy Stone Normal
                const snRules = await this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", srcId]], ["stone_type_id", "stone_shape_id", "stone_size_id", "stone_shade_id", "rate"]);
                if (snRules.length) {
                    await this.orm.create("pdp.margin.stone", snRules.map(r => ({
                        margin_id: newId,
                        stone_type_id:  r.stone_type_id  ? r.stone_type_id[0]  : false,
                        stone_shape_id: r.stone_shape_id ? r.stone_shape_id[0] : false,
                        stone_size_id:  r.stone_size_id  ? r.stone_size_id[0]  : false,
                        stone_shade_id: r.stone_shade_id ? r.stone_shade_id[0] : false,
                        rate: r.rate,
                    })));
                }
            }

            // Refresh margin list
            this.state.margins = await this.orm.searchRead("pdp.margin", [], ["id", "code", "name"]);
            this.state.selectedMarginId = newId;
            await this.loadMarginData(newId);

            this.closeNewMarginModal();
            this.notification.add("Margin created successfully.", { type: "success" });
        } catch (e) {
            this.notification.add("Failed to create Margin: " + (e.message || e), { type: "danger" });
        }
    }

    async loadMarginData(marginId) {
        const [marginRec, parts, addons, metals, stoneCond, stoneNorm] = await Promise.all([
            this.orm.read("pdp.margin", [marginId], ["labor_metal_rate", "labor_stone_rate"]),
            this.orm.searchRead("pdp.margin.part", [["margin_id", "=", marginId]], ["id", "rate"]),
            this.orm.searchRead("pdp.margin.addon", [["margin_id", "=", marginId]], ["id", "addon_id", "rate"]),
            this.orm.searchRead("pdp.margin.metal", [["margin_id", "=", marginId]], ["id", "metal_purity_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone.conditional", [["margin_id", "=", marginId]], ["id", "stone_cat_id", "operator", "comparative_cost", "currency_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", marginId]], ["id", "stone_type_id", "stone_shape_id", "stone_size_id", "stone_shade_id", "rate"]),
        ]);
        const mr = marginRec[0] || {};
        this.state.laborMetalRate = mr.labor_metal_rate || 1.0;
        this.state.laborStoneRate = mr.labor_stone_rate || 1.0;
        this.state.laborRateDirty = false;
        this.state.marginPartRecord = parts.length ? { ...parts[0], _dirty: false } : { id: null, rate: 1.0, _dirty: false };
        this.state.marginAddons = addons.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginMetals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginStonesConditional = stoneCond.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginStonesNormal = stoneNorm.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this._mDelAddonIds = [];
        this._mDelMetalIds = []; this._mDelStoneCondIds = []; this._mDelStoneNormIds = [];
    }

    // --- Misc tab ---
    setMarginPartRate(value) {
        if (!this.state.marginPartRecord) this.state.marginPartRecord = { id: null, rate: 1.0, _dirty: false };
        this.state.marginPartRecord.rate = parseFloat(value) || 1.0;
        this.state.marginPartRecord._dirty = true;
    }
    setLaborMetalRate(value) {
        this.state.laborMetalRate = parseFloat(value) || 1.0;
        this.state.laborRateDirty = true;
    }
    setLaborStoneRate(value) {
        this.state.laborStoneRate = parseFloat(value) || 1.0;
        this.state.laborRateDirty = true;
    }
    addMarginAddon() {
        this.state.marginAddons.push({ id: null, _key: -Date.now(), _dirty: true, addon_id: false, rate: 1.0 });
    }
    removeMarginAddon(key) {
        const idx = this.state.marginAddons.findIndex(r => r._key === key);
        if (idx === -1) return;
        const r = this.state.marginAddons[idx];
        if (r.id) this._mDelAddonIds.push(r.id);
        this.state.marginAddons.splice(idx, 1);
    }
    setMarginAddonField(key, field, value) {
        const r = this.state.marginAddons.find(r => r._key === key);
        if (!r) return;
        r[field] = field === 'rate' ? parseFloat(value) || 1.0 : (parseInt(value) || false);
        r._dirty = true;
    }

    // --- Metal tab ---
    addMarginMetal() {
        this.state.marginMetals.push({ id: null, _key: -Date.now(), _dirty: true, metal_purity_id: false, rate: 1.0 });
    }
    removeMarginMetal(key) {
        const idx = this.state.marginMetals.findIndex(r => r._key === key);
        if (idx === -1) return;
        const r = this.state.marginMetals[idx];
        if (r.id) this._mDelMetalIds.push(r.id);
        this.state.marginMetals.splice(idx, 1);
    }
    setMarginMetalField(key, field, value) {
        const r = this.state.marginMetals.find(r => r._key === key);
        if (!r) return;
        r[field] = field === 'rate' ? parseFloat(value) || 1.0 : (parseInt(value) || false);
        r._dirty = true;
    }

    // --- Stone Conditional tab ---
    addMarginStoneCond() {
        this.state.marginStonesConditional.push({
            id: null, _key: -Date.now(), _dirty: true,
            stone_cat_id: false, operator: '>', comparative_cost: 0,
            currency_id: this.state.currencies[0]?.id || false, rate: 1.0,
        });
    }
    removeMarginStoneCond(key) {
        const idx = this.state.marginStonesConditional.findIndex(r => r._key === key);
        if (idx === -1) return;
        const r = this.state.marginStonesConditional[idx];
        if (r.id) this._mDelStoneCondIds.push(r.id);
        this.state.marginStonesConditional.splice(idx, 1);
    }
    setMarginStoneCondField(key, field, value) {
        const r = this.state.marginStonesConditional.find(r => r._key === key);
        if (!r) return;
        if (field === 'rate' || field === 'comparative_cost') r[field] = parseFloat(value) || 0;
        else if (field === 'stone_cat_id' || field === 'currency_id') r[field] = parseInt(value) || false;
        else r[field] = value;
        r._dirty = true;
    }

    // --- Stone Normal tab ---
    addMarginStoneNorm() {
        this.state.marginStonesNormal.push({
            id: null, _key: -Date.now(), _dirty: true,
            stone_type_id: false, stone_shape_id: false,
            stone_size_id: false, stone_shade_id: false,
            rate: 1.0,
        });
    }
    removeMarginStoneNorm(key) {
        const idx = this.state.marginStonesNormal.findIndex(r => r._key === key);
        if (idx === -1) return;
        const r = this.state.marginStonesNormal[idx];
        if (r.id) this._mDelStoneNormIds.push(r.id);
        this.state.marginStonesNormal.splice(idx, 1);
    }
    setMarginStoneNormField(key, field, value) {
        const r = this.state.marginStonesNormal.find(r => r._key === key);
        if (!r) return;
        r[field] = field === 'rate' ? parseFloat(value) || 1.0 : (parseInt(value) || false);
        r._dirty = true;
    }

    async saveMarginData() {
        const mid = this.state.selectedMarginId;
        if (!mid) return;
        try {
            // Unlink deleted
            if (this._mDelAddonIds.length) { await this.orm.unlink("pdp.margin.addon", this._mDelAddonIds); this._mDelAddonIds = []; }
            if (this._mDelMetalIds.length) { await this.orm.unlink("pdp.margin.metal", this._mDelMetalIds); this._mDelMetalIds = []; }
            if (this._mDelStoneCondIds.length) { await this.orm.unlink("pdp.margin.stone.conditional", this._mDelStoneCondIds); this._mDelStoneCondIds = []; }
            if (this._mDelStoneNormIds.length) { await this.orm.unlink("pdp.margin.stone", this._mDelStoneNormIds); this._mDelStoneNormIds = []; }

            // Parts
            const pr = this.state.marginPartRecord;
            if (pr && pr._dirty) {
                if (pr.id) await this.orm.write("pdp.margin.part", [pr.id], { rate: pr.rate });
                else { const [nid] = await this.orm.create("pdp.margin.part", [{ margin_id: mid, rate: pr.rate }]); pr.id = nid; }
                pr._dirty = false;
            }
            // Labor (fields on pdp.margin directly)
            if (this.state.laborRateDirty) {
                await this.orm.write("pdp.margin", [mid], {
                    labor_metal_rate: this.state.laborMetalRate,
                    labor_stone_rate: this.state.laborStoneRate,
                });
                this.state.laborRateDirty = false;
            }
            // Addon
            for (const r of this.state.marginAddons) {
                if (!r._dirty) continue;
                const v = { addon_id: this.m2oId(r.addon_id), rate: r.rate };
                if (r.id) await this.orm.write("pdp.margin.addon", [r.id], v);
                else { const [nid] = await this.orm.create("pdp.margin.addon", [{ ...v, margin_id: mid }]); r.id = nid; r._key = nid; }
                r._dirty = false;
            }
            // Metal
            for (const r of this.state.marginMetals) {
                if (!r._dirty) continue;
                const v = { metal_purity_id: this.m2oId(r.metal_purity_id), rate: r.rate };
                if (r.id) await this.orm.write("pdp.margin.metal", [r.id], v);
                else { const [nid] = await this.orm.create("pdp.margin.metal", [{ ...v, margin_id: mid }]); r.id = nid; r._key = nid; }
                r._dirty = false;
            }
            // Stone Conditional
            for (const r of this.state.marginStonesConditional) {
                if (!r._dirty) continue;
                const v = { stone_cat_id: this.m2oId(r.stone_cat_id), operator: r.operator, comparative_cost: r.comparative_cost, currency_id: this.m2oId(r.currency_id), rate: r.rate };
                if (r.id) await this.orm.write("pdp.margin.stone.conditional", [r.id], v);
                else { const [nid] = await this.orm.create("pdp.margin.stone.conditional", [{ ...v, margin_id: mid }]); r.id = nid; r._key = nid; }
                r._dirty = false;
            }
            // Stone Normal
            for (const r of this.state.marginStonesNormal) {
                if (!r._dirty) continue;
                const v = {
                    stone_type_id:  this.m2oId(r.stone_type_id)  || false,
                    stone_shape_id: this.m2oId(r.stone_shape_id) || false,
                    stone_size_id:  this.m2oId(r.stone_size_id)  || false,
                    stone_shade_id: this.m2oId(r.stone_shade_id) || false,
                    rate: r.rate,
                };
                if (r.id) await this.orm.write("pdp.margin.stone", [r.id], v);
                else { const [nid] = await this.orm.create("pdp.margin.stone", [{ ...v, margin_id: mid }]); r.id = nid; r._key = nid; }
                r._dirty = false;
            }
            this.notification.add("Margin saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Save error: " + (e.message || e), { type: "danger" });
        }
    }

    async deleteProduct() {
        if (!this.state.selectedProductId) return;
        const product = this.activeProduct;
        if (!confirm(`Delete product "${product ? product.code : ''}"?`)) return;
        try {
            const delId = this.state.selectedProductId;
            const idx = this.state.products.findIndex(p => p.id === delId);
            // Delete child records first (FK constraints)
            const addonIds = await this.orm.search("pdp.addon.cost", [["product_id", "=", delId]]);
            if (addonIds.length) await this.orm.unlink("pdp.addon.cost", addonIds);
            const laborIds = await this.orm.search("pdp.labor.cost.product", [["product_id", "=", delId]]);
            if (laborIds.length) await this.orm.unlink("pdp.labor.cost.product", laborIds);
            const partIds = await this.orm.search("pdp.product.part", [["product_id", "=", delId]]);
            if (partIds.length) await this.orm.unlink("pdp.product.part", partIds);
            await this.orm.unlink("pdp.product", [delId]);
            this.state.products.splice(idx, 1);
            if (this.state.products.length > 0) {
                await this.selectProduct(this.state.products[Math.min(idx, this.state.products.length - 1)].id);
            } else {
                this.clearProductState();
            }
            this.notification.add("Product deleted.", { type: "warning" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || e), { type: "danger" });
        }
    }

    // ==========================================
    // Save All
    // ==========================================

    async saveAll() {
        if (!this.state.selectedModelId) return;

        const m2o = (v) => this.m2oId(v);

        // Build the payload from dirty rows. Value coercion stays here so the
        // backend persists exactly what the UI computed (no semantic change);
        // the whole save then runs as a single RPC = one transaction.
        const stones = [];
        if (this.state.selectedProductId) {
            for (const row of this.state.stoneRows) {
                if (!row._dirty) continue;
                if (!row._stoneValid || !row.stone_id) {
                    this.notification.add(`Stone "${row._stoneCode || '?'}" invalid — skipped.`, { type: 'warning' });
                    continue;
                }
                stones.push({
                    id: row.id, key: row._key,
                    line_num: row.line_num || '',
                    stone_id: m2o(row.stone_id),
                    pieces: row.pieces || 1,
                    weight: parseFloat(row.weight) || 0,
                    reshaped_weight: parseFloat(row.reshaped_weight) || 0,
                    setting: parseFloat(row.setting) || 0,
                    setting_type_id: m2o(row.setting_type_id) || false,
                    reshaped_shape_id: m2o(row.reshaped_shape_id) || false,
                    reshaped_size_id: m2o(row.reshaped_size_id) || false,
                    is_center: !!row.is_center,
                });
            }
        }

        const metals = this.state.metalWeights.filter(r => r._dirty).map(row => ({
            id: row.id, key: row._key,
            metal_id: m2o(row.metal_id),
            purity_id: m2o(row.purity_id),
            weight: row.weight || 0,
            metal_version: row.metal_version || 'W',
        }));

        const laborModel = this.state.laborModelCosts.filter(r => r._dirty).map(row => ({
            id: row.id, key: row._key,
            labor_id: m2o(row.labor_id),
            metal: row.metal || 'W',
            cost: row.cost || 0,
            currency_id: m2o(row.currency_id),
        }));

        let laborProduct = [], addons = [], parts = [];
        if (this.state.selectedProductId) {
            laborProduct = this.state.laborProductCosts.filter(r => r._dirty).map(row => ({
                id: row.id, key: row._key,
                labor_id: m2o(row.labor_id),
                cost: row.cost || 0,
                currency_id: m2o(row.currency_id),
            }));
            addons = this.state.addonCosts.filter(r => r._dirty).map(row => ({
                id: row.id, key: row._key,
                addon_id: m2o(row.addon_id),
                cost: row.cost || 0,
                currency_id: m2o(row.currency_id),
            }));
            parts = this.state.parts.filter(r => r._dirty).map(row => ({
                id: row.id, key: row._key,
                part_id: m2o(row.part_id),
                quantity: row.quantity || 0,
            }));
        }

        const payload = {
            model_id: this.state.selectedModelId,
            product_id: this.state.selectedProductId || false,
            composition_id: this._currentCompId || false,
            deleted: {
                metal: this._deletedMetalIds,
                labor_model: this._deletedLaborModelIds,
                labor_product: this._deletedLaborProductIds,
                addon: this._deletedAddonCostIds,
                part: this._deletedPartIds,
                stone: this._deletedStoneIds,
            },
            stones,
            metals,
            labor_model: laborModel,
            labor_product: laborProduct,
            addons,
            parts,
        };

        try {
            const result = await this.orm.call(
                "pdp.workspace.service", "save_product_workspace", [payload]
            );

            // Adopt the database ids of the rows the backend created.
            if (result.composition_id) this._currentCompId = result.composition_id;
            const newIds = result.new_ids || {};
            const adopt = (rows, map) => {
                if (!map) return;
                for (const row of rows) {
                    const nid = map[String(row._key)];
                    if (nid) { row.id = nid; row._key = nid; }
                }
            };
            adopt(this.state.stoneRows, newIds.stones);
            adopt(this.state.metalWeights, newIds.metals);
            adopt(this.state.laborModelCosts, newIds.labor_model);
            adopt(this.state.laborProductCosts, newIds.labor_product);
            adopt(this.state.addonCosts, newIds.addons);
            adopt(this.state.parts, newIds.parts);

            // Mark every sent row clean (invalid stones stay dirty for a retry).
            for (const r of [...this.state.metalWeights, ...this.state.laborModelCosts,
                             ...this.state.laborProductCosts, ...this.state.addonCosts,
                             ...this.state.parts]) {
                r._dirty = false;
            }
            for (const r of this.state.stoneRows) {
                if (r._stoneValid && r.stone_id) r._dirty = false;
            }

            // Deletions were applied in the same transaction; clear the queues.
            // (Not _resetDeletedLists: that also nulls the composition id.)
            this._deletedStoneIds = [];
            this._deletedMetalIds = [];
            this._deletedLaborModelIds = [];
            this._deletedLaborProductIds = [];
            this._deletedAddonCostIds = [];
            this._deletedPartIds = [];

            this.state.isDirty = false;
            this.notification.add("Saved successfully.", { type: "success" });
            await this.recalculatePrice();
            this._refreshSuggestedCode();
        } catch (e) {
            console.error("Save error:", e);
            this.notification.add("Save error: " + (e.message || e), { type: "danger" });
        }
    }

    // ==========================================
    // Pricing
    // ==========================================

    async recalculatePrice() {
        console.log("[price] recalculatePrice called. productId=", this.state.selectedProductId, "currencyId=", this.state.selectedCurrencyId, "marginId=", this.state.selectedMarginId);
        if (!this.state.selectedProductId || !this.state.selectedCurrencyId) {
            console.warn("[price] early return: productId=", this.state.selectedProductId, "currencyId=", this.state.selectedCurrencyId);
            return;
        }
        try {
            const result = await this.orm.call(
                "pdp.price.service", "compute_price_by_ids",
                [this.state.selectedProductId, this.state.selectedMarginId || false, this.state.selectedCurrencyId],
                { purity_id: this.state.selectedPurityId || false, conv_metal_code: this.state.selectedConvMetal || false }
            );
            console.log("[price] result=", result);
            if (result && !result.error) {
                this.state.priceLines = result.lines || [];
                this.state.priceTotals = result.totals || { cost: 0, margin: 0, price: 0 };
                if (result.currency && result.currency.symbol) {
                    this.state.currencySymbol = result.currency.symbol;
                }
            } else {
                console.warn("Pricing returned error:", result ? result.error : "No result");
            }
        } catch (e) {
            console.error("Price calculation error:", e);
        }
    }
}

PdpWorkspace.template = "pdp_frontend.Workspace";
registry.category("actions").add("pdp_frontend.workspace", PdpWorkspace);
