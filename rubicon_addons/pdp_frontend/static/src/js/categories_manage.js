/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class CategoriesManage extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this._deletedCategoryIds = [];

        this.state = useState({
            categories: [],
            isDirty: false,
        });

        onWillStart(async () => {
            await this._loadCategories();
        });
    }

    async _loadCategories() {
        const records = await this.orm.searchRead(
            "pdp.product.category",
            [],
            ["id", "code", "name", "waste"],
            { order: "code asc" }
        );
        this.state.categories = records.map(r => ({
            ...r,
            _key: r.id,
            _dirty: false,
        }));
    }

    m2oId(f) {
        return Array.isArray(f) ? f[0] : f;
    }

    get dirtyCount() {
        return this.state.categories.filter(r => r._dirty).length + this._deletedCategoryIds.length;
    }

    addRow() {
        this.state.categories.push({
            id: null,
            _key: -Date.now(),
            _dirty: true,
            code: "",
            name: "",
            waste: 0,
        });
        this.state.isDirty = true;
    }

    removeRow(row) {
        if (row.id) {
            this._deletedCategoryIds.push(row.id);
        }
        const idx = this.state.categories.indexOf(row);
        if (idx !== -1) {
            this.state.categories.splice(idx, 1);
        }
        this.state.isDirty = true;
    }

    onFieldChange(row, field, value) {
        row[field] = value;
        row._dirty = true;
        this.state.isDirty = true;
    }

    async saveAll() {
        try {
            // Unlink deleted
            if (this._deletedCategoryIds.length) {
                await this.orm.unlink("pdp.product.category", this._deletedCategoryIds);
                this._deletedCategoryIds = [];
            }

            // Write dirty existing rows
            const dirtyExisting = this.state.categories.filter(r => r._dirty && r.id);
            await Promise.all(
                dirtyExisting.map(r =>
                    this.orm.write("pdp.product.category", [r.id], {
                        code: r.code,
                        name: r.name,
                        waste: parseFloat(r.waste) || 0,
                    })
                )
            );

            // Create new rows
            const newRows = this.state.categories.filter(r => r.id === null);
            for (const r of newRows) {
                const [newId] = await this.orm.create("pdp.product.category", [{
                    code: r.code,
                    name: r.name,
                    waste: parseFloat(r.waste) || 0,
                }]);
                r.id = newId;
                r._key = newId;
                r._dirty = false;
            }

            // Clear dirty flags on existing rows
            for (const r of dirtyExisting) {
                r._dirty = false;
            }

            this.state.isDirty = false;

            this.notification.add("Saved.", { type: "success" });
        } catch (e) {
            this.notification.add("Error: " + (e.message || String(e)), { type: "danger" });
        }
    }
}

CategoriesManage.template = "pdp_frontend.categories_manage";
registry.category("actions").add("pdp_frontend.categories_manage", CategoriesManage);
