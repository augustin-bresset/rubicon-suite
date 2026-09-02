/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class SisReport extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            years: [],
            year: "",
            orders: [],
            orderId: "",
            showSettings: false,
            rates: { filling: "", setting: "" },
        });

        onWillStart(async () => {
            this.state.years = await this.orm.call(
                "sis.document", "get_stock_card_years", []);
            if (this.state.years.length) {
                this.state.year = String(this.state.years[0]);
                await this.loadOrders();
            }
        });
    }

    async onYearChange(ev) {
        this.state.year = ev.target.value;
        await this.loadOrders();
    }

    async loadOrders() {
        if (!this.state.year) {
            this.state.orders = [];
            this.state.orderId = "";
            return;
        }
        this.state.orders = await this.orm.call(
            "sis.document", "get_stock_card_orders",
            [parseInt(this.state.year)]);
        this.state.orderId = "";
    }

    async toggleSettings() {
        if (!this.state.showSettings) {
            const rates = await this.orm.call(
                "sis.document", "get_labor_minute_rates", []);
            this.state.rates = { filling: String(rates.filling),
                                 setting: String(rates.setting) };
        }
        this.state.showSettings = !this.state.showSettings;
    }

    async saveSettings() {
        const filling = parseFloat(this.state.rates.filling);
        const setting = parseFloat(this.state.rates.setting);
        if (!(filling > 0) || !(setting > 0)) {
            this.notification.add("Rates must be positive numbers.",
                                  { type: "warning" });
            return;
        }
        await this.orm.call(
            "sis.document", "set_labor_minute_rates", [filling, setting]);
        this.notification.add("System settings saved.", { type: "success" });
        this.state.showSettings = false;
    }

    async print() {
        if (!this.state.orderId) {
            this.notification.add("Select a sales order first.",
                                  { type: "warning" });
            return;
        }
        try {
            const reportAction = await this.orm.call(
                "sis.document", "action_print_stock_cards",
                [[parseInt(this.state.orderId)]]);
            await this.action.doAction(reportAction);
        } catch (error) {
            this.notification.add(
                error.data?.message || String(error), { type: "danger" });
        }
    }
}

SisReport.template = "sis_report.SisReport";
registry.category("actions").add("sis_report_action", SisReport);
