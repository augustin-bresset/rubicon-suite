/** @odoo-module **/

console.log("SIS Workspace JS loading...");

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class SisWorkspace extends Component {
    parseInt = parseInt;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        // Non-reactive lookup tables (loaded once, never change)
        this.margins = [];
        this.payTerms = [];
        this.shippers = [];
        this.sisCountries = [];
        this.allStates = [];
        this.receivingModes = [];
        this.tradeFairs = [];
        this.sisPartners = [];

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
            partyPhones: [],

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

            // ── Print modal ────────────────────────────────────
            showPrintModal: false,
            printType: 'with_weights',
            printMarkup: 0.0,

            // ── Items filter ───────────────────────────────────
            docItemsFilter: '',
            showClosedItems: false,

            // ── Customer address (derived, read-only display) ──
            docPartyAddress: '',
        });

        onWillStart(async () => {
            await this._loadLookups();
        });
    }

    // LOOKUP TABLES (non-reactive)

    async _loadLookups() {
        const [margins, payTerms, shippers, sisCountries, allStates, receivingModes, tradeFairs, sisPartners] =
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
            ]);
        this.margins = margins;
        this.payTerms = payTerms;
        this.shippers = shippers;
        this.sisCountries = sisCountries;
        this.allStates = allStates;
        this.receivingModes = receivingModes;
        this.tradeFairs = tradeFairs;
        this.sisPartners = sisPartners;
    }

    // LOBBY NAVIGATION

    async goParties() {
        await this._reloadParties();
        this.state.page = "parties";
        this.state.partyTab = "general";
    }

    async goDocument(docType) {
        const titles = {
            SQ: "Maintain Sales Quotations.",
            SO: "Maintain Sales Orders.",
            SI: "Maintain Sales Invoices.",
        };
        this.state.docType = docType;
        this.state.docTypeTitle = titles[docType] || "Maintain Sales Documents.";
        await this._reloadDocuments();
        this.state.page = "document";
    }

    goLobby() {
        this.state.page = "lobby";
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

    async _loadParty(partyId) {
        const records = await this.orm.read("res.partner", [partyId], [
            "id", "name", "category_id", "active",
            "title", "street", "city", "state_id", "zip", "country_id",
            "phone", "email", "website", "comment",
            "margin_id", "sis_pay_term_id", "customer_rank",
            "sis_contact",
            // New fields:
            "sis_is_customer", "sis_is_vendor",
            "sis_account", "sis_vendor_account", "sis_vendor_pay_term_id",
            "sis_ship_address", "sis_ship_country_id", "sis_ship_method_id", "sis_ship_fedex_acc", "sis_ship_stamp",
            "bank_ids", "sis_phone_ids", "sis_code"
        ]);
        this.state.party = records[0] ? { ...records[0] } : null;
        this.state.partyDirty = false;

        // Fetch Bank details if any
        if (this.state.party && this.state.party.bank_ids && this.state.party.bank_ids.length > 0) {
            this.state.partyBanks = await this.orm.read("res.partner.bank", this.state.party.bank_ids, [
                "bank_id", "acc_holder_name", "acc_number"
            ]);
        } else {
            this.state.partyBanks = [];
        }

        if (this.state.party && this.state.party.sis_phone_ids && this.state.party.sis_phone_ids.length > 0) {
            this.state.partyPhones = await this.orm.read("res.partner.phone", this.state.party.sis_phone_ids, [
                "name", "phone"
            ]);
        } else {
            this.state.partyPhones = [];
        }

        const idx = this.state.parties.findIndex((p) => p.id === partyId);
        if (idx >= 0) this.state.partyIndex = idx;
    }

    async onSelectParty(ev) {
        const id = parseInt(ev.target.value);
        if (id) await this._loadParty(id);
    }

    setPartyTab(tab) {
        this.state.partyTab = tab;
    }

    setPartyField(field, value) {
        this.state.party[field] = value;
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
            title: "", street: "", city: "", state_id: false, zip: "", country_id: false,
            phone: "", email: "", website: "", comment: "",
            sis_contact: "",
            margin_id: false, sis_pay_term_id: false,
            customer_rank: 1, // keeping this for legacy, but now we use sis_is_customer/vendor
            sis_is_customer: true,
            sis_is_vendor: false,
            sis_account: "", sis_vendor_account: "", sis_vendor_pay_term_id: false,
            sis_ship_address: "", sis_ship_country_id: false, sis_ship_method_id: false, sis_ship_fedex_acc: "", sis_ship_stamp: "",
            bank_ids: [],
            sis_phone_ids: [],
            sis_code: ""
        };
        this.state.partyBanks = [];
        this.state.partyPhones = [];
        this.state.partyDirty = true;
        this.state.partyTab = "general";
    }

    async saveParty() {
        if (!this.state.party) return;
        const p = this.state.party;
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
            sis_contact: p.sis_contact || "",
            margin_id: this._m2oId(p.margin_id),
            sis_pay_term_id: this._m2oId(p.sis_pay_term_id),
            sis_is_customer: p.sis_is_customer || false,
            sis_is_vendor: p.sis_is_vendor || false,
            sis_account: p.sis_account || "",
            sis_vendor_account: p.sis_vendor_account || "",
            sis_vendor_pay_term_id: this._m2oId(p.sis_vendor_pay_term_id),
            sis_ship_address: p.sis_ship_address || "",
            sis_ship_country_id: this._m2oId(p.sis_ship_country_id),
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

        if (p.id) {
            await this.orm.write("res.partner", [p.id], vals);
            this.state.partyDirty = false;
            this.notification.add("Party saved.", { type: "success" });
            await this._reloadParties();
            await this._loadParty(p.id);
        } else {
            const newId = (await this.orm.create("res.partner", [vals]))[0];
            this.state.partyDirty = false;
            this.notification.add("Party created.", { type: "success" });
            await this._reloadParties();
            await this._loadParty(newId);
        }
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
                "margin_id", "date_created", "date_due", "currency_id",
                "party_id", "party_code", "ship_method_id", "pay_term_id",
                "stamp", "notes", "footnotes",
                "customer_po", "rcv_mode_id", "trade_fair_id", "employee",
                "ship_address", "ship_consignee_bank",
                "ship_for_acc_of", "ship_book", "ship_page",
                "total_fob", "freight_insurance", "total_cif",
                "deposit", "total_amount",
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
        this.state.items = items;
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
            currency_id: false,
            party_id: false, party_code: "",
            ship_method_id: false, pay_term_id: false,
            stamp: "", notes: "", footnotes: "",
            customer_po: "", rcv_mode_id: false, trade_fair_id: false, employee: "",
            ship_address: "", ship_consignee_bank: false,
            ship_for_acc_of: "", ship_book: "", ship_page: "",
            total_fob: 0, freight_insurance: 0, total_cif: 0,
            deposit: 0, total_amount: 0,
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
        const vals = {
            name: d.name,
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
        };
        if (d.id) {
            await this.orm.write("sis.document", [d.id], vals);
            this.state.docDirty = false;
            this.notification.add("Document saved.", { type: "success" });
            await this._loadDocument(d.id);
        } else {
            const newId = (await this.orm.create("sis.document", [vals]))[0];
            this.state.docDirty = false;
            this.notification.add("Document created.", { type: "success" });
            await this._reloadDocuments();
            await this._loadDocument(newId);
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
