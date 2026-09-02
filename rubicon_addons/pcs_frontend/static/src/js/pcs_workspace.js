/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, onWillStart } from "@odoo/owl";

const SERVICE = "pcs.workspace.service";

const REPORT_TABS = [
    { key: "report_multi", label: "Multi Reports" },
    { key: "report_dept_cost", label: "Doc. Items Dept. Cost" },
    { key: "report_finish", label: "Doc. Items Finish" },
    { key: "report_priorities", label: "Priorities" },
    { key: "report_sis_not_pcs", label: "SIS Not In PCS" },
    { key: "report_order_parts", label: "Order Parts" },
    { key: "report_wax", label: "Wax PDP Weight" },
    { key: "report_summary", label: "Dashboard Summary" },
];

export class PcsWorkspace extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.scanInputRef = useRef("scanInput");

        const screen = this.props.action?.context?.screen || "documents";

        this.state = useState({
            screen,

            // Simulation data switch (shown once simulated documents exist)
            simMode: { include: true, has_sim: false },

            // Sales Documents
            salesDocs: [],
            salesDocId: null,
            salesTab: "docs",           // docs | items
            salesItems: [],

            // Documents
            documents: [],
            docsActiveOnly: true,
            docId: null,
            docTab: "docs",             // docs | barcodes | pbarcodes
            barcodes: [],
            pbarcodes: [],
            newDocRef: "",
            showAddDoc: false,

            // Dashboard
            dashPanel: "prod",          // prod | stone
            dashMode: "depts",          // depts | orders
            dashBarcode: "",
            dashDocumentId: "",
            dashPartyId: "",
            dashCells: [],
            dashTotal: 0,
            orderFilters: { companies: [], documents: [] },

            // Priority
            priorities: [],

            // Scan station
            scanConfig: { weight_control: "off", departments: [], employees: [] },
            scanDeptId: "",
            scanEmployeeId: "",
            scanWeight: "",
            scanStoneWeight: "",
            scanNote: "",
            scanPending: null,
            scanResults: [],

            // PCS Settings (operating modes)
            pcsSettings: { weight_control: "off" },

            // SSP
            sspLookups: { ssps: [], employees: [], departments: [] },
            sspRows: [],
            sspForm: { ssp_id: "", department_id: "", employee_id: "",
                       purity: "", issue_weight: "", receive_weight: "" },
            sspMonthOffset: 0,
            sspConsumption: { start: "", end: "", rows: [] },

            // Clearance
            clearances: [],
            clearanceId: null,
            clearanceTab: "master",     // master | prod | ssp
            clearanceLines: { prod: [], ssp: [] },

            // Operations timeline
            timelineDocs: [],
            timelineDocId: "",
            timelineBarcode: "",
            timelineBarcodes: [],

            // Reports
            reportRows: [],
            reportExtra: [],            // second table (multi filling / priorities bottom)
            reportDeptId: "",
            reportEmployeeId: "",
            reportPrioMode: "assorted",
            reportOrderDocId: "",
            reportPartyId: "",
        });

        onWillStart(async () => {
            this.state.simMode = await this.call("get_sim_mode");
            await this.openScreen(screen);
        });
    }

    async toggleSimMode(ev) {
        await this.call("set_sim_mode", [ev.target.checked]);
        this.state.simMode = await this.call("get_sim_mode");
        await this.openScreen(this.state.screen);
    }

    get reportTabs() {
        return REPORT_TABS;
    }

    get isReportScreen() {
        return this.state.screen.startsWith("report_");
    }

    call(method, args = []) {
        return this.orm.call(SERVICE, method, args);
    }

    async openScreen(screen) {
        this.state.screen = screen;
        const loaders = {
            sales_docs: () => this.loadSalesDocs(),
            documents: () => this.loadDocuments(),
            dashboard: () => this.loadDashboard(),
            priority: () => this.loadPriorities(),
            scan: () => this.loadScanConfig(),
            ssp: () => this.loadSsp(),
            clearance: () => this.loadClearances(),
            pcs_settings: () => this.loadPcsSettings(),
            timeline: () => this.loadTimelineDocs(),
            report_multi: () => this.loadReportMulti(),
            report_dept_cost: () => this.loadSimpleReport("report_doc_items_dept_cost"),
            report_finish: () => this.loadSimpleReport("report_doc_items_finish"),
            report_priorities: () => this.loadReportPriorities(),
            report_sis_not_pcs: () => this.loadSimpleReport("report_sis_not_in_pcs"),
            report_order_parts: () => this.loadReportOrderParts(),
            report_wax: () => this.loadSimpleReport("report_wax_pdp_weight"),
            report_summary: () => this.loadSimpleReport("report_dashboard_summary"),
        };
        if (loaders[screen]) {
            await loaders[screen]();
        }
    }

    // ── Sales Documents ─────────────────────────────────────────────────

    async loadSalesDocs() {
        this.state.salesDocs = await this.call("get_sales_docs");
    }

    async openSalesItems(docId) {
        this.state.salesDocId = docId;
        this.state.salesItems = await this.call("get_sales_doc_items", [docId]);
        this.state.salesTab = "items";
    }

    // ── Documents ───────────────────────────────────────────────────────

    async loadDocuments() {
        this.state.documents = await this.call(
            "get_documents", [this.state.docsActiveOnly]);
    }

    async toggleDocsActiveOnly(ev) {
        this.state.docsActiveOnly = ev.target.checked;
        await this.loadDocuments();
    }

    async selectDocument(docId, tab) {
        this.state.docId = docId;
        await this.openDocTab(tab || "barcodes");
    }

    async openDocTab(tab) {
        this.state.docTab = tab;
        if (!this.state.docId) {
            return;
        }
        if (tab === "barcodes") {
            this.state.barcodes = await this.call("get_barcodes", [this.state.docId]);
        } else if (tab === "pbarcodes") {
            this.state.pbarcodes = await this.call("get_pbarcodes", [this.state.docId]);
        }
    }

    onNewDocKeydown(ev) {
        if (ev.key === "Enter") {
            this.addDocument();
        }
    }

    async addDocument() {
        const ref = (this.state.newDocRef || "").trim();
        if (!ref) {
            return;
        }
        try {
            const docId = await this.call("add_document", [ref]);
            this.state.showAddDoc = false;
            this.state.newDocRef = "";
            await this.loadDocuments();
            await this.selectDocument(docId, "barcodes");
            this.notification.add(`Document ${ref} added.`, { type: "success" });
        } catch (error) {
            this.notification.add(
                error.data?.message || String(error), { type: "danger" });
        }
    }

    async setDocumentActive(doc, ev) {
        await this.call("set_document_active", [doc.id, ev.target.checked]);
        await this.loadDocuments();
    }

    async deleteDocument() {
        if (!this.state.docId) {
            return;
        }
        const doc = this.state.documents.find((d) => d.id === this.state.docId);
        const name = doc ? doc.name : "";
        // pcs.document cascades to its barcodes and their transactions:
        // deleting a document erases its whole scan history.
        if (!confirm(`Delete document "${name}" with all its barcodes and scan history?`)) {
            return;
        }
        await this.call("delete_document", [this.state.docId]);
        this.state.docId = null;
        this.state.docTab = "docs";
        await this.loadDocuments();
    }

    async updatePdp() {
        if (!this.state.docId) {
            return;
        }
        await this.call("update_pdp", [this.state.docId]);
        await this.openDocTab("barcodes");
        this.notification.add("PDP data refreshed.", { type: "success" });
    }

    async saveBarcodeField(row, field, ev) {
        const value = field === "priority" ? ev.target.checked : ev.target.value;
        row[field] = value;
        await this.call("update_barcode", [row.id, { [field]: value }]);
    }

    async printStockCards() {
        if (!this.state.docId) {
            return;
        }
        const reportAction = await this.orm.call(
            "pcs.document", "action_print_stock_cards", [[this.state.docId]]);
        await this.action.doAction(reportAction);
    }

    // ── Dashboard ───────────────────────────────────────────────────────

    onDashboardKeydown(ev) {
        if (ev.key === "Enter") {
            this.loadDashboard();
        }
    }

    async loadDashboard() {
        if (!this.state.orderFilters.companies.length) {
            this.state.orderFilters = await this.call("get_order_filters");
        }
        const result = await this.call("get_dashboard", [
            this.state.dashPanel,
            this.state.dashBarcode || null,
            this.state.dashMode === "orders" && this.state.dashDocumentId
                ? parseInt(this.state.dashDocumentId) : null,
            this.state.dashMode === "orders" && this.state.dashPartyId
                ? parseInt(this.state.dashPartyId) : null,
        ]);
        this.state.dashCells = result.cells;
        this.state.dashTotal = result.total_pieces;
    }

    async setDashPanel(panel) {
        this.state.dashPanel = panel;
        await this.loadDashboard();
    }

    async setDashMode(mode) {
        this.state.dashMode = mode;
        if (mode === "depts") {
            this.state.dashDocumentId = "";
            this.state.dashPartyId = "";
        }
        await this.loadDashboard();
    }

    // ── Priority ────────────────────────────────────────────────────────

    async loadPriorities() {
        this.state.priorities = await this.call("get_priorities");
    }

    async printPriorityList() {
        const reportAction = await this.orm.call(
            "pcs.document", "action_print_priority_list", []);
        await this.action.doAction(reportAction);
    }

    async savePriority(row, ev) {
        const value = parseInt(ev.target.value) || 0;
        row.priority_no = value;
        await this.call("set_priority", [row.id, value]);
    }

    // ── Scan station ────────────────────────────────────────────────────

    async loadScanConfig() {
        this.state.scanConfig = await this.call("get_scan_config");
    }

    get scanEmployees() {
        const deptId = parseInt(this.state.scanDeptId);
        if (!deptId) {
            return this.state.scanConfig.employees;
        }
        return this.state.scanConfig.employees.filter(
            (e) => !e.department_ids.length || e.department_ids.includes(deptId));
    }

    get scanDept() {
        const deptId = parseInt(this.state.scanDeptId);
        return this.state.scanConfig.departments.find((d) => d.id === deptId);
    }

    get scanNeeds() {
        // Which weighing fields to show: under weight control, the
        // department's needs (gold in grams, stones in carats); in legacy
        // mode, the single historical weight field.
        const dept = this.scanDept;
        if (!dept) {
            return [];
        }
        if (this.state.scanConfig.weight_control !== "off") {
            return dept.needs || [];
        }
        return dept.ask_weight ? ["gold"] : [];
    }

    focusScanInput() {
        if (this.scanInputRef.el) {
            this.scanInputRef.el.value = "";
            this.scanInputRef.el.focus();
        }
    }

    async onScanKeydown(ev) {
        if (ev.key !== "Enter") {
            return;
        }
        const value = ev.target.value.trim();
        if (!value) {
            return;
        }
        if (!this.state.scanDeptId) {
            this.notification.add("Select a department first.", { type: "warning" });
            return;
        }
        await this.performScan(value);
    }

    async performScan(value) {
        const result = await this.orm.call("pcs.transaction", "scan", [
            value,
            parseInt(this.state.scanDeptId),
            this.state.scanEmployeeId ? parseInt(this.state.scanEmployeeId) : false,
            parseFloat(this.state.scanWeight) || 0,
            parseFloat(this.state.scanStoneWeight) || 0,
            this.state.scanNote || false,
        ]);
        if (result.status === "weight_required") {
            // Keep the piece pending until its weights are entered.
            this.state.scanPending = { value, ...result };
            return;
        }
        result.time = new Date().toLocaleTimeString();
        this.state.scanResults.unshift(result);
        this.state.scanResults = this.state.scanResults.slice(0, 30);
        this.state.scanPending = null;
        this.state.scanWeight = "";
        this.state.scanStoneWeight = "";
        this.state.scanNote = "";
        this.focusScanInput();
    }

    async confirmPendingScan() {
        if (this.state.scanPending) {
            await this.performScan(this.state.scanPending.value);
            if (this.state.scanPending) {
                this.notification.add("Weights are still missing.",
                                      { type: "warning" });
            }
        }
    }

    cancelPendingScan() {
        this.state.scanPending = null;
        this.state.scanWeight = "";
        this.state.scanStoneWeight = "";
        this.state.scanNote = "";
        this.focusScanInput();
    }

    // ── PCS Settings (operating modes) ──────────────────────────────────

    async loadPcsSettings() {
        this.state.pcsSettings = await this.call("get_pcs_settings");
    }

    async setWeightControl(mode) {
        await this.call("set_pcs_settings", [{ weight_control: mode }]);
        this.state.pcsSettings.weight_control = mode;
        this.state.scanConfig = await this.call("get_scan_config");
        this.notification.add("Weight control mode saved.", { type: "success" });
    }

    // ── Operations timeline ─────────────────────────────────────────────

    async loadTimelineDocs() {
        this.state.timelineDocs = await this.call("get_documents", [false]);
    }

    async loadTimeline() {
        if (!this.state.timelineDocId && !this.state.timelineBarcode) {
            this.state.timelineBarcodes = [];
            return;
        }
        const result = await this.call("get_timeline", [
            this.state.timelineDocId ? parseInt(this.state.timelineDocId) : null,
            this.state.timelineBarcode || null,
        ]);
        this.state.timelineBarcodes = result.barcodes;
    }

    onTimelineKeydown(ev) {
        if (ev.key === "Enter") {
            this.loadTimeline();
        }
    }

    stepChipClass(step) {
        let cls = "pcs-chip";
        cls += step.track === "stone" ? " pcs-chip-stone" : " pcs-chip-prod";
        cls += step.status === "wip" ? " pcs-chip-wip" : " pcs-chip-fin";
        if (step.is_qc) {
            cls += " pcs-chip-qc";
        }
        return cls;
    }

    // ── SSP ─────────────────────────────────────────────────────────────

    async loadSsp() {
        this.state.sspLookups = await this.call("get_ssp_lookups");
        this.state.sspRows = await this.call("get_ssp_transactions");
        await this.loadSspConsumption();
    }

    async loadSspConsumption() {
        this.state.sspConsumption = await this.call(
            "report_ssp_consumption", [this.state.sspMonthOffset]);
    }

    async shiftSspMonth(delta) {
        this.state.sspMonthOffset += delta;
        await this.loadSspConsumption();
    }

    async createSspTransaction() {
        const form = this.state.sspForm;
        if (!form.ssp_id) {
            this.notification.add("Select an SSP type.", { type: "warning" });
            return;
        }
        await this.call("create_ssp_transaction", [{
            ssp_id: parseInt(form.ssp_id),
            department_id: form.department_id ? parseInt(form.department_id) : false,
            employee_id: form.employee_id ? parseInt(form.employee_id) : false,
            purity: form.purity,
            issue_weight: parseFloat(form.issue_weight) || 0,
            receive_weight: parseFloat(form.receive_weight) || 0,
        }]);
        this.state.sspForm = { ssp_id: "", department_id: "", employee_id: "",
                               purity: "", issue_weight: "", receive_weight: "" };
        this.state.sspRows = await this.call("get_ssp_transactions");
        await this.loadSspConsumption();
    }

    // ── Clearance ───────────────────────────────────────────────────────

    async loadClearances() {
        this.state.clearances = await this.call("get_clearances");
    }

    async newClearance() {
        await this.call("create_clearance");
        await this.loadClearances();
    }

    async openClearanceTab(tab) {
        this.state.clearanceTab = tab;
        if (tab !== "master" && this.state.clearanceId) {
            this.state.clearanceLines = await this.call(
                "get_clearance_lines", [this.state.clearanceId]);
        }
    }

    async selectClearance(rowId) {
        this.state.clearanceId = rowId;
        this.state.clearanceLines = await this.call(
            "get_clearance_lines", [rowId]);
    }

    // ── Reports ─────────────────────────────────────────────────────────

    async loadSimpleReport(method) {
        this.state.reportRows = await this.call(method);
        this.state.reportExtra = [];
    }

    async loadReportMulti() {
        if (!this.state.scanConfig.departments.length) {
            this.state.scanConfig = await this.call("get_scan_config");
        }
        if (!this.state.reportDeptId) {
            this.state.reportRows = [];
            this.state.reportExtra = [];
            return;
        }
        const result = await this.call("report_multi", [
            parseInt(this.state.reportDeptId),
            this.state.reportEmployeeId
                ? parseInt(this.state.reportEmployeeId) : null,
        ]);
        this.state.reportRows = result.cutting;
        this.state.reportExtra = result.filling;
    }

    async loadReportPriorities() {
        const result = await this.call(
            "report_priorities", [this.state.reportPrioMode]);
        this.state.reportRows = result.top;
        this.state.reportExtra = result.bottom;
    }

    async loadReportOrderParts() {
        if (!this.state.orderFilters.companies.length) {
            this.state.orderFilters = await this.call("get_order_filters");
        }
        this.state.reportRows = await this.call("report_order_parts", [
            this.state.reportOrderDocId
                ? parseInt(this.state.reportOrderDocId) : null,
            this.state.reportPartyId
                ? parseInt(this.state.reportPartyId) : null,
        ]);
        this.state.reportExtra = [];
    }

    exportCsv(rows, filename) {
        if (!rows.length) {
            this.notification.add("Nothing to export.", { type: "warning" });
            return;
        }
        const columns = Object.keys(rows[0]);
        const escape = (value) => {
            const text = value === null || value === undefined ? "" : String(value);
            return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
        };
        const lines = [columns.join(",")];
        for (const row of rows) {
            lines.push(columns.map((c) => escape(row[c])).join(","));
        }
        const blob = new Blob([lines.join("\n")], { type: "text/csv" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        URL.revokeObjectURL(link.href);
    }
}

PcsWorkspace.template = "pcs_frontend.PcsWorkspace";
registry.category("actions").add("pcs_workspace_action", PcsWorkspace);
