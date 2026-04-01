/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

const CHECK_LABELS = {
    blank_stone_margins: 'Blank Stone Margins',
    blank_stone_costs:   'Blank Stone Costs',
    blank_stone_weights: 'Blank Stone Weights',
};

export class PdpToolsCheckData extends Component {
    static template = "pdp_frontend.ToolsCheckData";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            activeCheck: null,
            results:     [],
            loading:     false,
        });
    }

    get activeLabel() {
        return CHECK_LABELS[this.state.activeCheck] || '';
    }

    async runCheck(checkType) {
        this.state.activeCheck = checkType;
        this.state.loading     = true;
        this.state.results     = [];
        try {
            this.state.results = await this.orm.call(
                'pdp.tools.service', 'get_check_data', [],
                { check_type: checkType }
            );
        } catch (err) {
            this.notification.add(
                err?.data?.message || err?.message || "Query failed.",
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    printReport() {
        window.print();
    }
}

registry.category("actions").add("pdp_frontend.tools_check_data", PdpToolsCheckData);
