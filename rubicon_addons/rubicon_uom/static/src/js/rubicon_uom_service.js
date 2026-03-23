/** @odoo-module **/

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

const rubiconUomService = {
    dependencies: ["orm"],

    start(env, { orm }) {
        let _categories = [];
        let _units = [];
        let _userPrefs = {};   // { category_id: uom_id }
        let _loaded = false;

        async function load() {
            const [categories, units, prefs] = await Promise.all([
                orm.searchRead('rubicon.uom.category', [], ['name', 'code']),
                orm.searchRead('rubicon.uom', [], [
                    'name', 'symbol', 'category_id', 'ratio', 'is_reference', 'is_global_default',
                ]),
                orm.searchRead('rubicon.uom.user.pref',
                    [['user_id', '=', user.userId]],
                    ['category_id', 'uom_id']
                ),
            ]);
            _categories = categories;
            _units = units;
            _userPrefs = {};
            for (const pref of prefs) {
                const catId = Array.isArray(pref.category_id) ? pref.category_id[0] : pref.category_id;
                const uomId = Array.isArray(pref.uom_id) ? pref.uom_id[0] : pref.uom_id;
                _userPrefs[catId] = uomId;
            }
            _loaded = true;
        }

        function _catByCode(code) {
            return _categories.find(c => c.code === code);
        }

        function _uomById(id) {
            return _units.find(u => u.id === id);
        }

        function _unitsForCat(catId) {
            return _units.filter(u => {
                const cid = Array.isArray(u.category_id) ? u.category_id[0] : u.category_id;
                return cid === catId;
            });
        }

        function _activeUom(categoryCode) {
            if (!_loaded) return null;
            const cat = _catByCode(categoryCode);
            if (!cat) {
                console.warn(`[rubicon_uom] Unknown category: ${categoryCode}`);
                return null;
            }
            const catUnits = _unitsForCat(cat.id);
            // 1. user pref
            const prefId = _userPrefs[cat.id];
            if (prefId) {
                const pref = catUnits.find(u => u.id === prefId);
                if (pref) return pref;
            }
            // 2. global default
            const gd = catUnits.find(u => u.is_global_default);
            if (gd) return gd;
            // 3. reference
            return catUnits.find(u => u.is_reference) || null;
        }

        function _refUom(categoryCode) {
            if (!_loaded) return null;
            const cat = _catByCode(categoryCode);
            if (!cat) return null;
            return _unitsForCat(cat.id).find(u => u.is_reference) || null;
        }

        function convert(value, categoryCode) {
            const active = _activeUom(categoryCode);
            if (!active || !value) return value || 0;
            const ref = _refUom(categoryCode);
            if (!ref) return value;
            return value * ref.ratio / active.ratio;
        }

        function symbol(categoryCode) {
            const uom = _activeUom(categoryCode);
            return uom ? uom.symbol : '';
        }

        function format(value, categoryCode, digits = 3) {
            const sym = symbol(categoryCode);
            const val = convert(value, categoryCode);
            if (!sym) return String(value || 0);
            return `${Number(val).toFixed(digits)} ${sym}`;
        }

        function convertExplicit(value, fromUomId, toUomId) {
            const from = _uomById(fromUomId);
            const to = _uomById(toUomId);
            if (!from || !to || !value) return value || 0;
            return value * from.ratio / to.ratio;
        }

        function getUnitsForCategory(categoryCode) {
            if (!_loaded) return [];
            const cat = _catByCode(categoryCode);
            if (!cat) return [];
            return _unitsForCat(cat.id);
        }

        function getActiveUom(categoryCode) {
            return _activeUom(categoryCode);
        }

        function hasUserPref(categoryCode) {
            if (!_loaded) return false;
            const cat = _catByCode(categoryCode);
            return cat ? cat.id in _userPrefs : false;
        }

        async function setUserPref(categoryCode, uomId) {
            const cat = _catByCode(categoryCode);
            if (!cat) return;
            const existing = await orm.searchRead(
                'rubicon.uom.user.pref',
                [['user_id', '=', user.userId], ['category_id', '=', cat.id]],
                ['id']
            );
            if (existing.length) {
                await orm.write('rubicon.uom.user.pref', [existing[0].id], { uom_id: uomId });
            } else {
                await orm.create('rubicon.uom.user.pref', [{
                    user_id: user.userId,
                    category_id: cat.id,
                    uom_id: uomId,
                }]);
            }
            await load();
        }

        async function resetUserPref(categoryCode) {
            const cat = _catByCode(categoryCode);
            if (!cat) return;
            const existing = await orm.searchRead(
                'rubicon.uom.user.pref',
                [['user_id', '=', user.userId], ['category_id', '=', cat.id]],
                ['id']
            );
            if (existing.length) {
                await orm.unlink('rubicon.uom.user.pref', existing.map(r => r.id));
            }
            await load();
        }

        return {
            load,
            convert,
            convertExplicit,
            symbol,
            format,
            getUnitsForCategory,
            getActiveUom,
            hasUserPref,
            setUserPref,
            resetUserPref,
        };
    },
};

registry.category("services").add("rubicon_uom", rubiconUomService);
