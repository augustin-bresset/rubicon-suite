from odoo.tests import common, tagged
import uuid

@tagged('post_install', '-at_install')
class TestPDPProcesses(common.TransactionCase):
    
    def setUp(self):
        super(TestPDPProcesses, self).setUp()
        self.Model = self.env['pdp.product.model']
        self.Product = self.env['pdp.product']
        
    def _get_unique_code(self, prefix):
        return f"{prefix}-{str(uuid.uuid4())[:8]}"

    def test_01_create_model_backend(self):
        """ Workflow 1: Create a Model via Backend """
        model_code = self._get_unique_code("R-TEST")
        model = self.Model.create({
            'code': model_code,
            'drawing': 'DRAW-001',
            'quotation': 'QUOT-001'
        })
        
        self.assertTrue(model.id, "Model should be created")
        self.assertEqual(model.code, model_code, "Model code mismatch")
        print(f"Test 1: Created Model {model.code}")
        
    def test_02_create_product_frontend_logic(self):
        """ Workflow 2: Create a Product Variant via Frontend Logic """
        model_code = self._get_unique_code("R-FRONT")
        model = self.Model.create({'code': model_code})
        
        new_design_code = self._get_unique_code("NEW-DESIGN")
        product = self.Product.create({
            'model_id': model.id,
            'code': new_design_code
        })
        
        self.assertTrue(product.id, "Product should be created")
        self.assertEqual(product.model_id.id, model.id, "Product linked to correct model")
        self.assertEqual(product.code, new_design_code, "Product code set correctly")
        
        product.write({'remark': 'Test Remark'})
        self.assertEqual(product.remark, 'Test Remark')

    def test_03_create_product_copy(self):
        """ Workflow 2b: Create by Copy """
        model_code = self._get_unique_code("R-COPY")
        model = self.Model.create({'code': model_code})
        original_code = self._get_unique_code("ORIG")
        original = self.Product.create({'model_id': model.id, 'code': original_code})
        
        copy_code = self._get_unique_code("COPY")
        duplicate = original.copy({'code': copy_code})
        
        self.assertTrue(duplicate.id)
        self.assertNotEqual(duplicate.id, original.id)
        self.assertEqual(duplicate.model_id.id, model.id)
        self.assertEqual(duplicate.code, copy_code)

    def test_04_manage_labor(self):
        """ Workflow 5: Manage Labor Costs """
        LaborType = self.env['pdp.labor.type']
        LaborCost = self.env['pdp.labor.cost.model']
        
        # 1. Create Labor Type (Manual)
        labor_code = self._get_unique_code("LABOR")
        manual_labor = LaborType.create({
            'code': labor_code,
            'name': 'Manual Polish'
        })
        self.assertTrue(manual_labor.id)
        
        # 2. Add Cost for a Model
        model_code = self._get_unique_code("R-LABOR")
        model = self.Model.create({'code': model_code})
        
        # Check if cost was auto-created (Unique Constraint robustness)
        # Check if cost was auto-created
        # Create triggers auto-creation (presumably), so we MUST find it.
        # But create might fail if we try to double-create.
        
        # 1. Try to Find existing
        # self.env.invalidate_all() 
        cost = LaborCost.search([('model_id', '=', model.id), ('labor_id', '=', manual_labor.id)], limit=1)
        
        if not cost:
            # 2. If not found, Create it
            # Need currency_id as it is required
            currency = self.env['res.currency'].search([('name', '=', 'THB')], limit=1) or self.env['res.currency'].search([], limit=1)
            
            try:
                 with self.env.cr.savepoint():
                    cost = LaborCost.create({
                        'model_id': model.id,
                        'labor_id': manual_labor.id,
                        'cost': 150.0,
                        'currency_id': currency.id
                    })
            except Exception:
                # 3. If create blocked (Unique), search AGAIN
                cost = LaborCost.with_context(active_test=False).search([('model_id', '=', model.id), ('labor_id', '=', manual_labor.id)], limit=1)
        
        # If found/created, update
        if cost:
            cost.write({'cost': 150.0})
            
        self.assertTrue(cost, f"Labor Cost should exist for {model.code}")
        self.assertEqual(cost.cost, 150.0)
        print(f"Test 4: Added/Updated Labor Cost to {model.code}")
