/** @odoo-module **/

console.log("SIS Workspace JS loading...");

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

// Persists across component destroy/recreate within the same page load.
let _sisWorkspaceNav = null;

export class SisWorkspace extends Component {
    parseInt = parseInt;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        // Non-reactive lookup tables (loaded once, never change)
        this.docTypeFootnotes = {}; // code → footer_note
        this.margins = [];
        this.payTerms = [];
        this.shippers = [];
        this.sisCountries = [];
        this.allStates = [];
        this.receivingModes = [];
        this.tradeFairs = [];
        this.sisPartners = [];
        this.currencies = [];
        this.metals = [];
        this.metalNameById = {};
        this.companyCurrencyId = null;
        this._allModelMetals = [];
        this._deletedItemIds = [];
        this._fromPage = null;
        this.docTypes = [];

        this.state = useState({
            page: "lobby", // lobby | parties | document

            docType: null,
            docTypeTitle: "",

            // ── Parties ────────────────────────────────────────
            parties: [],
            partySearch: "",
            partyIndex: 0,
            partyTab: "general",
            party: null,
            partyDirty: false,
            partyBanks: [],
            partyBank: { id: null, sis_bank_name: "", sis_bank_address: "", acc_holder_name: "", acc_number: "" },
            partyPhones: [],
            deliveryPartner: { id: null, name: "", street: "", street2: "", city: "", state_id: false, zip: "", country_id: false },
            contactPartner:  { id: null, name: "" },

            // ── Documents ──────────────────────────────────────
            documents: [],
            docYear: String(new Date().getFullYear()),
            docIndex: 0,
            docTab: "general",
            docItemsTab: "general",
            doc: null,
            docDirty: false,
            items: [],
            childDocs: [],

            // ── Delete confirm ─────────────────────────────────
            showDeleteConfirm: false,
            deletePartyDocCount: 0,

            // ── Print modal ────────────────────────────────────
            showPrintModal: false,
            printType: 'with_weights',
            printMarkup: 0.0,

            // ── Prices modal (PDP suggestion) ───────────────────
            showPricesModal: false,
            selectedItemId: null,
            pricesModelCode: '',
            pricesProductId: null,
            pricesDesigns: [],
            pricesPurities: [],
            pricesPurity: null,
            pricesConvMetal: '',
            pricesQty: 1,
            pricesChangeByPct: 0,
            pricesRoundOff: false,
            pricesMetal: [],
            pricesStones: [],
            pricesHistory: [],
            pricesMarginId: null,
            pricesCurrencyId: null,
            pricesResult: null,
            pricesLoading: false,

            // ── Items filter ───────────────────────────────────
            docItemsFilter: '',
            showClosedItems: true,

            // ── Customer address (derived, read-only display) ──
            docPartyAddress: '',

            // ── Metal Req. modal ───────────────────────────────
            showMetalReqModal: false,
            metalReq: [],

            // ── Copy modal ─────────────────────────────────────
            showCopyModal: false,
            copyDocTypeFilter: 'SQ',
            copyDocNameFilter: '',
            copyVisibility: 'open',
            copyItemsVisibility: 'all',
            copyDocs: [],
            copyDocId: null,
            copyItems: [],
            copySerialFilter: '',
            copySelectedItemIds: [],
            copyCopyDocName: true,
            copyReCalcCost: true,
        });

