/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class RubiconStorage extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const currentYear = new Date().getFullYear();
        this.state = useState({
            years: [],
            selectedYear: currentYear,
            orders: [],
            selectedOrderId: null,
            rows: [],
            grouped: true,
        });

        onWillStart(async () => {
            await this._loadYears();
        });
    }

    async _loadYears() {
        const years = await this.orm.call("sis.document", "get_available_years", []);
        this.state.years = years;
        if (years.length > 0 && !years.includes(this.state.selectedYear)) {
            this.state.selectedYear = years[0];
        }
        await this._loadOrders();
    }

    async _loadOrders() {
        const orders = await this.orm.call("sis.document", "get_sale_orders_by_year", [this.state.selectedYear]);
        this.state.orders = orders;
        this.state.selectedOrderId = null;
        this.state.rows = [];
    }

    async onYearChange(ev) {
        this.state.selectedYear = parseInt(ev.target.value);
        await this._loadOrders();
    }

    onOrderChange(ev) {
        const val = parseInt(ev.target.value);
        this.state.selectedOrderId = isNaN(val) ? null : val;
        this.state.rows = [];
    }

    async onLoad() {
        if (!this.state.selectedOrderId) return;
        const rows = await this.orm.call("sis.document", "get_stone_list", [this.state.selectedOrderId, this.state.grouped]);
        this.state.rows = rows;
    }

    async onToggleGrouped(ev) {
        this.state.grouped = ev.target.checked;
        if (this.state.selectedOrderId && this.state.rows.length > 0) {
            await this.onLoad();
        }
    }

    async onPrint() {
        if (!this.state.selectedOrderId) return;
        const action = await this.orm.call("sis.document", "action_print_stone_list", [[this.state.selectedOrderId]]);
        await this.action.doAction(action);
    }

    onClose() {
        this.action.doAction({ type: "ir.actions.act_window_close" });
    }
}

RubiconStorage.template = "rubicon_storage.RubiconStorage";

registry.category("actions").add("rubicon_storage_action", RubiconStorage);
