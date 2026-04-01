/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class PdpToolsReports extends Component {
    static template = "pdp_frontend.ToolsReports";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        // Non-reactive lookup tables (loaded once)
        this.margins    = [];
        this.purities   = [];
        this.metals     = [];
        this.currencies = [];
        this.categories = [];

        this.state = useState({
            // Report type checkboxes
            repPriceList: true,
            repPictures:  false,
            repByDate:    false,
            repByStone:   false,

            // Parameters — col 1
            marginId:       null,
            purityId:       null,
            metalId:        null,
            currencyId:     null,
            priceListType:  'single',

            // Parameters — col 2
            categoryId:    null,
            fromSeq:       0,
            tillSeq:       100,
            updatedDate:   '',
            applFromDate:  '',
            items:         'all',

            loading: false,
        });

        onWillStart(async () => {
            const [margins, purities, metals, currencies, categories] = await Promise.all([
                this.orm.searchRead("pdp.margin",           [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.metal.purity",     [], ["id", "code"]),
                this.orm.searchRead("pdp.metal",            [], ["id", "code", "name"]),
                this.orm.searchRead("pdp.currency.setting", [], ["id", "currency_id"]),
                this.orm.searchRead("pdp.product.category", [], ["id", "code", "name"]),
            ]);
            this.margins    = margins;
            this.purities   = purities;
            this.metals     = metals;
            this.currencies = currencies.map(c => ({
                id: Array.isArray(c.currency_id) ? c.currency_id[0] : c.currency_id,
                name: Array.isArray(c.currency_id) ? c.currency_id[1] : '',
            }));
            this.categories = categories;
        });
    }

    async makeExcel() {
        const reportTypes = [];
        if (this.state.repPriceList) reportTypes.push('price_list');
        if (this.state.repPictures)  reportTypes.push('pictures');
        if (this.state.repByDate)    reportTypes.push('item_by_date');
        if (this.state.repByStone)   reportTypes.push('item_by_stone');

        if (!reportTypes.length) {
            this.notification.add("Please select at least one report type.", { type: "warning" });
            return;
        }

        this.state.loading = true;
        try {
            const params = {
                margin_id:       this.state.marginId   ? parseInt(this.state.marginId)   : null,
                purity_id:       this.state.purityId   ? parseInt(this.state.purityId)   : null,
                metal_id:        this.state.metalId    ? parseInt(this.state.metalId)    : null,
                currency_id:     this.state.currencyId ? parseInt(this.state.currencyId) : null,
                price_list_type: this.state.priceListType,
                category_id:     this.state.categoryId ? parseInt(this.state.categoryId) : null,
                from_seq:        parseInt(this.state.fromSeq)  || 0,
                till_seq:        parseInt(this.state.tillSeq)  || 100,
                updated_date:    this.state.updatedDate   || null,
                appl_from_date:  this.state.applFromDate  || null,
                items:           this.state.items,
            };

            const result = await this.orm.call(
                'pdp.tools.service', 'generate_report_excel', [],
                { report_types: reportTypes, params }
            );

            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
                return;
            }

            // Decode base64 → Blob → download
            const binary = atob(result.data);
            const buf    = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) buf[i] = binary.charCodeAt(i);
            const blob = new Blob([buf], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            });
            const url = URL.createObjectURL(blob);
            const a   = Object.assign(document.createElement('a'), {
                href: url, download: result.filename,
            });
            a.click();
            URL.revokeObjectURL(url);

            this.notification.add("Excel file generated.", { type: "success" });
        } catch (err) {
            this.notification.add(err?.data?.message || err?.message || "Failed to generate report.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }
}

registry.category("actions").add("pdp_frontend.tools_reports", PdpToolsReports);
