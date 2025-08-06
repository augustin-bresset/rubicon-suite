
from odoo import fields, Model


class MarginMetal(Model):
    """
    MarginID : varchar(5) [PK, FK → Margins.MarginID]
    StoneCatID : char(1) [PK]
    TypeID : char(5) [PK, FK → StoneTypes.TypeID]
    ShapeID : char(5) [PK, FK → StoneShapes.ShapeID]
    StoneSize : varchar(10) [PK, FK → StoneSizes.StoneSize]
    ShadeID : char(5) [PK, FK → StoneShades.ShadeID]
    StoneMargin : decimal(18)
    """
    
    margin_code = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin.metal",
        required=True
    )
    
    stone = fields.Many2one(
        string="Stone",
        comodel_name="pdp.stone",
        required=True
    )
    
    margin = fields.Float(
        string="Margin",
        digits=(5, 3),
        required=True,
    )
