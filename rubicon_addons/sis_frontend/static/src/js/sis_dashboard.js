/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class SisDashboard extends Component {
    setup() {
        this.action = useService("action");
    }

    /**
     * Opens an Odoo action by its XML ID
     */
    openAction(xmlId) {
        this.action.doAction(xmlId);
    }

    /**
     * Redirects to a specific URL
     */
    openUrl(url) {
        window.location.href = url;
    }
}

SisDashboard.template = "sis_frontend.SisDashboard";

// Register the component as a client action
registry.category("actions").add("sis_frontend.dashboard", SisDashboard);
