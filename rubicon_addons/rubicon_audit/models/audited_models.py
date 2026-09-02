"""Apply the audit mixin to the models whose values drive the pricing.

Adding a model to the history means inheriting rubicon.audit.mixin and
listing the sensitive fields in `_audit_fields` (see audit_log.py for the
journal itself).
"""
from odoo import models


class PdpStone(models.Model):
    _name = 'pdp.stone'
    _inherit = ['pdp.stone', 'rubicon.audit.mixin']
    _audit_fields = ('cost', 'currency_id')


class PdpMetal(models.Model):
    _name = 'pdp.metal'
    _inherit = ['pdp.metal', 'rubicon.audit.mixin']
    _audit_fields = ('cost', 'cost_method')


class PdpPartCost(models.Model):
    _name = 'pdp.part.cost'
    _inherit = ['pdp.part.cost', 'rubicon.audit.mixin']
    _audit_fields = ('cost',)


class PdpLaborCostModel(models.Model):
    _name = 'pdp.labor.cost.model'
    _inherit = ['pdp.labor.cost.model', 'rubicon.audit.mixin']
    _audit_fields = ('cost',)


class PdpLaborCostProduct(models.Model):
    _name = 'pdp.labor.cost.product'
    _inherit = ['pdp.labor.cost.product', 'rubicon.audit.mixin']
    _audit_fields = ('cost',)


class PdpAddonCost(models.Model):
    _name = 'pdp.addon.cost'
    _inherit = ['pdp.addon.cost', 'rubicon.audit.mixin']
    _audit_fields = ('cost',)


class PdpMargin(models.Model):
    _name = 'pdp.margin'
    _inherit = ['pdp.margin', 'rubicon.audit.mixin']
    _audit_fields = ('labor_metal_rate', 'labor_stone_rate')


class PdpMarginMetal(models.Model):
    _name = 'pdp.margin.metal'
    _inherit = ['pdp.margin.metal', 'rubicon.audit.mixin']
    _audit_fields = ('rate',)


class PdpMarginStone(models.Model):
    _name = 'pdp.margin.stone'
    _inherit = ['pdp.margin.stone', 'rubicon.audit.mixin']
    _audit_fields = ('rate',)


class PdpMarginAddon(models.Model):
    _name = 'pdp.margin.addon'
    _inherit = ['pdp.margin.addon', 'rubicon.audit.mixin']
    _audit_fields = ('rate',)


class PdpMarginPart(models.Model):
    _name = 'pdp.margin.part'
    _inherit = ['pdp.margin.part', 'rubicon.audit.mixin']
    _audit_fields = ('rate',)


class PdpMarginStoneConditional(models.Model):
    _name = 'pdp.margin.stone.conditional'
    _inherit = ['pdp.margin.stone.conditional', 'rubicon.audit.mixin']
    _audit_fields = ('rate', 'comparative_cost')


class PdpCurrencySetting(models.Model):
    _name = 'pdp.currency.setting'
    _inherit = ['pdp.currency.setting', 'rubicon.audit.mixin']
    _audit_fields = ('rate',)


class SisDocument(models.Model):
    _name = 'sis.document'
    _inherit = ['sis.document', 'rubicon.audit.mixin']
    _audit_fields = ('margin_id',)


class SisDocumentItem(models.Model):
    _name = 'sis.document.item'
    _inherit = ['sis.document.item', 'rubicon.audit.mixin']
    _audit_fields = ('unit_price', 'unit_cost')
    # 200k+ items are bulk-loaded during a migration: creations are normal
    # workflow here, only price changes are worth a journal row.
    _audit_log_create = False
