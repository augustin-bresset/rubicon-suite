/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class GemNotationWorkspace extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            dicts: { stones: [], grades: [], hues: [], shapes: [] },

            // Compose panel
            stoneId: false,
            gradeId: false,
            hueId: false,
            shapeId: false,
            token: "",
            problems: [],
            omitted: [],

            // Read / look up panel
            query: "",
            read: null,
        });

        onWillStart(async () => {
            this.state.dicts = await this.orm.call(
                "gem.notation", "ui_bootstrap", []);
        });
    }

    get selectedStone() {
        return this.state.dicts.stones.find(
            (s) => s.id === this.state.stoneId);
    }

    async onComponentChange(field, ev) {
        this.state[field] = parseInt(ev.target.value) || false;
        await this.refreshToken();
    }

    async refreshToken() {
        if (!this.state.stoneId) {
            this.state.token = "";
            this.state.problems = [];
            this.state.omitted = [];
            return;
        }
        const result = await this.orm.call("gem.notation", "build_token", [
            this.state.stoneId,
            this.state.gradeId,
            this.state.hueId,
            this.state.shapeId,
        ]);
        this.state.token = result.token;
        this.state.problems = result.problems;
        const stone = this.selectedStone;
        const omitted = [];
        if (stone) {
            if (this.state.gradeId
                    && this.state.gradeId === stone.default_grade_id) {
                omitted.push("grade (default)");
            }
            if (this.state.hueId
                    && (this.state.hueId === stone.default_hue_id
                        || this.state.hueId === stone.implied_hue_id)) {
                omitted.push("hue (default or implied)");
            }
            if (this.state.shapeId
                    && this.state.shapeId === stone.default_shape_id) {
                omitted.push("shape (default)");
            }
        }
        this.state.omitted = omitted;
    }

    async runQuery() {
        const query = (this.state.query || "").trim();
        this.state.read = query
            ? await this.orm.call("gem.notation", "ui_read", [query])
            : null;
    }

    onQueryKeydown(ev) {
        if (ev.key === "Enter") {
            this.runQuery();
        }
    }

    openDictionary(xmlid) {
        this.action.doAction(xmlid);
    }
}

GemNotationWorkspace.template = "gem_notation.Workspace";
registry.category("actions").add("gem_notation_workspace", GemNotationWorkspace);
