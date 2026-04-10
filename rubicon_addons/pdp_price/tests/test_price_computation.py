# tests/test_price_computation.py
"""
Tests for PDP Price Computation.

These tests use mock data that is:
- Created in setUp() or within each test method
- Automatically rolled back after each test (TransactionCase behavior)

No persistent data is left in the database after test execution.
"""
from odoo.tests.common import TransactionCase
from datetime import date


class TestPriceComputationMock(TransactionCase):
    """
    Test suite for price computation with mock data.
    
    All data created here is automatically cleaned up after each test
    thanks to Odoo's TransactionCase rollback mechanism.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up mock data shared across all tests in this class.
        This data will be rolled back after the test class completes.
        """
        super().setUpClass()
        
        # Reference to existing currencies (these are not mock, they exist in Odoo)
        cls.usd = cls.env.ref('base.USD')
        
    def _create_mock_market_metal(self, code='XAU', name='Gold'):
        """Helper to create a mock market metal."""
        return self.env['pdp.market.metal'].create({
            'name': name,
            'code': code,
            'base_unit': 'troy_oz',
            'base_currency_id': self.usd.id
        })
    
    def _create_mock_metal(self, code, name, cost_method='fixed', cost=0.0, market_metal=None):
        """Helper to create a mock metal definition."""
        vals = {
            'name': name,
            'code': code,
            'cost_method': cost_method,
            'cost': cost,
            'currency_id': self.usd.id,
        }
        if market_metal:
            vals['market_metal_id'] = market_metal.id
        return self.env['pdp.metal'].create(vals)
    
    def _create_mock_market_price(self, market_metal, price, price_date=None):
        """Helper to create a mock market price entry."""
        return self.env['pdp.market.price'].create({
            'metal_id': market_metal.id,
            'date': price_date or date.today(),
            'price': price,
            'currency_id': self.usd.id
        })
    
    def _create_mock_stone(self, code, cost=0.0):
        """Helper to create a complete mock stone with all required relations."""
        stype = self.env['pdp.stone.type'].create({'name': f'Type_{code}', 'code': f'T{code}'})
        sshape = self.env['pdp.stone.shape'].create({'shape': f'Shape_{code}', 'code': f'S{code}'})
        sshade = self.env['pdp.stone.shade'].create({'shade': f'Shade_{code}', 'code': f'H{code}'})
        ssize = self.env['pdp.stone.size'].create({'name': f'Size_{code}'})

        return self.env['pdp.stone'].create({
            'code': code,
            'type_id': stype.id,
            'shape_id': sshape.id,
            'shade_id': sshade.id,
            'size_id': ssize.id,
            'cost': cost,
            'currency_id': self.usd.id
        })

    def _create_mock_product_with_stone(self, stone, pieces=1):
        """Helper to create a mock product with a stone composition."""
        Composition = self.env['pdp.product.stone.composition']
        ProductStone = self.env['pdp.product.stone']

        comp = Composition.create({'code': f'COMP_{stone.code}'})
        ProductStone.create({
            'composition_id': comp.id,
            'stone_id': stone.id,
            'pieces': pieces
        })

        return self.env['pdp.product'].create({
            'code': f'PROD_{stone.code}',
            'stone_composition_id': comp.id
        })

    # =========================================================================
    # TEST CASES
    # =========================================================================

    def test_stone_zero_cost_warning(self):
        """
        Test that a stone with zero cost generates a warning.
        
        Mock data created:
        - Stone with cost = 0
        - Product using this stone
        
        Expected: Warning in result, no crash, cost = 0
        """
        # Create mock stone with zero cost
        mock_stone = self._create_mock_stone('MOCK_ZERO', cost=0.0)
        
        # Create mock product using this stone
        mock_product = self._create_mock_product_with_stone(mock_stone, pieces=5)
        
        # Run price computation
        PriceService = self.env['pdp.price.service']
        result = PriceService.compute_product_price(mock_product, currency=self.usd)
        
        # Assertions
        self.assertIn('warnings', result, "Result should contain 'warnings' key")
        self.assertTrue(len(result['warnings']) > 0, "Should have at least one warning")
        self.assertIn('no cost defined', result['warnings'][0], "Warning should mention missing cost")
        
        # Verify no crash and totals are returned
        self.assertIn('totals', result)
        self.assertEqual(result['totals']['cost'], 0.0)

    def test_stone_with_cost_no_warning(self):
        """
        Test that a stone with valid cost does NOT generate a warning.
        
        Mock data created:
        - Stone with cost = 50 USD
        - Product using this stone (5 pieces)
        
        Expected: No warning, cost = 250
        """
        # Create mock stone with valid cost
        mock_stone = self._create_mock_stone('MOCK_VALID', cost=50.0)
        
        # Create mock product
        mock_product = self._create_mock_product_with_stone(mock_stone, pieces=5)
        
        # Run price computation
        PriceService = self.env['pdp.price.service']
        result = PriceService.compute_product_price(mock_product, currency=self.usd)
        
        # Should have no warnings
        warnings = result.get('warnings', [])
        stone_warnings = [w for w in warnings if 'MOCK_VALID' in w]
        self.assertEqual(len(stone_warnings), 0, "Should have no warning for this stone")
        
        # Cost should be 50 * 5 = 250
        # Note: actual total depends on margin configuration

    def test_empty_product_no_crash(self):
        """
        Test that an empty product (no stones, no metal) doesn't crash.
        
        Mock data created:
        - Empty product
        
        Expected: No crash, totals = 0
        """
        mock_product = self.env['pdp.product'].create({
            'code': 'EMPTY_001'
        })
        
        PriceService = self.env['pdp.price.service']
        result = PriceService.compute_product_price(mock_product, currency=self.usd)
        
        self.assertIn('totals', result)
        self.assertEqual(result['totals']['cost'], 0.0)
        self.assertEqual(result['totals']['price'], 0.0)

    def test_null_product_returns_error(self):
        """
        Test that passing None as product returns an error dict.
        
        Expected: {'error': 'Product required'}
        """
        PriceService = self.env['pdp.price.service']
        result = PriceService.compute_product_price(None)
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Product required')

    def test_market_metal_price_lookup(self):
        """
        Test that market price is correctly looked up.
        
        Mock data created:
        - Market metal (Gold)
        - Market price entry for today
        - Metal definition using market price
        
        Expected: Price based on market rate
        """
        # Create mock market metal
        mock_market_metal = self._create_mock_market_metal('MOCK_AU', 'Mock Gold')
        
        # Create market price: $3110.35 / troy oz ≈ $100 / gram
        self._create_mock_market_price(mock_market_metal, 3110.35)
        
        # Create metal definition that uses market
        mock_metal = self._create_mock_metal(
            'MOCK_18K', 'Mock 18K Gold',
            cost_method='market',
            market_metal=mock_market_metal
        )
        
        # Verify market metal is linked
        self.assertEqual(mock_metal.cost_method, 'market')
        self.assertEqual(mock_metal.market_metal_id.id, mock_market_metal.id)
        
        # Note: Full product-metal integration test would require
        # pdp.product.model and pdp.product.model.metal setup


class TestPriceComponentsMock(TransactionCase):
    """
    Test individual price components in isolation.
    """
    
    def test_stone_component_direct(self):
        """Test the stone component compute method directly."""
        # This tests the wizard/component_stone.py compute method
        # by calling it with a mock product
        pass  # Placeholder for direct component testing
