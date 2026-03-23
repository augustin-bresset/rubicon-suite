from odoo.tests.common import TransactionCase

class TestPdpProductCopy(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Setup base required data
        cls.category = cls.env['pdp.product.category'].create({'name': 'Test Category', 'code': 'TCAT', 'waste': 0.0})
        cls.model = cls.env['pdp.product.model'].create({'code': 'MOD01'})
        cls.currency = cls.env['res.currency'].create({'name': 'TC', 'symbol': 'TC'})

        # Setup source product
        cls.source_product = cls.env['pdp.product'].create({
            'code': 'SRC-PROD-01',
            'model_id': cls.model.id,
            'category_id': cls.category.id,
            'active': True,
            'metal': 'YG',
        })

        # Add Stones
        cls.comp = cls.env['pdp.product.stone.composition'].create({'code': 'COMP-SRC-PROD-01'})
        cls.stone_type = cls.env['pdp.stone.type'].create({'name': 'Diamond_Test_Copy', 'code': 'DIATC'})
        cls.stone_shade = cls.env['pdp.stone.shade'].create({'shade': 'White_Test_Copy', 'code': 'WHITC'})
        cls.stone_shape = cls.env['pdp.stone.shape'].create({'shape': 'Round_Test_Copy', 'code': 'RNDTC'})
        cls.stone_size = cls.env['pdp.stone.size'].create({'name': '1.0TC'})
        cls.stone = cls.env['pdp.stone'].create({
            'code': 'DIATCWHITC-RNDTC-1.0TC',
            'type_id': cls.stone_type.id,
            'shade_id': cls.stone_shade.id,
            'shape_id': cls.stone_shape.id,
            'size_id': cls.stone_size.id,
        })
        cls.env['pdp.product.stone'].create({
            'composition_id': cls.comp.id,
            'stone_id': cls.stone.id,
            'pieces': 2,
            'weight': 1.5,
        })
        cls.source_product.write({'stone_composition_id': cls.comp.id})

        # Add Labor
        cls.labor_type = cls.env['pdp.labor.type'].create({
            'code': 'POLISHTC',
            'name': 'Manual Polish Test Copy'
        })
        cls.labor = cls.env['pdp.labor.cost.product'].create({
            'product_id': cls.source_product.id,
            'labor_id': cls.labor_type.id,
            'cost': 150.0,
            'currency_id': cls.currency.id,
        })

        # Add Parts
        cls.part_model = cls.env['pdp.part'].create({
            'code': 'PARTTC',
            'name': 'Test Part Copy'
        })
        cls.part = cls.env['pdp.product.part'].create({
            'product_id': cls.source_product.id,
            'part_id': cls.part_model.id,
            'quantity': 5,
        })

        # Add Misc / Addon
        cls.addon_type = cls.env['pdp.addon.type'].create({
            'code': 'ADDONTC',
            'name': 'Test Addon Copy'
        })
        cls.addon = cls.env['pdp.addon.cost'].create({
            'product_id': cls.source_product.id,
            'addon_id': cls.addon_type.id,
            'cost': 25.0,
            'currency_id': cls.currency.id,
        })

    def test_01_create_blank_product(self):
        """Test creating a blank product with NO fields copied."""
        options = {
            'copy_stone': False,
            'copy_labor': False,
            'copy_parts': False,
            'copy_misc': False,
        }
        new_id = self.env['pdp.product'].copy_product_from_ui(self.source_product.id, 'NEW-BLK-01', options)
        new_product = self.env['pdp.product'].browse(new_id)

        self.assertEqual(new_product.code, 'NEW-BLK-01')
        self.assertEqual(new_product.model_id.id, self.source_product.model_id.id)
        self.assertTrue(new_product.active)
        self.assertEqual(new_product.metal, 'YG')

        # Check that nothing else was copied
        self.assertFalse(new_product.stone_composition_id)
        self.assertEqual(len(self.env['pdp.labor.cost.product'].search([('product_id', '=', new_id)])), 0)
        self.assertEqual(len(self.env['pdp.product.part'].search([('product_id', '=', new_id)])), 0)
        self.assertEqual(len(self.env['pdp.addon.cost'].search([('product_id', '=', new_id)])), 0)

    def test_02_copy_single_field(self):
        """Test copying just the stones, ensuring others remain empty."""
        options = {
            'copy_stone': True,
            'copy_labor': False,
            'copy_parts': False,
            'copy_misc': False,
        }
        new_id = self.env['pdp.product'].copy_product_from_ui(self.source_product.id, 'NEW-STN-01', options)
        new_product = self.env['pdp.product'].browse(new_id)

        self.assertEqual(new_product.code, 'NEW-STN-01')
        self.assertEqual(new_product.metal, 'YG')

        # Check stones copied
        self.assertTrue(new_product.stone_composition_id)
        new_stones = self.env['pdp.product.stone'].search([('composition_id', '=', new_product.stone_composition_id.id)])
        self.assertEqual(len(new_stones), 1)
        self.assertEqual(new_stones[0].pieces, 2)
        self.assertEqual(float(new_stones[0].weight), 1.5)

        # Check others NOT copied
        self.assertEqual(len(self.env['pdp.labor.cost.product'].search([('product_id', '=', new_id)])), 0)
        self.assertEqual(len(self.env['pdp.product.part'].search([('product_id', '=', new_id)])), 0)
        self.assertEqual(len(self.env['pdp.addon.cost'].search([('product_id', '=', new_id)])), 0)

    def test_03_copy_all_fields(self):
        """Test copying ALL fields from source to new product."""
        options = {
            'copy_stone': True,
            'copy_labor': True,
            'copy_parts': True,
            'copy_misc': True,
        }
        new_id = self.env['pdp.product'].copy_product_from_ui(self.source_product.id, 'NEW-ALL-01', options)
        new_product = self.env['pdp.product'].browse(new_id)

        self.assertEqual(new_product.code, 'NEW-ALL-01')
        self.assertEqual(new_product.metal, 'YG')

        # Check stones
        self.assertTrue(new_product.stone_composition_id)
        
        # Check labor
        new_labors = self.env['pdp.labor.cost.product'].search([('product_id', '=', new_id)])
        self.assertEqual(len(new_labors), 1)
        self.assertEqual(new_labors[0].cost, 150.0)

        # Check parts
        new_parts = self.env['pdp.product.part'].search([('product_id', '=', new_id)])
        self.assertEqual(len(new_parts), 1)
        self.assertEqual(new_parts[0].quantity, 5)

        # Check misc
        new_addons = self.env['pdp.addon.cost'].search([('product_id', '=', new_id)])
        self.assertEqual(len(new_addons), 1)
        self.assertEqual(new_addons[0].cost, 25.0)

