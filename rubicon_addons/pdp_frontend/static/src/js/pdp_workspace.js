/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";
import { UomSelector } from "@rubicon_uom/js/rubicon_uom_selector";

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
            marginLabors: [],
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
                this.orm.searchRead("pdp.product.model", [], ["id", "code", "drawing", "quotation", "category_id"], { order: "code ASC" }),
                this.orm.searchRead("pdp.margin", [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.labor.type", [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.metal", [], ["id", "code", "name", "purity_system"]),
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

            // Load default labor currency from settings (singleton created at install)
            const laborSettings = await this.orm.searchRead(
                'pdp.labor.settings', [], ['default_labor_currency_id'], { limit: 1 }
            );
            if (laborSettings.length && laborSettings[0].default_labor_currency_id) {
                const cur = laborSettings[0].default_labor_currency_id;
                this._defaultLaborCurrencyId = Array.isArray(cur) ? cur[0] : cur;
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

        } catch (e) {
            console.error("Initial load failed:", e);
        }
    }

    // ==========================================
    // Computed
    // ==========================================

    get filteredModels() {
        return this.state.models;
    }

    get filteredProducts() {
        if (!this.state.productFilter) return this.state.products;
        const q = this.state.productFilter.toLowerCase();
        return this.state.products.filter(p => p.code.toLowerCase().includes(q));
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

    // Returns only purities compatible with the current product's metal purity system
    get filteredPurities() {
        const product = this.activeProduct;
        if (!product?.metal) return this.purities;
        const mw = this.state.metalWeights.find(m => m.metal_version === product.metal);
        if (!mw) return this.purities;
        const metalId = Array.isArray(mw.metal_id) ? mw.metal_id[0] : mw.metal_id;
        const metal = this.allMetals.find(m => m.id === metalId);
        if (!metal?.purity_system) return this.purities;
        return this.purities.filter(p => p.purity_system === metal.purity_system);
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
                    `Pierre "${s.code}" : prix unitaire non renseigné. Le coût ne sera pas calculé.`,
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
            this.notification.add(`Pierre "${trimmed}" introuvable.`, { type: 'warning' });
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    async onStoneAttrChange(key, field, newId) {
        const row = this.state.stoneRows.find(r => r._key === key);
        if (!row || !row._stoneDetail) return;
        const d = row._stoneDetail;
        const m2o = (f) => (Array.isArray(f) ? f[0] : f) || false;
        const typeId  = m2o(d.type_id);
        const shadeId = field === 'shade_id' ? (parseInt(newId) || false) : m2o(d.shade_id);
        const shapeId = field === 'shape_id' ? (parseInt(newId) || false) : m2o(d.shape_id);
        const sizeId  = field === 'size_id'  ? (parseInt(newId) || false) : m2o(d.size_id);

        const domain = [
            ['type_id',  '=', typeId],
            ['shade_id', '=', shadeId || false],
            ['shape_id', '=', shapeId || false],
            ['size_id',  '=', sizeId  || false],
        ];
        try {
            const found = await this.orm.searchRead(
                "pdp.stone", domain,
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
                        `Pierre "${s.code}" : prix unitaire non renseigné. Le coût ne sera pas calculé.`,
                        { type: 'warning' }
                    );
                }
            } else {
                this.notification.add(`Aucune pierre trouvée pour cette combinaison.`, { type: 'warning' });
            }
        } catch (e) {
            this.notification.add(`Erreur lors de la recherche de pierre.`, { type: 'danger' });
        }
        row._dirty = true;
        this.state.isDirty = true;
    }

    getStoneType(stone_type_id_val) {
        const id = Array.isArray(stone_type_id_val) ? stone_type_id_val[0] : stone_type_id_val;
        if (!id) return null;
        return this.stoneTypes.find(t => t.id === id) || null;
    }

    _resetDeletedLists() {
        this._deletedStoneIds = [];
        this._deletedMetalIds = [];
        this._deletedLaborModelIds = [];
        this._deletedLaborProductIds = [];
        this._deletedAddonCostIds = [];
        this._deletedPartIds = [];
        this._currentCompId = null;
    }

    // ==========================================
    // Event Handlers
    // ==========================================

    onProductSearchInput(ev) {
        const q = ev.target.value;
        this.state.productSearch = q;
        if (!q) {
            this.state.productSearchResults = [];
            this.state.productFilter = '';
            return;
        }
        const ql = q.toLowerCase();
        this.state.productSearchResults = this.state.products.filter(
            p => p.code.toLowerCase().includes(ql)
        );
    }

    onProductSearchKeydown(ev) {
        if (ev.key === 'Enter') {
            this.state.productFilter = this.state.productSearch;
            this.state.productSearchResults = [];
        } else if (ev.key === 'Escape') {
            this.state.productSearch = '';
            this.state.productFilter = '';
            this.state.productSearchResults = [];
        }
    }

    selectProductFromSearch(product) {
        this.state.productSearch = product.code;
        this.state.productFilter = product.code;
        this.state.productSearchResults = [];
        this.selectProduct(product.id);
    }

    openModelList() {
        this.state.showModelList = true;
    }

    closeModelList() {
        this.state.showModelList = false;
    }

    selectModelFromList(modelId) {
        this.state.showModelList = false;
        this.selectModel(modelId);
    }

    async onModelSelectChange(ev) {
        const modelId = parseInt(ev.target.value);
        if (modelId) await this.selectModel(modelId);
    }

    setImageMode(mode) {
        this.state.imageMode = mode;
    }

    onBottomSplitterMouseDown(ev) {
        ev.preventDefault();
        const workspace = ev.target.closest('.pdp-workspace');
        const bottomPane = workspace.querySelector('.pdp-bottom-pane');
        const startY = ev.clientY;
        const startHeight = bottomPane.getBoundingClientRect().height;
        const maxHeight = workspace.getBoundingClientRect().height - 100;
        const onMouseMove = (e) => {
            const newHeight = Math.max(80, Math.min(maxHeight, startHeight + (startY - e.clientY)));
            bottomPane.style.height = newHeight + 'px';
        };
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    openFullScreenImage() {
        this.state.showFullScreenImage = true;
    }

    closeFullScreenImage() {
        this.state.showFullScreenImage = false;
    }

    async onDrawingChange(ev) {
        if (!this.activeModel) return;
        const val = ev.target.value;
        this.activeModel.drawing = val;
        try {
            await this.orm.write("pdp.product.model", [this.activeModel.id], { drawing: val });
        } catch (e) {
            this.notification.add("Error saving Drawing#: " + e.message, { type: "danger" });
        }
    }

    async onQuotationChange(ev) {
        if (!this.activeModel) return;
        const val = ev.target.value;
        this.activeModel.quotation = val;
        try {
            await this.orm.write("pdp.product.model", [this.activeModel.id], { quotation: val });
        } catch (e) {
            this.notification.add("Error saving Quotation#: " + e.message, { type: "danger" });
        }
    }

    async onPurityChange(ev) {
        this.state.selectedPurityId = parseInt(ev.target.value) || null;
        await this.recalculatePrice();
    }

    // ==========================================
    // Model Selection
    // ==========================================

    async selectModel(modelId) {
        this.state.selectedModelId = parseInt(modelId);
        this.state.productSearch = '';
        this.state.productSearchResults = [];
        this.state.productFilter = '';
        this._resetDeletedLists();
        this.state.isDirty = false;
        try {
            this.state.products = await this.orm.searchRead(
                "pdp.product",
                [["model_id", "=", this.state.selectedModelId]],
                ["id", "code", "create_date", "in_collection", "category_id", "metal", "active", "remark"]
            );

            await Promise.all([
                this.fetchModelPicture(),
                this.fetchModelMetals(),
                this.fetchModelLabor(),
                this.fetchMatchingModels(),
            ]);

            await this.fetchWhereUsed();

            if (this.state.products.length > 0) {
                await this.selectProduct(this.state.products[0].id);
            } else {
                this.clearProductState();
            }
        } catch (e) {
            console.error("Failed fetching model data", e);
        }
    }

    // ==========================================
    // Product Selection
    // ==========================================

    async selectProduct(productId) {
        this.state.selectedProductId = parseInt(productId);
        // Set default purity from the model metal entry matching this product's metal version
        const product = this.state.products.find(p => p.id === this.state.selectedProductId);
        if (product?.metal) {
            const mw = this.state.metalWeights.find(m => m.metal_version === product.metal);
            if (mw) {
                const pid = Array.isArray(mw.purity_id) ? mw.purity_id[0] : mw.purity_id;
                if (pid) this.state.selectedPurityId = pid;
            }
        }
        try {
            // fetchModelPicture must finish first: it populates allPictures,
            // which fetchProductPicture reads to decide what to display.
            await this.fetchModelPicture();
            await Promise.all([
                this.fetchProductPicture(productId),
                this.fetchProductStones(),
                this.fetchProductParts(),
                this.fetchProductLabor(),
                this.fetchAddonCosts(),
            ]);
            await this.recalculatePrice();
        } catch (e) {
            console.error("Error fetching product details", e);
        }
    }

    clearProductState() {
        this.state.selectedProductId = null;
        this.state.stoneOriginal = [];
        this.state.stoneRecut = [];
        this.state.stoneRows = [];
        this.state.selectedStoneKey = null;
        this.state.laborProductCosts = [];
        this.state.addonCosts = [];
        this.state.parts = [];
        this.state.priceLines = [];
        this.state.priceTotals = { cost: 0, margin: 0, price: 0 };
        this._currentCompId = null;
        this._deletedStoneIds = [];
    }

    setTab(tabName) {
        this.state.activeTab = tabName;
    }

    async onMarginChange(ev) {
        if (ev.target.value) {
            this.state.selectedMarginId = parseInt(ev.target.value);
            await this.recalculatePrice();
        }
    }

    async onCurrencyChange(ev) {
        if (ev.target.value) {
            this.state.selectedCurrencyId = parseInt(ev.target.value);
            const curr = this.state.currencies.find(c => c.id === this.state.selectedCurrencyId);
            if (curr) {
                this.state.currencySymbol = curr.symbol;
                this.state.usRate = curr.rate || 1.0;
            }
            await this.recalculatePrice();
        }
    }

    // ==========================================
    // Data Fetching
    // ==========================================

    async fetchModelPicture() {
        try {
            const modelId   = this.state.selectedModelId;
            const productId = this.state.selectedProductId ? parseInt(this.state.selectedProductId) : null;

            // Model-scoped photos visible from any product of this model
            const modelDomain = ["&", ["scope", "=", "model"], ["product_ids.model_id", "=", modelId]];

            // Product-scoped photos only for the currently selected product
            const productDomain = productId
                ? ["&", ["scope", "=", "product"], ["product_ids", "in", [productId]]]
                : null;

            const domain = productDomain ? ["|", ...modelDomain, ...productDomain] : modelDomain;

            const pics = await this.orm.searchRead(
                "pdp.picture",
                domain,
                ["id", "filename", "product_ids", "scope"],
            );
            this.state.allPictures = pics;
            if (!pics.some(p => p.id === this.state.pictureId)) {
                const display = pics.find(p => p.scope === "model") || pics[0] || null;
                this.state.pictureId  = display ? display.id : null;
                this.state.pictureUrl = display ? `/web/image/pdp.picture/${display.id}/image_1920` : null;
                this.state.drawingUrl = display ? `/web/image/pdp.picture/${display.id}/drawing_1920` : null;
            }
        } catch (e) {
            this.state.pictureId = null;
            this.state.pictureUrl = null;
            this.state.drawingUrl = null;
            this.state.allPictures = [];
        }
    }

    /** Prioritise a product-scoped picture; fall back to a model-scoped thumbnail. */
    async fetchProductPicture(productId) {
        try {
            const pid = parseInt(productId);
            const inList = p => Array.isArray(p.product_ids) && p.product_ids.includes(pid);

            // 1. Product-specific (scope='product', explicitly linked to this product)
            const productPic = this.state.allPictures.find(p => p.scope === "product" && inList(p));
            if (productPic) {
                this.state.productPictureId = productPic.id;
                this.state.pictureId  = productPic.id;
                this.state.pictureUrl = `/web/image/pdp.picture/${productPic.id}/image_1920`;
                this.state.drawingUrl = `/web/image/pdp.picture/${productPic.id}/drawing_1920`;
                return;
            }

            // 2. Model thumbnail fallback (scope='model', linked to all products of model)
            this.state.productPictureId = null;
            const modelPic = this.state.allPictures.find(p => p.scope === "model" && inList(p));
            if (modelPic) {
                this.state.pictureId  = modelPic.id;
                this.state.pictureUrl = `/web/image/pdp.picture/${modelPic.id}/image_1920`;
                this.state.drawingUrl = `/web/image/pdp.picture/${modelPic.id}/drawing_1920`;
            } else {
                // This product has no picture at all
                this.state.pictureId  = null;
                this.state.pictureUrl = null;
                this.state.drawingUrl = null;
            }
        } catch (e) {
            this.state.productPictureId = null;
        }
    }

    /** Make a picture the active display (called from the picture manager). */
    setActivePicture(picId) {
        this.state.pictureId  = picId;
        this.state.pictureUrl = `/web/image/pdp.picture/${picId}/image_1920`;
        this.state.drawingUrl = `/web/image/pdp.picture/${picId}/drawing_1920`;
        const pid = this.state.selectedProductId ? parseInt(this.state.selectedProductId) : null;
        const pic = this.state.allPictures.find(p => p.id === picId);
        this.state.productPictureId =
            (pid && pic?.scope === "product" && pic?.product_ids?.includes(pid)) ? picId : null;
    }

    /**
     * @param {string} field  - 'image_1920' or 'drawing_1920'
     * @param {string} scope  - 'model' | 'product'
     */
    triggerImageUpload(field, scope) {
        const input = document.getElementById(`pdp-upload-${field}-${scope}`);
        if (input) input.click();
    }

    async onImageFileSelected(ev, field, scope) {
        const file = ev.target.files[0];
        if (!file) return;
        ev.target.value = "";   // reset so the same file can be re-selected later
        try {
            const base64 = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload  = (e) => resolve(e.target.result.split(",")[1]);
                reader.onerror = (e) => reject(new Error("FileReader error: " + e.target.error));
                reader.readAsDataURL(file);
            });

            const filenameField = field === "image_1920" ? "filename" : "drawing_filename";
            const productId = this.state.selectedProductId;
            let newId;

            if (scope === "product") {
                const pid = parseInt(productId);
                // Drawing on an existing product picture → add drawing to it
                if (field === "drawing_1920" && this.state.productPictureId) {
                    await this.orm.write("pdp.picture", [this.state.productPictureId], {
                        drawing_1920: base64,
                        drawing_filename: file.name,
                    });
                    newId = this.state.productPictureId;
                } else {
                    [newId] = await this.orm.create("pdp.picture", [{
                        scope: "product",
                        product_ids: [[4, pid]],
                        [field]: base64,
                        [filenameField]: file.name,
                    }]);
                    this.state.productPictureId = newId;
                }
            } else {
                // scope='model' — thumbnail shared across all products of this model
                const modelProducts = await this.orm.searchRead(
                    "pdp.product",
                    [["model_id", "=", this.state.selectedModelId]],
                    ["id"]
                );
                if (!modelProducts.length) {
                    this.notification.add(
                        "Add a product to this model before uploading a photo.",
                        { type: "warning" }
                    );
                    return;
                }
                const existingModelPic = this.state.allPictures.find(p => p.scope === "model");
                if (field === "drawing_1920" && existingModelPic) {
                    await this.orm.write("pdp.picture", [existingModelPic.id], {
                        drawing_1920: base64,
                        drawing_filename: file.name,
                    });
                    newId = existingModelPic.id;
                } else {
                    [newId] = await this.orm.create("pdp.picture", [{
                        scope: "model",
                        product_ids: modelProducts.map(p => [4, p.id]),
                        [field]: base64,
                        [filenameField]: file.name,
                    }]);
                }
            }

            this.state.pictureId = newId;
            if (field === "image_1920") {
                this.state.pictureUrl = `/web/image/pdp.picture/${newId}/image_1920`;
            } else {
                this.state.drawingUrl = `/web/image/pdp.picture/${newId}/drawing_1920`;
            }
            await this.fetchModelPicture();
        } catch (err) {
            this.notification.add(
                err?.data?.message || err?.message || "Failed to upload image",
                { type: "danger" }
            );
        }
    }

    async deletePictureField(field) {
        if (!this.state.pictureId) return;
        const productId = this.state.selectedProductId;
        const picId     = this.state.pictureId;
        const pid       = productId ? parseInt(productId) : null;
        const pic       = this.state.allPictures.find(p => p.id === picId);
        const isProductPic = !!(pid && pic?.scope === "product" && pic?.product_ids?.includes(pid));

        if (isProductPic && pid) {
            // Remove the M2M link for this product; auto-delete if no links remain
            await this.orm.write("pdp.picture", [picId], { product_ids: [[3, pid]] });
            const remaining = await this.orm.read("pdp.picture", [picId], ["product_ids"]);
            if (!remaining[0].product_ids.length) {
                await this.orm.unlink("pdp.picture", [picId]);
            }
            this.state.productPictureId = null;
        } else {
            // Model-level picture — delete the field (or the whole record if no other field)
            const isDrawing  = field === "drawing_1920";
            const otherField = isDrawing ? "image_1920" : "drawing_1920";
            const rec = await this.orm.read("pdp.picture", [picId], [otherField]);
            if (rec[0][otherField]) {
                await this.orm.write("pdp.picture", [picId], {
                    [field]: false,
                    [isDrawing ? "drawing_filename" : "filename"]: false,
                });
            } else {
                await this.orm.unlink("pdp.picture", [picId]);
            }
        }
        // Clear display immediately for instant feedback
        this.state.pictureId = null;
        this.state.pictureUrl = null;
        this.state.drawingUrl = null;
        await this.fetchModelPicture();
        if (productId) await this.fetchProductPicture(parseInt(productId));
    }

    async deletePictureById(picId) {
        const pic = this.state.allPictures.find(p => p.id === picId);
        const pid = this.state.selectedProductId ? parseInt(this.state.selectedProductId) : null;

        if (pic?.scope === "product" && pid) {
            // Unlink from this product only; delete the record if no links remain
            await this.orm.write("pdp.picture", [picId], { product_ids: [[3, pid]] });
            const remaining = await this.orm.read("pdp.picture", [picId], ["product_ids"]);
            if (!remaining[0]?.product_ids?.length) {
                await this.orm.unlink("pdp.picture", [picId]);
            }
        } else {
            await this.orm.unlink("pdp.picture", [picId]);
        }

        if (this.state.pictureId === picId) {
            this.state.pictureId = null;
            this.state.pictureUrl = null;
            this.state.drawingUrl = null;
            this.state.productPictureId = null;
        }
        await this.fetchModelPicture();
        const productId = this.state.selectedProductId;
        if (productId) await this.fetchProductPicture(parseInt(productId));
        if (this.state.allPictures.length === 0) this.state.showPictureManager = false;
    }

    async fetchModelMetals() {
        try {
            const rows = await this.orm.searchRead(
                "pdp.product.model.metal",
                [["model_id", "=", this.state.selectedModelId]],
                ["id", "metal_id", "purity_id", "weight", "metal_version"]
            );
            this.state.metalWeights = rows.map(r => ({ ...r, _key: r.id, _dirty: false }));
        } catch (e) {
            this.state.metalWeights = [];
        }
    }

    async fetchModelLabor() {
        try {
            const rows = await this.orm.searchRead(
                "pdp.labor.cost.model",
                [["model_id", "=", this.state.selectedModelId]],
                ["id", "labor_id", "metal", "cost", "currency_id"]
            );
            this.state.laborModelCosts = rows.map(r => ({ ...r, _key: r.id, _dirty: false }));
        } catch (e) {
            this.state.laborModelCosts = [];
        }
    }

    async fetchMatchingModels() {
        try {
            const matches = await this.orm.searchRead(
                "pdp.product.model.matching",
                ["|", ["model_one_id", "=", this.state.selectedModelId], ["model_two_id", "=", this.state.selectedModelId]],
                ["id", "model_one_id", "model_two_id"]
            );

            const matchedIds = matches.map(m =>
                m.model_one_id[0] === this.state.selectedModelId
                    ? m.model_two_id[0]
                    : m.model_one_id[0]
            );

            if (matchedIds.length > 0) {
                this.state.matchingModels = await this.orm.searchRead(
                    "pdp.product.model",
                    [["id", "in", matchedIds]],
                    ["id", "code", "picture_id"]
                );
            } else {
                this.state.matchingModels = [];
            }
        } catch (e) {
            this.state.matchingModels = [];
        }
    }

    async fetchWhereUsed() {
        try {
            if (!this.state.metalWeights.length) { this.state.whereUsedModels = []; return; }
            const metalIds = [...new Set(
                this.state.metalWeights.map(m => this.m2oId(m.metal_id)).filter(Boolean)
            )];
            if (!metalIds.length) { this.state.whereUsedModels = []; return; }
            const usages = await this.orm.searchRead(
                "pdp.product.model.metal",
                [["metal_id", "in", metalIds], ["model_id", "!=", this.state.selectedModelId]],
                ["model_id"]
            );
            const seen = new Set();
            this.state.whereUsedModels = usages.reduce((acc, u) => {
                const mid = u.model_id[0];
                if (!seen.has(mid)) { seen.add(mid); acc.push({ id: mid, code: u.model_id[1] }); }
                return acc;
            }, []);
        } catch (e) {
            this.state.whereUsedModels = [];
        }
    }

    async fetchProductStones() {
        try {
            const productData = await this.orm.read("pdp.product", [this.state.selectedProductId], ["stone_composition_id"]);
            const compId = productData[0]?.stone_composition_id?.[0] || null;
            this._currentCompId = compId;
            if (compId) {
                const stones = await this.orm.searchRead(
                    "pdp.product.stone", [["composition_id", "=", compId]],
                    ["id", "line_num", "stone_id", "pieces", "weight", "setting", "setting_type_id",
                     "reshaped_shape_id", "reshaped_size_id", "reshaped_weight"]
                );
                // Batch-fetch stone details (type/shade/shape/size/cost/currency) in one query
                const stoneIds = stones.filter(s => s.stone_id).map(s => Array.isArray(s.stone_id) ? s.stone_id[0] : s.stone_id);
                let detailMap = {};
                if (stoneIds.length) {
                    const details = await this.orm.read("pdp.stone", stoneIds, ["id", "code", "type_id", "shape_id", "shade_id", "size_id", "weight", "cost", "currency_id"]);
                    // note: cost/currency_id already included above
                    detailMap = Object.fromEntries(details.map(d => [d.id, d]));
                }
                this.state.stoneRows = stones.map(s => {
                    const sid = Array.isArray(s.stone_id) ? s.stone_id[0] : s.stone_id;
                    const detail = sid ? (detailMap[sid] || null) : null;
                    return {
                        ...s, _key: s.id, _dirty: false,
                        _stoneCode: detail ? detail.code : (Array.isArray(s.stone_id) ? s.stone_id[1] : ''),
                        _stoneValid: !!sid,
                        _stoneDetail: detail,
                        _stoneTypeName: detail ? this._getStoneTypeName(detail) : '',
                    };
                });
                this.state.stoneOriginal = stones.map(s => {
                    const sid = Array.isArray(s.stone_id) ? s.stone_id[0] : s.stone_id;
                    const d = sid ? (detailMap[sid] || null) : null;
                    return {
                        type:   d?.type_id  ? d.type_id[1]  : '',
                        shade:  d?.shade_id ? d.shade_id[1] : '',
                        shape:  d?.shape_id ? d.shape_id[1] : '',
                        pieces: s.pieces,
                        weight: s.weight || d?.weight || 0,
                    };
                });
                this.state.stoneRecut = stones.map(s => {
                    const sid = Array.isArray(s.stone_id) ? s.stone_id[0] : s.stone_id;
                    const d = sid ? (detailMap[sid] || null) : null;
                    return {
                        type:   d?.type_id  ? d.type_id[1]  : '',
                        shade:  d?.shade_id ? d.shade_id[1] : '',
                        shape:  s.reshaped_shape_id ? s.reshaped_shape_id[1] : (d?.shape_id ? d.shape_id[1] : ''),
                        pieces: s.pieces,
                        weight: s.reshaped_weight || s.weight || d?.weight || 0,
                    };
                });
            } else {
                this.state.stoneRows = [];
                this.state.stoneOriginal = [];
                this.state.stoneRecut = [];
            }
        } catch (e) {
            this.state.stoneRows = [];
            this.state.stoneOriginal = [];
            this.state.stoneRecut = [];
        }
    }

    async fetchProductParts() {
        try {
            const rows = await this.orm.searchRead(
                "pdp.product.part", [["product_id", "=", this.state.selectedProductId]],
                ["id", "part_id", "quantity"]
            );
            this.state.parts = rows.map(r => ({ ...r, _key: r.id, _dirty: false }));
        } catch (e) {
            this.state.parts = [];
        }
    }

    async fetchProductLabor() {
        try {
            const rows = await this.orm.searchRead(
                "pdp.labor.cost.product", [["product_id", "=", this.state.selectedProductId]],
                ["id", "labor_id", "cost", "currency_id"]
            );
            this.state.laborProductCosts = rows.map(r => ({ ...r, _key: r.id, _dirty: false }));
        } catch (e) {
            this.state.laborProductCosts = [];
        }
    }

    async fetchAddonCosts() {
        try {
            const rows = await this.orm.searchRead(
                "pdp.addon.cost", [["product_id", "=", this.state.selectedProductId]],
                ["id", "addon_id", "cost", "currency_id"]
            );
            this.state.addonCosts = rows.map(r => ({ ...r, _key: r.id, _dirty: false }));
        } catch (e) {
            this.state.addonCosts = [];
        }
    }

    // ==========================================
    // Metal CRUD (model level)
    // ==========================================

    addMetal() {
        this.state.metalWeights.push({
            id: null, _key: -Date.now(), _dirty: true,
            metal_id: this.allMetals.length > 0 ? [this.allMetals[0].id, this.allMetals[0].code] : false,
            purity_id: this.purities.length > 0 ? [this.purities[0].id, this.purities[0].code] : false,
            weight: 0, metal_version: 'W',
        });
        this.state.isDirty = true;
    }

    removeMetal(key) {
        const idx = this.state.metalWeights.findIndex(r => r._key === key);
        if (idx === -1) return;
        const row = this.state.metalWeights[idx];
        if (row.id) this._deletedMetalIds.push(row.id);
        this.state.metalWeights.splice(idx, 1);
        this.state.isDirty = true;
    }

    setMetalField(key, field, value) {
        const row = this.state.metalWeights.find(r => r._key === key);
        if (!row) return;
        if (field === 'weight') row[field] = parseFloat(value) || 0;
        else if (field === 'metal_id' || field === 'purity_id') row[field] = parseInt(value) || false;
        else row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ==========================================
    // Labor Model CRUD
    // ==========================================

    addLaborModel() {
        this.state.laborModelCosts.push({
            id: null, _key: -Date.now(), _dirty: true,
            labor_id: this.laborTypes.length > 0 ? [this.laborTypes[0].id, this.laborTypes[0].code] : false,
            metal: 'W', cost: 0,
            currency_id: this.defaultLaborCurrencyId ? [this.defaultLaborCurrencyId, ''] : false,
        });
        this.state.isDirty = true;
    }

    removeLaborModel(key) {
        const idx = this.state.laborModelCosts.findIndex(r => r._key === key);
        if (idx === -1) return;
        const row = this.state.laborModelCosts[idx];
        if (row.id) this._deletedLaborModelIds.push(row.id);
        this.state.laborModelCosts.splice(idx, 1);
        this.state.isDirty = true;
    }

    setLaborModelField(key, field, value) {
        const row = this.state.laborModelCosts.find(r => r._key === key);
        if (!row) return;
        if (field === 'cost') row[field] = parseFloat(value) || 0;
        else if (field === 'labor_id' || field === 'currency_id') row[field] = parseInt(value) || false;
        else row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ==========================================
    // Labor Product CRUD
    // ==========================================

    addLaborProduct() {
        this.state.laborProductCosts.push({
            id: null, _key: -Date.now(), _dirty: true,
            labor_id: this.laborTypes.length > 0 ? [this.laborTypes[0].id, this.laborTypes[0].code] : false,
            cost: 0,
            currency_id: this.defaultLaborCurrencyId ? [this.defaultLaborCurrencyId, ''] : false,
        });
        this.state.isDirty = true;
    }

    removeLaborProduct(key) {
        const idx = this.state.laborProductCosts.findIndex(r => r._key === key);
        if (idx === -1) return;
        const row = this.state.laborProductCosts[idx];
        if (row.id) this._deletedLaborProductIds.push(row.id);
        this.state.laborProductCosts.splice(idx, 1);
        this.state.isDirty = true;
    }

    setLaborProductField(key, field, value) {
        const row = this.state.laborProductCosts.find(r => r._key === key);
        if (!row) return;
        if (field === 'cost') row[field] = parseFloat(value) || 0;
        else if (field === 'labor_id' || field === 'currency_id') row[field] = parseInt(value) || false;
        else row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ==========================================
    // Addon Cost CRUD (Misc)
    // ==========================================

    addAddonCost() {
        this.state.addonCosts.push({
            id: null, _key: -Date.now(), _dirty: true,
            addon_id: this.addonTypes.length > 0 ? [this.addonTypes[0].id, this.addonTypes[0].code] : false,
            cost: 0,
            currency_id: this.defaultLaborCurrencyId ? [this.defaultLaborCurrencyId, ''] : false,
        });
        this.state.isDirty = true;
    }

    removeAddonCost(key) {
        const idx = this.state.addonCosts.findIndex(r => r._key === key);
        if (idx === -1) return;
        const row = this.state.addonCosts[idx];
        if (row.id) this._deletedAddonCostIds.push(row.id);
        this.state.addonCosts.splice(idx, 1);
        this.state.isDirty = true;
    }

    setAddonCostField(key, field, value) {
        const row = this.state.addonCosts.find(r => r._key === key);
        if (!row) return;
        if (field === 'cost') row[field] = parseFloat(value) || 0;
        else if (field === 'addon_id' || field === 'currency_id') row[field] = parseInt(value) || false;
        else row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ==========================================
    // Parts CRUD (product level)
    // ==========================================

    addPart() {
        this.state.parts.push({
            id: null, _key: -Date.now(), _dirty: true,
            part_id: this.allParts.length > 0 ? [this.allParts[0].id, this.allParts[0].code] : false,
            quantity: 1,
        });
        this.state.isDirty = true;
    }

    removePart(key) {
        const idx = this.state.parts.findIndex(r => r._key === key);
        if (idx === -1) return;
        const row = this.state.parts[idx];
        if (row.id) this._deletedPartIds.push(row.id);
        this.state.parts.splice(idx, 1);
        this.state.isDirty = true;
    }

    setPartField(key, field, value) {
        const row = this.state.parts.find(r => r._key === key);
        if (!row) return;
        if (field === 'quantity') row[field] = parseFloat(value) || 0;
        else if (field === 'part_id') row[field] = parseInt(value) || false;
        else row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    // ==========================================
    // Stones CRUD
    // ==========================================

    addStone() {
        const key = -Date.now();
        this.state.stoneRows.push({
            id: null, _key: key, _dirty: true,
            line_num: '', stone_id: false, _stoneCode: '', _stoneValid: false, _stoneDetail: null, _stoneTypeName: '',
            pieces: 1, weight: '0', setting: 0, setting_type_id: false,
            reshaped_shape_id: false, reshaped_size_id: false, reshaped_weight: '',
        });
        this.state.selectedStoneKey = key;
        this.state.isDirty = true;
    }

    selectStoneRow(key) {
        this.state.selectedStoneKey = this.state.selectedStoneKey === key ? null : key;
    }

    goToManage(actionTag) {
        this.action.doAction({ type: 'ir.actions.client', tag: actionTag });
    }

    removeStone(key) {
        const idx = this.state.stoneRows.findIndex(r => r._key === key);
        if (idx === -1) return;
        const row = this.state.stoneRows[idx];
        if (row.id) this._deletedStoneIds.push(row.id);
        this.state.stoneRows.splice(idx, 1);
        this.state.isDirty = true;
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
            ["stone_id", "pieces", "weight", "reshaped_shape_id", "reshaped_size_id", "reshaped_weight"]
        );
        if (!stones.length) return;

        const newCompId = (await this.orm.create("pdp.product.stone.composition", [{ code: newCode }]))[0];
        for (const s of stones) {
            await this.orm.create("pdp.product.stone", [{
                composition_id: newCompId,
                stone_id: s.stone_id ? s.stone_id[0] : false,
                pieces: s.pieces || 0,
                weight: s.weight || 0,
                reshaped_shape_id: s.reshaped_shape_id ? s.reshaped_shape_id[0] : false,
                reshaped_size_id: s.reshaped_size_id ? s.reshaped_size_id[0] : false,
                reshaped_weight: s.reshaped_weight || 0,
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

                // Copy Labors
                const lRules = await this.orm.searchRead("pdp.margin.labor", [["margin_id", "=", srcId]], ["labor_id", "rate"]);
                if (lRules.length) {
                    await this.orm.create("pdp.margin.labor", lRules.map(r => ({ margin_id: newId, labor_id: r.labor_id[0], rate: r.rate })));
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
                const snRules = await this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", srcId]], ["stone_type_id", "rate"]);
                if (snRules.length) {
                    await this.orm.create("pdp.margin.stone", snRules.map(r => ({ margin_id: newId, stone_type_id: r.stone_type_id[0], rate: r.rate })));
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
        const [parts, labors, addons, metals, stoneCond, stoneNorm] = await Promise.all([
            this.orm.searchRead("pdp.margin.part", [["margin_id", "=", marginId]], ["id", "rate"]),
            this.orm.searchRead("pdp.margin.labor", [["margin_id", "=", marginId]], ["id", "labor_id", "rate"]),
            this.orm.searchRead("pdp.margin.addon", [["margin_id", "=", marginId]], ["id", "addon_id", "rate"]),
            this.orm.searchRead("pdp.margin.metal", [["margin_id", "=", marginId]], ["id", "metal_purity_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone.conditional", [["margin_id", "=", marginId]], ["id", "stone_cat_id", "operator", "comparative_cost", "currency_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", marginId]], ["id", "stone_type_id", "rate"]),
        ]);
        this.state.marginPartRecord = parts.length ? { ...parts[0], _dirty: false } : { id: null, rate: 1.0, _dirty: false };
        this.state.marginLabors = labors.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginAddons = addons.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginMetals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginStonesConditional = stoneCond.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginStonesNormal = stoneNorm.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this._mDelLaborIds = []; this._mDelAddonIds = [];
        this._mDelMetalIds = []; this._mDelStoneCondIds = []; this._mDelStoneNormIds = [];
    }

    // --- Misc tab ---
    setMarginPartRate(value) {
        if (!this.state.marginPartRecord) this.state.marginPartRecord = { id: null, rate: 1.0, _dirty: false };
        this.state.marginPartRecord.rate = parseFloat(value) || 1.0;
        this.state.marginPartRecord._dirty = true;
    }
    addMarginLabor() {
        this.state.marginLabors.push({ id: null, _key: -Date.now(), _dirty: true, labor_id: false, rate: 1.0 });
    }
    removeMarginLabor(key) {
        const idx = this.state.marginLabors.findIndex(r => r._key === key);
        if (idx === -1) return;
        const r = this.state.marginLabors[idx];
        if (r.id) this._mDelLaborIds.push(r.id);
        this.state.marginLabors.splice(idx, 1);
    }
    setMarginLaborField(key, field, value) {
        const r = this.state.marginLabors.find(r => r._key === key);
        if (!r) return;
        r[field] = field === 'rate' ? parseFloat(value) || 1.0 : (parseInt(value) || false);
        r._dirty = true;
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
        this.state.marginStonesNormal.push({ id: null, _key: -Date.now(), _dirty: true, stone_type_id: false, rate: 1.0 });
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
            if (this._mDelLaborIds.length) { await this.orm.unlink("pdp.margin.labor", this._mDelLaborIds); this._mDelLaborIds = []; }
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
            // Labor
            for (const r of this.state.marginLabors) {
                if (!r._dirty) continue;
                const v = { labor_id: this.m2oId(r.labor_id), rate: r.rate };
                if (r.id) await this.orm.write("pdp.margin.labor", [r.id], v);
                else { const [nid] = await this.orm.create("pdp.margin.labor", [{ ...v, margin_id: mid }]); r.id = nid; r._key = nid; }
                r._dirty = false;
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
                const v = { stone_type_id: this.m2oId(r.stone_type_id), rate: r.rate };
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
        try {
            // 1. Unlink deleted records
            if (this._deletedMetalIds.length) {
                await this.orm.unlink("pdp.product.model.metal", this._deletedMetalIds);
                this._deletedMetalIds = [];
            }
            if (this._deletedLaborModelIds.length) {
                await this.orm.unlink("pdp.labor.cost.model", this._deletedLaborModelIds);
                this._deletedLaborModelIds = [];
            }
            if (this._deletedLaborProductIds.length) {
                await this.orm.unlink("pdp.labor.cost.product", this._deletedLaborProductIds);
                this._deletedLaborProductIds = [];
            }
            if (this._deletedAddonCostIds.length) {
                await this.orm.unlink("pdp.addon.cost", this._deletedAddonCostIds);
                this._deletedAddonCostIds = [];
            }
            if (this._deletedPartIds.length) {
                await this.orm.unlink("pdp.product.part", this._deletedPartIds);
                this._deletedPartIds = [];
            }
            if (this._deletedStoneIds.length) {
                await this.orm.unlink("pdp.product.stone", this._deletedStoneIds);
                this._deletedStoneIds = [];
            }

            // 2. Save stones (product level)
            if (this.state.selectedProductId) {
                const dirtyStones = this.state.stoneRows.filter(r => r._dirty);
                if (dirtyStones.length) {
                    // Create composition if product doesn't have one yet
                    if (!this._currentCompId) {
                        const product = this.activeProduct;
                        const compCode = product ? product.code : ('COMP-' + this.state.selectedProductId);
                        this._currentCompId = (await this.orm.create("pdp.product.stone.composition", [{ code: compCode }]))[0];
                        await this.orm.write("pdp.product", [this.state.selectedProductId], { stone_composition_id: this._currentCompId });
                    }
                    for (const row of dirtyStones) {
                        if (!row._stoneValid || !row.stone_id) {
                            this.notification.add(`Pierre "${row._stoneCode || '?'}" invalide — ignorée.`, { type: 'warning' });
                            continue;
                        }
                        const vals = {
                            line_num: row.line_num || '',
                            stone_id: this.m2oId(row.stone_id),
                            pieces: row.pieces || 1,
                            weight: parseFloat(row.weight) || 0,
                            setting: parseFloat(row.setting) || 0,
                            setting_type_id: this.m2oId(row.setting_type_id) || false,
                            reshaped_shape_id: this.m2oId(row.reshaped_shape_id) || false,
                            reshaped_size_id: this.m2oId(row.reshaped_size_id) || false,
                            reshaped_weight: row.reshaped_weight || '',
                        };
                        if (row.id) {
                            await this.orm.write("pdp.product.stone", [row.id], vals);
                        } else {
                            const nid = (await this.orm.create("pdp.product.stone", [{ ...vals, composition_id: this._currentCompId }]))[0];
                            row.id = nid; row._key = nid;
                        }
                        row._dirty = false;
                    }
                }
            }

            // 3. Save metal weights
            for (const row of this.state.metalWeights) {
                if (!row._dirty) continue;
                const vals = {
                    metal_id: this.m2oId(row.metal_id),
                    purity_id: this.m2oId(row.purity_id),
                    weight: row.weight || 0,
                    metal_version: row.metal_version || 'W',
                };
                if (row.id) {
                    await this.orm.write("pdp.product.model.metal", [row.id], vals);
                } else {
                    const nid = (await this.orm.create("pdp.product.model.metal", [{ ...vals, model_id: this.state.selectedModelId }]))[0];
                    row.id = nid; row._key = nid;
                }
                row._dirty = false;
            }

            // 3. Save labor model costs
            for (const row of this.state.laborModelCosts) {
                if (!row._dirty) continue;
                const vals = {
                    labor_id: this.m2oId(row.labor_id),
                    metal: row.metal || 'W',
                    cost: row.cost || 0,
                    currency_id: this.m2oId(row.currency_id),
                };
                if (row.id) {
                    await this.orm.write("pdp.labor.cost.model", [row.id], vals);
                } else {
                    const nid = (await this.orm.create("pdp.labor.cost.model", [{ ...vals, model_id: this.state.selectedModelId }]))[0];
                    row.id = nid; row._key = nid;
                }
                row._dirty = false;
            }

            // Product-level saves
            if (this.state.selectedProductId) {
                for (const row of this.state.laborProductCosts) {
                    if (!row._dirty) continue;
                    const vals = {
                        labor_id: this.m2oId(row.labor_id),
                        cost: row.cost || 0,
                        currency_id: this.m2oId(row.currency_id),
                    };
                    if (row.id) {
                        await this.orm.write("pdp.labor.cost.product", [row.id], vals);
                    } else {
                        const nid = (await this.orm.create("pdp.labor.cost.product", [{ ...vals, product_id: this.state.selectedProductId }]))[0];
                        row.id = nid; row._key = nid;
                    }
                    row._dirty = false;
                }

                for (const row of this.state.addonCosts) {
                    if (!row._dirty) continue;
                    const vals = {
                        addon_id: this.m2oId(row.addon_id),
                        cost: row.cost || 0,
                        currency_id: this.m2oId(row.currency_id),
                    };
                    if (row.id) {
                        await this.orm.write("pdp.addon.cost", [row.id], vals);
                    } else {
                        const nid = (await this.orm.create("pdp.addon.cost", [{ ...vals, product_id: this.state.selectedProductId }]))[0];
                        row.id = nid; row._key = nid;
                    }
                    row._dirty = false;
                }

                for (const row of this.state.parts) {
                    if (!row._dirty) continue;
                    const vals = {
                        part_id: this.m2oId(row.part_id),
                        quantity: row.quantity || 0,
                    };
                    if (row.id) {
                        await this.orm.write("pdp.product.part", [row.id], vals);
                    } else {
                        const nid = (await this.orm.create("pdp.product.part", [{ ...vals, product_id: this.state.selectedProductId }]))[0];
                        row.id = nid; row._key = nid;
                    }
                    row._dirty = false;
                }
            }

            this.state.isDirty = false;
            this.notification.add("Saved successfully.", { type: "success" });
            await this.recalculatePrice();
        } catch (e) {
            console.error("Save error:", e);
            this.notification.add("Save error: " + (e.message || e), { type: "danger" });
        }
    }

    // ==========================================
    // Pricing
    // ==========================================

    async recalculatePrice() {
        if (!this.state.selectedProductId || !this.state.selectedCurrencyId) return;
        try {
            const result = await this.orm.call(
                "pdp.price.service", "compute_price_by_ids",
                [this.state.selectedProductId, this.state.selectedMarginId || false, this.state.selectedCurrencyId],
                { purity_id: this.state.selectedPurityId || false }
            );
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
