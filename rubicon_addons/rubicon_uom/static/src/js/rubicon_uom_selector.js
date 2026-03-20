/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class UomSelector extends Component {
    static template = "rubicon_uom.UomSelector";
    static props = {
        categoryCode: String,
        onUomChange: { type: Function, optional: true },
    };

    setup() {
        this.uomService = useService("rubicon_uom");
    }

    get units() {
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
        await this.uomService.setUserPref(this.props.categoryCode, uomId);
        if (this.props.onUomChange) {
            this.props.onUomChange(this.props.categoryCode, uomId);
        }
    }

    async onReset() {
        await this.uomService.resetUserPref(this.props.categoryCode);
        if (this.props.onUomChange) {
            this.props.onUomChange(this.props.categoryCode, null);
        }
    }
}
