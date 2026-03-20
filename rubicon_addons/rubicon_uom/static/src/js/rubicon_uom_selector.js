/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class UomSelector extends Component {
    static template = "rubicon_uom.UomSelector";
    static props = {
        categoryCode: String,
        onUomChange: { type: Function, optional: true },
    };

    setup() {
        this.uomService = useService("rubicon_uom");
        this.state = useState({ version: 0 });
    }

    get units() {
        void this.state.version;  // reactive dependency — forces re-render on version increment
        return this.uomService.getUnitsForCategory(this.props.categoryCode);
    }

    get activeUomId() {
        const uom = this.uomService.getActiveUom(this.props.categoryCode);
        return uom ? uom.id : null;
    }

    get userHasPref() {
        return this.uomService.hasUserPref(this.props.categoryCode);
    }

    async onChangeUom(ev) {
        const uomId = parseInt(ev.target.value, 10);
        try {
            await this.uomService.setUserPref(this.props.categoryCode, uomId);
        } catch (e) {
            console.error('[rubicon_uom] setUserPref failed:', e);
            return;
        }
        this.state.version++;
        if (this.props.onUomChange) {
            this.props.onUomChange(this.props.categoryCode, uomId);
        }
    }

    async onReset() {
        try {
            await this.uomService.resetUserPref(this.props.categoryCode);
        } catch (e) {
            console.error('[rubicon_uom] resetUserPref failed:', e);
            return;
        }
        this.state.version++;
        if (this.props.onUomChange) {
            this.props.onUomChange(this.props.categoryCode, null);
        }
    }
}