        onWillStart(async () => {
            await this._loadLookups();
        });
    }

    // LOOKUP TABLES (non-reactive)

    async _loadLookups() {
        const [margins, payTerms, shippers, sisCountries, allStates, receivingModes, tradeFairs, sisPartners, currencies, companies, metals, docTypes] =
            await Promise.all([
                this.orm.searchRead("pdp.margin", [], ["id", "name"], { order: "name" }),
                this.orm.searchRead("sis.pay.term", [], ["id", "name"], { order: "name" }),
                this.orm.searchRead("sis.shipper", [], ["id", "name"], { order: "name" }),
                this.orm.searchRead("res.country", [], ["id", "name", "code"], { order: "name" }),
                this.orm.searchRead("res.country.state", [], ["id", "name", "code", "country_id"], { order: "name" }),
                this.orm.searchRead("sis.doc.in.mode", [], ["id", "name"], { order: "name" }),
                this.orm.searchRead("sis.trade.fair", [], ["id", "name"], { order: "name" }),
                this.orm.searchRead(
                    "res.partner",
                    [["sis_code", "!=", false]],
                    ["id", "name", "sis_code"],
                    { order: "name", limit: 2000 }
                ),
                this.orm.searchRead("res.currency", [["active", "=", true]], ["id", "name", "symbol"], { order: "name" }),
                this.orm.searchRead("res.company", [], ["currency_id"], { limit: 1 }),
                this.orm.searchRead("pdp.metal", [], ["id", "code", "name"], { order: "code" }),
                this.orm.searchRead("sis.doc.type", [], ["code", "name", "footer_note"]),
            ]);
        this.margins = margins;
        this.payTerms = payTerms;
        this.shippers = shippers;
        this.sisCountries = sisCountries;
        this.allStates = allStates;
        this.receivingModes = receivingModes;
        this.tradeFairs = tradeFairs;
        this.sisPartners = sisPartners;
        this.currencies = currencies;
        this.companyCurrencyId = companies[0]?.currency_id?.[0] || false;
        this.metals = metals;
        this.metalNameById = Object.fromEntries(metals.map(m => [m.id, m.name || m.code]));
        this.docTypeFootnotes = Object.fromEntries(
            docTypes.filter(dt => dt.footer_note).map(dt => [dt.code, dt.footer_note])
        );
        this.docTypes = docTypes.map(dt => ({ code: dt.code, name: dt.name || dt.code }));

        if (_sisWorkspaceNav) {
            const nav = _sisWorkspaceNav;
            _sisWorkspaceNav = null;
            const docTitles = { SQ: "Maintain Sales Quotations.", SO: "Maintain Sales Orders.", SI: "Maintain Sales Invoices." };
            if (nav.page === 'parties') {
                await this._reloadParties();
                if (nav.partyId && this.state.party?.id !== nav.partyId) {
                    await this._loadParty(nav.partyId);
                }
                if (nav.partyTab) this.state.partyTab = nav.partyTab;
                this.state.page = 'parties';
            } else if (nav.page === 'document' && nav.docType) {
                this.state.docType = nav.docType;
                this.state.docTypeTitle = docTitles[nav.docType] || "Maintain Sales Documents.";
                if (nav.docYear) this.state.docYear = nav.docYear;
                await this._reloadDocuments();
                if (nav.docId && this.state.doc?.id !== nav.docId) {
                    await this._loadDocument(nav.docId);
                }
                this.state.page = 'document';
            }
        }
    }

    // LOBBY NAVIGATION

    async goParties() {
        await this._reloadParties();
        this.state.page = "parties";
        this.state.partyTab = "general";
        this._saveNavState();
    }

    async goDocument(docType) {
        const titles = {
            SQ: "Maintain Sales Quotations.",
            SO: "Maintain Sales Orders.",
            SI: "Maintain Sales Invoices.",
        };
        this.state.docType = docType;
        this.state.docTypeTitle = titles[docType] || "Maintain Sales Documents.";
        this.state.docYear = String(new Date().getFullYear());
        await this._reloadDocuments();
        this.state.page = "document";
        this._saveNavState();
    }

    _saveNavState() {
        _sisWorkspaceNav = {
            page: this.state.page,
            docType: this.state.docType,
            docYear: this.state.docYear,
            partyId: this.state.party?.id || null,
            docId: this.state.doc?.id || null,
            partyTab: this.state.partyTab,
        };
    }

    goLobby() {
        if (this._fromPage === 'document') {
            this._fromPage = null;
            this.state.page = 'document';
        } else {
            this._fromPage = null;
            this.state.page = 'lobby';
        }
    }

    async openCustomers() {
        this._fromPage = 'document';
        await this.goParties();
    }

    // PARTIES

    async _reloadParties() {
        this.state.parties = await this.orm.searchRead(
            "res.partner",
            [["sis_code", "!=", false], ["is_company", "=", true]],
            ["id", "name", "sis_code", "category_id"],
            { order: "name" }
        );
        if (this.state.parties.length > 0) {
            await this._loadParty(this.state.parties[0].id);
        } else {
            this.state.party = null;
        }
    }

    get filteredParties() {
        const q = (this.state.partySearch || "").toLowerCase();
        if (!q) return this.state.parties;
        return this.state.parties.filter(
            (p) =>
                (p.name || "").toLowerCase().includes(q)
        );
    }

    get partyStates() {
        const cId = this.state.party && this._m2oId(this.state.party.country_id);
        if (!cId) return this.allStates;
        return this.allStates.filter(s => s.country_id[0] === cId);
    }

    get deliveryStates() {
        const cId = this.state.deliveryPartner && this._m2oId(this.state.deliveryPartner.country_id);
        if (!cId) return this.allStates;
        return this.allStates.filter(s => s.country_id[0] === cId);
    }

    async _loadParty(partyId) {
        const records = await this.orm.read("res.partner", [partyId], [
            "id", "name", "category_id", "active",
            "title", "street", "street2", "city", "state_id", "zip", "country_id",
            "phone", "email", "website", "comment",
            "margin_id", "sis_pay_term_id",
            // New fields:
            "sis_is_customer", "sis_is_vendor",
            "sis_account", "sis_vendor_account", "sis_vendor_pay_term_id",
            "sis_ship_method_id", "sis_ship_fedex_acc", "sis_ship_stamp",
            "bank_ids", "sis_phone_ids", "sis_code"
        ]);
        this.state.party = records[0] ? { ...records[0] } : null;
        this.state.partyDirty = false;

        // Fetch Bank details if any
        const _emptyBank = { id: null, sis_bank_name: "", sis_bank_address: "", acc_holder_name: "", acc_number: "" };
        if (this.state.party && this.state.party.bank_ids && this.state.party.bank_ids.length > 0) {
            this.state.partyBanks = await this.orm.read("res.partner.bank", this.state.party.bank_ids, [
                "bank_id", "acc_holder_name", "acc_number", "sis_bank_name", "sis_bank_address"
            ]);
            this.state.partyBank = { ..._emptyBank, ...this.state.partyBanks[0] };
        } else {
            this.state.partyBanks = [];
            this.state.partyBank = { ..._emptyBank };
        }

        if (this.state.party && this.state.party.sis_phone_ids && this.state.party.sis_phone_ids.length > 0) {
            this.state.partyPhones = await this.orm.read("res.partner.phone", this.state.party.sis_phone_ids, [
                "name", "phone"
            ]);
        } else {
            this.state.partyPhones = [];
        }

        // Load delivery address child (standard Odoo type='delivery')
        const deliveryList = await this.orm.searchRead("res.partner",
            [["parent_id", "=", partyId], ["type", "=", "delivery"]],
            ["id", "name", "street", "street2", "city", "state_id", "zip", "country_id"],
            { limit: 1 }
        );
        this.state.deliveryPartner = deliveryList.length
            ? { ...deliveryList[0] }
            : { id: null, name: "", street: "", street2: "", city: "",
                state_id: false, zip: "", country_id: false };

        // Load contact child (standard Odoo type='contact')
        const contactList = await this.orm.searchRead("res.partner",
            [["parent_id", "=", partyId], ["type", "=", "contact"],
             ["is_company", "=", false]],
            ["id", "name"],
            { limit: 1 }
        );
        this.state.contactPartner = contactList.length
            ? { ...contactList[0] }
            : { id: null, name: "" };

        const idx = this.state.parties.findIndex((p) => p.id === partyId);
        if (idx >= 0) this.state.partyIndex = idx;
        this._saveNavState();
    }

    async onSelectParty(ev) {
        const id = parseInt(ev.target.value);
        if (id) await this._loadParty(id);
    }

    setPartyTab(tab) {
        this.state.partyTab = tab;
        this._saveNavState();
    }

    setPartyField(field, value) {
        this.state.party[field] = value;
        this.state.partyDirty = true;
    }

    // Odoo Html fields return markup — extract plain text for simple textareas.
    stripHtml(html) {
        if (!html) return '';
        return new DOMParser().parseFromString(html, 'text/html').body.textContent.trim();
    }

    setDeliveryField(field, value) {
        this.state.deliveryPartner[field] = value;
        this.state.partyDirty = true;
    }

    setContactField(field, value) {
        this.state.contactPartner[field] = value;
        this.state.partyDirty = true;
    }

    setBankField(field, value) {
        this.state.partyBank[field] = value;
        this.state.partyDirty = true;
    }

    addPartyPhone() {
        this.state.partyPhones.push({ id: "new_" + Date.now(), name: "", phone: "" });
        this.state.partyDirty = true;
    }

    updatePartyPhone(id, field, value) {
        const phone = this.state.partyPhones.find(p => p.id === id);
        if (phone) {
            phone[field] = value;
            this.state.partyDirty = true;
        }
    }

    removePartyPhone(id) {
        this.state.partyPhones = this.state.partyPhones.filter(p => p.id !== id);
        this.state.partyDirty = true;
    }

    async partyNav(dir) {
        const list = this.filteredParties;
        if (!list.length) return;
        let idx = this.state.partyIndex;
        if (dir === "first") idx = 0;
        else if (dir === "prev") idx = Math.max(0, idx - 1);
        else if (dir === "next") idx = Math.min(list.length - 1, idx + 1);
        else if (dir === "last") idx = list.length - 1;
        await this._loadParty(list[idx].id);
    }

    newParty() {
        this.state.party = {
            id: null, name: "", is_company: true, active: true,
            title: "", street: "", street2: "", city: "", state_id: false, zip: "", country_id: false,
            phone: "", email: "", website: "", comment: "",
            margin_id: false, sis_pay_term_id: false,
            sis_is_customer: true,
            sis_is_vendor: false,
            sis_account: "", sis_vendor_account: "", sis_vendor_pay_term_id: false,
            sis_ship_method_id: false, sis_ship_fedex_acc: "", sis_ship_stamp: "",
            bank_ids: [],
            sis_phone_ids: [],
            sis_code: ""
        };
        this.state.deliveryPartner = {
            id: null, name: "", street: "", street2: "",
            city: "", state_id: false, zip: "", country_id: false
        };
        this.state.contactPartner = { id: null, name: "" };
        this.state.partyBanks = [];
        this.state.partyBank = { id: null, sis_bank_name: "", sis_bank_address: "", acc_holder_name: "", acc_number: "" };
        this.state.partyPhones = [];
        this.state.partyDirty = true;
        this.state.partyTab = "general";
    }

    async saveParty() {
        if (!this.state.party) return;
        const p = this.state.party;
        if (!p.name || !p.name.trim()) {
            this.notification.add("Company name is required.", { type: "warning" });
            return;
        }
        const isNew = !p.id;
        try {
        const vals = {
            name: p.name,
            sis_code: p.sis_code || "",
            is_company: true,
            active: p.active !== false,
            title: p.title || "",
            street: p.street || "",
            city: p.city || "",
            state_id: this._m2oId(p.state_id),
            zip: p.zip || "",
            country_id: this._m2oId(p.country_id),
            phone: p.phone || "",
            email: p.email || "",
            website: p.website || "",
            comment: p.comment || "",
            margin_id: this._m2oId(p.margin_id),
            sis_pay_term_id: this._m2oId(p.sis_pay_term_id),
            sis_is_customer: p.sis_is_customer || false,
            sis_is_vendor: p.sis_is_vendor || false,
            sis_account: p.sis_account || "",
            sis_vendor_account: p.sis_vendor_account || "",
            sis_vendor_pay_term_id: this._m2oId(p.sis_vendor_pay_term_id),
            sis_ship_method_id: this._m2oId(p.sis_ship_method_id),
            sis_ship_fedex_acc: p.sis_ship_fedex_acc || "",
            sis_ship_stamp: p.sis_ship_stamp || "",
            // Note: We don't save bank_ids from this simple form currently as they are a One2Many which requires specific command formatting in odoo ORM if creating/updating from here. The user edits them via the backend for now, or we'd need a specific sub-form.
        };

        const phoneCommands = [[5, 0, 0]];
        for (const ph of this.state.partyPhones) {
            if (ph.name || ph.phone) {
                phoneCommands.push([0, 0, { name: ph.name || "", phone: ph.phone || "" }]);
            }
        }
        vals.sis_phone_ids = phoneCommands;

        // Build the party + its delivery/contact/bank children into one payload.
        // The backend sets each child's parent link, so a freshly created party
        // id propagates, and the whole save commits in one transaction.
        const dp = this.state.deliveryPartner;
        const cp = this.state.contactPartner;
        const bk = this.state.partyBank;

        const payload = { party_id: p.id || false, party_vals: vals };

        const deliveryVals = {
            type: "delivery",
            name: dp.name || this.state.party.name || "",
            street: dp.street || "",
            street2: dp.street2 || "",
            city: dp.city || "",
            zip: dp.zip || "",
            state_id: this._m2oId(dp.state_id) || false,
            country_id: this._m2oId(dp.country_id) || false,
        };
        if (dp.id) {
            payload.delivery = { id: dp.id, vals: deliveryVals };
        } else if (dp.city || dp.country_id) {
            payload.delivery = { id: false, vals: deliveryVals };
        }

        if (cp.name) {
            payload.contact = {
                id: cp.id || false,
                vals: { type: "contact", name: cp.name, is_company: false },
            };
        }

        if (bk.sis_bank_name || bk.acc_number) {
            payload.bank = {
                id: bk.id || false,
                vals: {
                    acc_number:       bk.acc_number || "—",
                    acc_holder_name:  bk.acc_holder_name || "",
                    sis_bank_name:    bk.sis_bank_name || "",
                    sis_bank_address: bk.sis_bank_address || "",
                },
            };
        }

        const savedPartyId = await this.orm.call("sis.workspace.service", "save_party", [payload]);
        this.state.party.id = savedPartyId;

        this.state.partyDirty = false;
        this.notification.add(isNew ? "Party created." : "Party saved.", { type: "success" });
        await this._reloadParties();
        await this._loadParty(savedPartyId);
        } catch (e) {
            this.notification.add(`Save failed: ${e.message || e}`, { type: "danger" });
        }
    }

    async openDeleteConfirm() {
        if (!this.state.party?.id) return;
        this.state.deletePartyDocCount = await this.orm.searchCount(
            'sis.document', [['party_id', '=', this.state.party.id]]
        );
        this.state.showDeleteConfirm = true;
    }

    cancelDeleteConfirm() {
        this.state.showDeleteConfirm = false;
    }

    async confirmDeleteParty() {
        this.state.showDeleteConfirm = false;
        const id = this.state.party.id;
        if (!id) return;
        try {
            await this.orm.unlink('res.partner', [id]);
            this.notification.add('Party deleted.', { type: 'success' });
            await this._reloadParties();
        } catch (e) {
            this.notification.add(`Delete failed: ${e.message || e}`, { type: 'danger' });
        }
    }

    // METAL REQ.

    async openMetalReqModal() {
        if (!this.state.doc?.id) return;
        const items = this.state.items.filter(it => it.design && parseFloat(it.qty) > 0);
        if (!items.length) {
            this.notification.add("No items with design codes in this document.", { type: "warning" });
            return;
        }
        const designCodes = [...new Set(items.map(it => it.design))];
        const products = await this.orm.searchRead(
            'pdp.product', [['code', 'in', designCodes]], ['id', 'code', 'model_id'], {}
        );
        const productByCode = Object.fromEntries(products.map(p => [p.code, p]));
        const modelIds = [...new Set(
            products.map(p => Array.isArray(p.model_id) ? p.model_id[0] : p.model_id).filter(Boolean)
        )];
        if (!modelIds.length) {
            this.notification.add("No PDP model data found for items in this document.", { type: "warning" });
            return;
        }
        const metalRecs = await this.orm.searchRead(
            'pdp.product.model.metal', [['model_id', 'in', modelIds]],
            ['model_id', 'metal_id', 'purity_id', 'weight'], {}
        );
        const metalByModel = {};
        for (const m of metalRecs) {
            const modelId = Array.isArray(m.model_id) ? m.model_id[0] : m.model_id;
            const metalCode = Array.isArray(m.metal_id) ? m.metal_id[1] : '';
            const purityCode = Array.isArray(m.purity_id) ? m.purity_id[1] : '';
            const goldType = `${metalCode}-${purityCode}`;
            if (!metalByModel[modelId]) metalByModel[modelId] = [];
            metalByModel[modelId].push({ goldType, weight: m.weight });
        }
        const totals = {};
        for (const item of items) {
            const product = productByCode[item.design];
            if (!product) continue;
            const modelId = Array.isArray(product.model_id) ? product.model_id[0] : product.model_id;
            const qty = parseFloat(item.qty) || 0;
            for (const { goldType, weight } of (metalByModel[modelId] || [])) {
                totals[goldType] = (totals[goldType] || 0) + weight * qty;
            }
        }
        this.state.metalReq = Object.entries(totals)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([goldType, grams]) => ({ goldType, grams }));
        this.state.showMetalReqModal = true;
    }

    closeMetalReqModal() {
        this.state.showMetalReqModal = false;
    }

    // COPY BROWSER

    async openCopyModal() {
        const defaultType = this.state.docType === 'SO' ? 'SQ' : this.state.docType;
        this.state.copyDocTypeFilter = defaultType;
        this.state.copyDocNameFilter = '';
        this.state.copyVisibility = 'all';
        this.state.copyItemsVisibility = 'all';
        this.state.copyDocs = [];
        this.state.copyDocId = null;
        this.state.copyItems = [];
        this.state.copySerialFilter = '';
        this.state.copySelectedItemIds = [];
        this.state.copyCopyDocName = true;
        this.state.copyReCalcCost = true;
        this.state.showCopyModal = true;
        await this._loadCopyDocs();
    }

    closeCopyModal() {
        this.state.showCopyModal = false;
    }

    async _loadCopyDocs() {
        const domain = [['doc_type_code', '=', this.state.copyDocTypeFilter]];
        if (this.state.copyVisibility === 'open') {
            domain.push(['closed', '=', false], ['canceled', '=', false]);
        } else if (this.state.copyVisibility === 'closed') {
            domain.push(['closed', '=', true]);
        } else if (this.state.copyVisibility === 'canceled') {
            domain.push(['canceled', '=', true]);
        }
        if (this.state.copyDocNameFilter) {
            domain.push(['name', 'ilike', this.state.copyDocNameFilter]);
        }
        this.state.copyDocs = await this.orm.searchRead(
            'sis.document', domain,
            ['id', 'name', 'party_id', 'customer_po', 'date_created', 'date_due',
             'total_qty', 'total_amount'],
            { order: 'name', limit: 200 }
        );
        this.state.copyDocId = null;
        this.state.copyItems = [];
        this.state.copySelectedItemIds = [];
    }

    async onCopyDocTypeChange(ev) {
        this.state.copyDocTypeFilter = ev.target.value;
        await this._loadCopyDocs();
    }

    async onCopyDocNameFilterChange(ev) {
        this.state.copyDocNameFilter = ev.target.value;
        await this._loadCopyDocs();
    }

    async onCopyVisibilityChange(visibility) {
        this.state.copyVisibility = visibility;
        await this._loadCopyDocs();
    }

    async onCopyDocSelect(docId) {
        this.state.copyDocId = docId;
        this.state.copySelectedItemIds = [];
        this.state.copyItems = await this.orm.searchRead(
            'sis.document.item', [['document_id', '=', docId]],
            ['id', 'sequence', 'design', 'purity', 'qty', 'qty_shipped', 'qty_balance',
             'unit_price', 'amount', 'description', 'unit_cost',
             'item_group', 'special_instruction', 'size_remarks',
             'diamond_weight', 'stone_weight', 'diverse_weight', 'metal_weight'],
            { order: 'sequence' }
        );
    }

    onCopyItemsVisibilityChange(visibility) {
        this.state.copyItemsVisibility = visibility;
    }

    get copySelectedDocName() {
        if (!this.state.copyDocId) return '';
        return this.state.copyDocs.find(d => d.id === this.state.copyDocId)?.name || '';
    }

    toggleCopyItem(itemId) {
        const idx = this.state.copySelectedItemIds.indexOf(itemId);
        if (idx >= 0) {
            this.state.copySelectedItemIds.splice(idx, 1);
        } else {
            this.state.copySelectedItemIds.push(itemId);
        }
    }

    get filteredCopyItems() {
        let items = this.state.copyItems;
        const f = (this.state.copySerialFilter || '').toLowerCase();
        if (f) items = items.filter(it => (it.design || '').toLowerCase().includes(f));
        const vis = this.state.copyItemsVisibility;
        if (vis === 'open') {
            items = items.filter(it => (parseFloat(it.qty_balance) || 0) > 0 || (parseFloat(it.qty_shipped) || 0) === 0);
        } else if (vis === 'closed') {
            items = items.filter(it => (parseFloat(it.qty_balance) || 0) === 0 && (parseFloat(it.qty_shipped) || 0) > 0);
        }
        return items;
    }

    get copySourceDiffParty() {
        if (!this.state.copyDocId || !this.state.doc) return false;
        const sourceDoc = this.state.copyDocs.find(d => d.id === this.state.copyDocId);
        if (!sourceDoc) return false;
        const sourcePartyId = Array.isArray(sourceDoc.party_id) ? sourceDoc.party_id[0] : sourceDoc.party_id;
        const currentPartyId = this._m2oId(this.state.doc.party_id);
        return sourcePartyId && currentPartyId && sourcePartyId !== currentPartyId;
    }

    async doCopyItems(all) {
        if (!this.state.doc) {
            this.notification.add("Please open or create a document first.", { type: "warning" });
            return;
        }
        const pool = this.filteredCopyItems;
        const itemsToCopy = all
            ? pool
            : pool.filter(it => this.state.copySelectedItemIds.includes(it.id));
        if (!itemsToCopy.length) {
            this.notification.add("No items to copy.", { type: "warning" });
            return;
        }
        const maxSeq = this.state.items.length
            ? Math.max(...this.state.items.map(i => i.sequence || 0))
            : 0;
        let seq = maxSeq + 10;
        const now = Date.now();
        for (const src of itemsToCopy) {
            this.state.items.push({
                id: null, _key: -(now + seq), _dirty: true,
                sequence: seq,
                design: src.design || '',
                purity: src.purity || '',
                description: src.description || '',
                qty: src.qty,
                qty_shipped: 0, qty_balance: 0,
                currency_id: false,
                unit_price: src.unit_price,
                amount: src.amount,
                unit_cost: this.state.copyReCalcCost ? 0 : src.unit_cost,
                cost: 0, profit: 0, profit_pct: 0,
                item_group: src.item_group || '',
                special_instruction: src.special_instruction || '',
                size_remarks: src.size_remarks || '',
                diamond_weight: src.diamond_weight || 0,
                stone_weight: src.stone_weight || 0,
                diverse_weight: src.diverse_weight || 0,
                metal_weight: src.metal_weight || 0,
            });
            seq += 10;
        }
        if (this.state.copyCopyDocName) {
            const sourceDoc = this.state.copyDocs.find(d => d.id === this.state.copyDocId);
            if (sourceDoc) {
                const ref = `[Copied from ${sourceDoc.name}]`;
                this.state.doc.notes = this.state.doc.notes
                    ? this.state.doc.notes + '\n' + ref
                    : ref;
            }
        }
        this.state.docDirty = true;
        this.state.showCopyModal = false;
        this.notification.add(`${itemsToCopy.length} item(s) copied. Save to apply.`, { type: "success" });
    }

    // DOCUMENTS

    async _reloadDocuments() {
        const year = this.state.docYear;
        const domain = [["doc_type_code", "=", this.state.docType]];
        if (year && year.length === 4) {
            domain.push(["date_created", ">=", `${year}-01-01`]);
            domain.push(["date_created", "<=", `${year}-12-31`]);
        }
        this.state.documents = await this.orm.searchRead(
            "sis.document",
            domain,
            ["id", "name", "party_id", "date_created", "closed", "canceled"],
            { order: "name", limit: 2000 }
        );
        this.state.docIndex = 0;
        if (this.state.documents.length > 0) {
            await this._loadDocument(this.state.documents[0].id);
        } else {
            this.state.doc = null;
            this.state.items = [];
            this.state.childDocs = [];
        }
    }

    async _loadDocument(docId) {
        const [docRecords, items] = await Promise.all([
            this.orm.read("sis.document", [docId], [
                "id", "name", "doc_type_code", "legacy_id", "closed", "canceled",
                "margin_id", "margin_name", "date_created", "date_due", "currency_id",
                "party_id", "party_code", "ship_method_id", "pay_term_id",
                "stamp", "notes", "footnotes",
                "customer_po", "rcv_mode_id", "trade_fair_id", "employee",
                "ship_address", "ship_consignee_bank",
                "ship_for_acc_of", "ship_book", "ship_page",
                "total_amount", "freight_insurance", "total_cif",
                "deposit",
                "total_qty", "total_cost", "total_profit", "profit_pct",
                "child_doc_ids",
            ]),
            this.orm.searchRead(
                "sis.document.item",
                [["document_id", "=", docId]],
                [
                    "id", "sequence", "design", "purity",
                    "qty", "qty_shipped", "qty_balance",
                    "currency_id", "unit_price", "amount", "description",
                    "item_group", "special_instruction", "size_remarks",
                    "diamond_weight", "stone_weight", "diverse_weight", "metal_weight",
                    "unit_cost", "cost", "profit", "profit_pct",
                ],
                { order: "sequence" }
            ),
        ]);

        const doc = docRecords[0];
        this.state.doc = doc ? { ...doc } : null;

        // Resolve M2O fields from legacy data when M2O is unset (imported documents)
        if (this.state.doc) {
            // Auto-set currency from company default when not imported
            if (!this.state.doc.currency_id && this.companyCurrencyId) {
                const curr = this.currencies.find(c => c.id === this.companyCurrencyId);
                if (curr) this.state.doc.currency_id = [curr.id, curr.symbol || curr.name];
            }
            if (!this.state.doc.party_id && this.state.doc.name) {
                // party_code stores a legacy numeric ID, not the sis_code.
                // Extract the customer code from the document name (SO-EMA-25001 → "EMA").
                const parts = this.state.doc.name.split('-');
                const codeFromName = parts.length >= 2 ? parts[1] : null;
                if (codeFromName) {
                    const found = this.sisPartners.find(p => p.sis_code === codeFromName);
                    if (found) this.state.doc.party_id = [found.id, found.name];
                }
            }
            if (!this.state.doc.margin_id && this.state.doc.margin_name) {
                const found = this.margins.find(m => m.name === this.state.doc.margin_name);
                if (found) this.state.doc.margin_id = [found.id, found.name];
            }
        }

        this.state.items = items.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this._deletedItemIds = [];
        this.state.docDirty = false;
        this.state.docTab = "general";
        this.state.docItemsTab = "general";

        const childIds = doc?.child_doc_ids || [];
        this.state.childDocs = childIds.length > 0
            ? await this.orm.read("sis.document", childIds, [
                "id", "name", "doc_type_code", "party_id", "date_created", "closed",
            ])
            : [];

        const idx = this.state.documents.findIndex((d) => d.id === docId);
        if (idx >= 0) this.state.docIndex = idx;

        await this._fetchPartyAddress(doc?.party_id);
        this._saveNavState();
    }

    async onCustomerChange(ev) {
        const id = parseInt(ev.target.value) || false;
        this.state.doc.party_id = id;
        this.state.docDirty = true;
        if (id) {
            const [p] = await this.orm.read("res.partner", [id],
                ["sis_pay_term_id"]);
            if (p) {
                if (!this._m2oId(this.state.doc.pay_term_id) && p.sis_pay_term_id)
                    this.state.doc.pay_term_id = p.sis_pay_term_id;
            }
            if (!this.state.doc.id) {
                const partner = this.sisPartners.find(pt => pt.id === id);
                if (partner?.sis_code) {
                    this.state.doc.name = `${this.state.docType}-${partner.sis_code}-`;
                }
            }
        } else if (!this.state.doc.id) {
            this.state.doc.name = `${this.state.docType}-`;
        }
        await this._fetchPartyAddress(id);
    }

    async _fetchPartyAddress(partyId) {
        const id = Array.isArray(partyId) ? partyId[0] : partyId;
        if (!id) { this.state.docPartyAddress = ''; return; }
        const [p] = await this.orm.read("res.partner", [id],
            ["name", "street", "street2", "city", "zip", "country_id", "phone"]);
        if (!p) { this.state.docPartyAddress = ''; return; }
        const lines = [];
        if (p.name) lines.push(p.name);
        if (p.street) lines.push(p.street);
        if (p.street2) lines.push(p.street2);
        const city = [p.city, p.zip].filter(Boolean).join(', ');
        if (city) lines.push(city);
        const country = Array.isArray(p.country_id) ? p.country_id[1] : '';
        const tel = p.phone ? `Tel:${p.phone}` : '';
        const last = [country, tel].filter(Boolean).join('  ');
        if (last) lines.push(last);
        this.state.docPartyAddress = lines.join('\n');
    }

    async onSelectDocument(ev) {
        const id = parseInt(ev.target.value);
        if (id) await this._loadDocument(id);
    }

    async onDocYearChange(ev) {
        this.state.docYear = ev.target.value;
        if (this.state.docYear.length === 4) {
            await this._reloadDocuments();
        }
    }

    setDocTab(tab) {
        this.state.docTab = tab;
    }

    setDocItemsTab(tab) {
        this.state.docItemsTab = tab;
    }

    setDocField(field, value) {
        this.state.doc[field] = value;
        this.state.docDirty = true;
    }

    async docNav(dir) {
        const list = this.state.documents;
        if (!list.length) return;
        let idx = this.state.docIndex;
        if (dir === "first") idx = 0;
        else if (dir === "prev") idx = Math.max(0, idx - 1);
        else if (dir === "next") idx = Math.min(list.length - 1, idx + 1);
        else if (dir === "last") idx = list.length - 1;
        await this._loadDocument(list[idx].id);
    }

    newDocument() {
        const today = new Date();
        const due = new Date(today);
        due.setMonth(due.getMonth() + 1);
        const fmt = (d) => d.toISOString().split("T")[0];
        const defaultMargin = this.margins.find((m) => m.name === "Wholesale");
        this.state.doc = {
            id: null,
            name: this.state.docType + "-",
            doc_type_code: this.state.docType,
            legacy_id: null,
            closed: false, canceled: false,
            margin_id: defaultMargin ? [defaultMargin.id, defaultMargin.name] : false,
            date_created: fmt(today),
            date_due: fmt(due),
            currency_id: this.companyCurrencyId ? [this.companyCurrencyId, ''] : false,
            party_id: false, party_code: "",
            ship_method_id: false, pay_term_id: false,
            stamp: "", notes: "", footnotes: "",
            customer_po: "", rcv_mode_id: false, trade_fair_id: false, employee: "",
            ship_address: "", ship_consignee_bank: false,
            ship_for_acc_of: "", ship_book: "", ship_page: "",
            total_amount: 0, freight_insurance: 0, total_cif: 0,
            deposit: 0,
            total_qty: 0, total_cost: 0, total_profit: 0, profit_pct: 0,
            child_doc_ids: [],
        };
        this.state.items = [];
        this.state.childDocs = [];
        this.state.docDirty = true;
        this.state.docTab = "general";
    }

    async saveDocument() {
        if (!this.state.doc) return;
        const d = this.state.doc;
        if (!this._m2oId(d.party_id)) {
            this.notification.add("Please select a customer before saving.", { type: "warning" });
            return;
        }
        // If saving a new doc whose name still lacks the customer code, auto-fill it
        // so the backend auto-numbering can produce TYPE-CODE-YYnnn.
        if (!d.id) {
            const nameParts = (d.name || '').split('-');
            if (nameParts.length < 3 || !nameParts[1]) {
                const pid = this._m2oId(d.party_id);
                const partner = this.sisPartners.find(p => p.id === pid);
                if (partner?.sis_code) {
                    d.name = `${this.state.docType}-${partner.sis_code}-`;
                }
            }
        }
        const vals = {
            name: d.name,
            doc_type_code: d.doc_type_code || this.state.docType || "",
            closed: d.closed || false,
            canceled: d.canceled || false,
            margin_id: this._m2oId(d.margin_id),
            date_created: d.date_created || false,
            date_due: d.date_due || false,
            party_id: this._m2oId(d.party_id),
            ship_method_id: this._m2oId(d.ship_method_id),
            pay_term_id: this._m2oId(d.pay_term_id),
            stamp: d.stamp || "",
            notes: d.notes || "",
            footnotes: d.footnotes || "",
            customer_po: d.customer_po || "",
            rcv_mode_id: this._m2oId(d.rcv_mode_id),
            trade_fair_id: this._m2oId(d.trade_fair_id),
            employee: d.employee || "",
            ship_address: d.ship_address || "",
            ship_consignee_bank: d.ship_consignee_bank || false,
            ship_for_acc_of: d.ship_for_acc_of || "",
            ship_book: d.ship_book || "",
            ship_page: d.ship_page || "",
            deposit: parseFloat(d.deposit) || 0,
            freight_insurance: parseFloat(d.freight_insurance) || 0,
            currency_id: this._m2oId(d.currency_id) || false,
        };
        const isNewDoc = !d.id;
        const items = this.state.items
            .filter(i => i._dirty)
            .map(i => ({ id: i.id || false, vals: this._itemVals(i, false) }));
        const payload = {
            id: d.id || false,
            doc_vals: vals,
            deleted_items: this._deletedItemIds,
            items,
        };

        try {
            // One RPC = one transaction: document + item writes/creates/deletes
            // all commit together or not at all.
            const res = await this.orm.call("sis.workspace.service", "save_document", [payload]);
            this._deletedItemIds = [];
            this.state.docDirty = false;
            this.notification.add(isNewDoc ? "Document created." : "Document saved.", { type: "success" });
            if (isNewDoc) await this._reloadDocuments();
            await this._loadDocument(res.id);
        } catch (e) {
            this.notification.add(`Save failed: ${e.message || e}`, { type: "danger" });
        }
    }

    async refreshDocument() {
        if (this.state.doc?.id) {
            await this._loadDocument(this.state.doc.id);
        }
    }

    // PRINT

    openPrintModal() {
        if (!this.state.doc?.id) return;
        this.state.showPrintModal = true;
    }

    closePrintModal() {
        this.state.showPrintModal = false;
    }

    async printDocument() {
        const docId = this.state.doc?.id;
        if (!docId) return;
        this.state.showPrintModal = false;
        await this.action.doAction("sis_document.action_report_sis_document", {
            additionalContext: {
                active_ids: [docId],
                active_model: "sis.document",
                print_type: this.state.printType,
                print_markup: this.state.printMarkup,
            }
        });
    }

    // ITEMS CRUD

    addItem() {
        const seq = this.state.items.length
            ? Math.max(...this.state.items.map(i => i.sequence || 0)) + 10
            : 10;
        const item = {
            id: null, _key: -Date.now(), _dirty: true,
            sequence: seq,
            design: '', purity: '', description: '',
            qty: 1, qty_shipped: 0, qty_balance: 0,
            currency_id: false,
            unit_price: 0, amount: 0,
            unit_cost: 0, cost: 0, profit: 0, profit_pct: 0,
            item_group: '', special_instruction: '', size_remarks: '',
            diamond_weight: 0, stone_weight: 0, diverse_weight: 0, metal_weight: 0,
        };
        this.state.items.push(item);
        this.state.selectedItemId = item._key;
        this.state.docItemsTab = 'general';
        this.state.docDirty = true;
    }

    removeItem(item) {
        if (item.id) this._deletedItemIds.push(item.id);
        const idx = this.state.items.findIndex(i => i._key === item._key);
        if (idx >= 0) this.state.items.splice(idx, 1);
        if (this.state.selectedItemId === item._key) this.state.selectedItemId = null;
        this.state.docDirty = true;
    }

    setItemField(item, field, value) {
        this.state.selectedItemId = item._key;
        item[field] = value;
        item._dirty = true;
        if (field === 'qty' || field === 'unit_price') {
            item.amount = (parseFloat(item.qty) || 0) * (parseFloat(item.unit_price) || 0);
        }
        this.state.docDirty = true;
    }

    _itemVals(item, docId) {
        return {
            document_id: docId,
            sequence: item.sequence || 0,
            design: item.design || '',
            purity: item.purity || '',
            description: item.description || '',
            qty: parseFloat(item.qty) || 0,
            qty_shipped: parseFloat(item.qty_shipped) || 0,
            qty_balance: parseFloat(item.qty_balance) || 0,
            currency_id: this._m2oId(item.currency_id) || false,
            unit_price: parseFloat(item.unit_price) || 0,
            // amount/cost/profit are computed on the model from qty/unit_price/
            // unit_cost — don't send them (the local amount calc is display-only).
            unit_cost: parseFloat(item.unit_cost) || 0,
            item_group: item.item_group || '',
            special_instruction: item.special_instruction || '',
            size_remarks: item.size_remarks || '',
            diamond_weight: parseFloat(item.diamond_weight) || 0,
            stone_weight: parseFloat(item.stone_weight) || 0,
            diverse_weight: parseFloat(item.diverse_weight) || 0,
            metal_weight: parseFloat(item.metal_weight) || 0,
        };
    }

    // PRICES (PDP suggestion)

    selectItem(item) {
        this.state.selectedItemId = item._key;
    }

    async openPricesModal() {
        if (!this.state.doc?.id) return;
        this.state.pricesMarginId = this._m2oId(this.state.doc?.margin_id) || null;
        this.state.pricesCurrencyId = this.companyCurrencyId || null;
        this.state.pricesResult = null;
        this.state.pricesDesigns = [];
        this.state.pricesPurities = [];
        this.state.pricesPurity = null;
        this.state.pricesConvMetal = '';
        this.state.pricesQty = 1;
        this.state.pricesChangeByPct = 0;
        this.state.pricesRoundOff = false;
        this.state.pricesMetal = [];
        this.state.pricesStones = [];
        this.state.pricesHistory = [];
        this.state.pricesProductId = null;
        this.state.showPricesModal = true;

        // Pre-fill model from selected item's design code
        const item = this.state.items.find(it => it._key === this.state.selectedItemId);
        const modelCode = item?.design ? item.design.split('-')[0] : '';
        this.state.pricesModelCode = modelCode;
        if (modelCode) await this._loadPricesDesigns(modelCode, item?.design || null);
    }

    closePricesModal() {
        this.state.showPricesModal = false;
    }

    async onPricesModelChange(ev) {
        const code = (ev.target.value || '').toUpperCase().trim();
        this.state.pricesModelCode = code;
        this.state.pricesProductId = null;
        this.state.pricesDesigns = [];
        this.state.pricesPurities = [];
        this.state.pricesPurity = null;
        this.state.pricesMetal = [];
        this.state.pricesStones = [];
        this.state.pricesHistory = [];
        this.state.pricesResult = null;
        this._allModelMetals = [];
        if (code) await this._loadPricesDesigns(code, null);
    }

    async _loadPricesDesigns(modelCode, preferredDesignCode) {
        const [designs, allMetals] = await Promise.all([
            this.orm.searchRead('pdp.product', [['model_id.code', '=', modelCode]], ['id', 'code'], { order: 'code' }),
            this.orm.searchRead('pdp.product.model.metal', [['model_id.code', '=', modelCode]],
                ['metal_id', 'purity_id', 'weight'], { order: 'purity_id' }),
        ]);
        this.state.pricesDesigns = designs;
        this._allModelMetals = allMetals;

        // Build purity list from metal records
        const seen = new Set();
        const purities = [];
        for (const m of allMetals) {
            if (m.purity_id && !seen.has(m.purity_id[0])) {
                seen.add(m.purity_id[0]);
                purities.push({ id: m.purity_id[0], code: m.purity_id[1] });
            }
        }
        this.state.pricesPurities = purities;
        if (purities.length) this.state.pricesPurity = purities[0].id;
        this._updatePricesMetal();

        // Select preferred design, or first one
        const preferred = preferredDesignCode ? designs.find(d => d.code === preferredDesignCode) : null;
        const toSelect = preferred || designs[0] || null;
        if (toSelect) await this._selectPricesDesign(toSelect.id);
    }

    async onPricesDesignChange(ev) {
        const id = parseInt(ev.target.value) || null;
        if (id) await this._selectPricesDesign(id);
    }

    async _selectPricesDesign(productId) {
        this.state.pricesProductId = productId;
        this.state.pricesResult = null;

        // Load product to get stone_composition_id
        const [prod] = await this.orm.read('pdp.product', [productId], ['code', 'stone_composition_id']);
        if (!prod) return;

        // Stone lines (via composition)
        let stones = [];
        if (prod.stone_composition_id) {
            const compId = Array.isArray(prod.stone_composition_id) ? prod.stone_composition_id[0] : prod.stone_composition_id;
            stones = await this.orm.searchRead(
                'pdp.product.stone', [['composition_id', '=', compId]],
                ['stone_id', 'pieces', 'weight'], {}
            );
        }
        // pdp.product.stone.weight may be stored as 0 (import artefact); fall back to pdp.stone.weight
        if (stones.length) {
            const stoneIds = stones.map(s => Array.isArray(s.stone_id) ? s.stone_id[0] : s.stone_id).filter(Boolean);
            const stoneRecs = stoneIds.length
                ? await this.orm.read('pdp.stone', stoneIds, ['id', 'weight', 'type_id'])
                : [];
            const typeIds = [...new Set(
                stoneRecs.map(r => Array.isArray(r.type_id) ? r.type_id[0] : null).filter(Boolean)
            )];
            const typeRecs = typeIds.length
                ? await this.orm.read('pdp.stone.type', typeIds, ['id', 'name'])
                : [];
            const typeNameById = Object.fromEntries(typeRecs.map(r => [r.id, r.name]));
            const weightById = Object.fromEntries(stoneRecs.map(r => [r.id, r.weight]));
            const stoneTypeIdById = Object.fromEntries(
                stoneRecs.map(r => [r.id, Array.isArray(r.type_id) ? r.type_id[0] : null])
            );
            // Aggregate by stone type name
            const byType = {};
            for (const s of stones) {
                const sid = Array.isArray(s.stone_id) ? s.stone_id[0] : s.stone_id;
                const typeId = stoneTypeIdById[sid];
                const typeName = (typeId && typeNameById[typeId]) || (Array.isArray(s.stone_id) ? s.stone_id[1] : '');
                if (!byType[typeName]) byType[typeName] = { stone: typeName, pcs: 0, weight: 0 };
                byType[typeName].pcs += (s.pieces || 0);
                byType[typeName].weight += s.weight || weightById[sid] || 0;
            }
            this.state.pricesStones = Object.values(byType);
        } else {
            this.state.pricesStones = [];
        }

        // Purchase history for this design
        const code = prod.code || '';
        if (code) {
            const hist = await this.orm.searchRead(
                'sis.document.item', [['design', '=', code]],
                ['document_id', 'qty', 'unit_price', 'amount'],
                { order: 'id desc', limit: 5 }
            );
            this.state.pricesHistory = hist.map(h => ({
                docname: Array.isArray(h.document_id) ? h.document_id[1] : '',
                qty: h.qty,
                uprice: h.unit_price,
                amount: h.amount,
            }));
        } else {
            this.state.pricesHistory = [];
        }
    }

    onPricesPurityChange(ev) {
        this.state.pricesPurity = parseInt(ev.target.value) || null;
        this.state.pricesResult = null;
        this._updatePricesMetal();
    }

    _updatePricesMetal() {
        const purityId = this.state.pricesPurity;
        const filtered = (this._allModelMetals || []).filter(m =>
            !purityId || (m.purity_id && m.purity_id[0] === purityId)
        );
        this.state.pricesMetal = filtered.map(m => {
            const id = Array.isArray(m.metal_id) ? m.metal_id[0] : null;
            return {
                metal: (id && this.metalNameById[id]) || (Array.isArray(m.metal_id) ? m.metal_id[1] : ''),
                weight: m.weight,
            };
        });
    }

    get adjustedPrice() {
        if (!this.state.pricesResult) return 0;
        let price = this.state.pricesResult.totals.price * (this.state.pricesQty || 1);
        if (this.state.pricesChangeByPct) price *= (1 + this.state.pricesChangeByPct / 100);
        return this.state.pricesRoundOff ? Math.round(price) : price;
    }

    get adjustedCost() {
        if (!this.state.pricesResult) return 0;
        return this.state.pricesResult.totals.cost * (this.state.pricesQty || 1);
    }

    async computePdpPrice() {
        if (!this.state.pricesProductId) {
            this.notification.add("Select a design first.", { type: "warning" });
            return;
        }
        this.state.pricesLoading = true;
        this.state.pricesResult = null;
        try {
            const result = await this.orm.call(
                'pdp.price.service', 'compute_price_by_ids',
                [
                    this.state.pricesProductId,
                    this.state.pricesMarginId || false,
                    this.state.pricesCurrencyId || this.companyCurrencyId || false,
                    this.state.pricesPurity || false,
                    this.state.pricesConvMetal || false,
                ]
            );
            this.state.pricesResult = result;
        } catch (e) {
            this.notification.add(`Error: ${e.message || e}`, { type: "danger" });
        } finally {
            this.state.pricesLoading = false;
        }
    }

    async acceptPdpPrice() {
        const item = this.state.items.find(it => it._key === this.state.selectedItemId);
        if (!item?.id || !this.state.pricesResult) return;
        const unitPrice = this.adjustedPrice / (this.state.pricesQty || 1);
        const unitCost = this.adjustedCost / (this.state.pricesQty || 1);
        await this.orm.write('sis.document.item', [item.id], {
            unit_price: unitPrice,
            unit_cost: unitCost,
        });
        this.notification.add("Price applied from PDP.", { type: "success" });
        this.closePricesModal();
        if (this.state.doc?.id) await this._loadDocument(this.state.doc.id);
    }

    // HELPERS

    _m2oId(val) {
        if (!val) return false;
        return Array.isArray(val) ? val[0] : val;
    }

    m2oName(val) {
        if (!val) return "";
        return Array.isArray(val) ? val[1] : String(val);
    }

    fmt(val, dec = 2) {
        return (parseFloat(val) || 0).toFixed(dec);
    }
}

SisWorkspace.template = "sis_frontend.SisWorkspace";
registry.category("actions").add("sis_frontend.workspace", SisWorkspace);
