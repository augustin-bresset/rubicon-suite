#!/usr/bin/env python3
"""
Test PDP domain methods via XML-RPC.
Tests the refactored to_dict() and get_*() methods.
"""

import xmlrpc.client

# Configuration
URL = "http://localhost:8069"
DB = "rubicon"
USERNAME = "admin"
PASSWORD = "admin"

def main():
    print("="*60)
    print("PDP Domain Methods Test")
    print("="*60)
    print(f"URL: {URL}")
    print(f"Database: {DB}")
    print()

    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    
    try:
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    except Exception as e:
        print(f"[FAIL] Authentication error: {e}")
        return 1
    
    if not uid:
        print("[FAIL] Authentication failed - check credentials")
        return 1
    
    print(f"[OK] Authenticated as uid={uid}")
    
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
    
    # =========================================================================
    # Test pdp.product methods
    # =========================================================================
    print("\n" + "-"*60)
    print("Testing pdp.product methods")
    print("-"*60)
    
    # Find a product
    product_ids = models.execute_kw(DB, uid, PASSWORD, 'pdp.product', 'search', [[]], {'limit': 1})
    
    if not product_ids:
        print("[SKIP] No products found in database")
    else:
        product_id = product_ids[0]
        print(f"Testing with product id={product_id}")
        
        # Test to_dict()
        print("\n[TEST] pdp.product.to_dict()")
        try:
            result = models.execute_kw(DB, uid, PASSWORD, 'pdp.product', 'to_dict', [product_id])
            if isinstance(result, dict) and 'id' in result:
                print(f"  [PASS] Returned dict with keys: {list(result.keys())}")
            else:
                print(f"  [FAIL] Unexpected result: {result}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
        
        # Test get_weight_data()
        print("\n[TEST] pdp.product.get_weight_data()")
        try:
            result = models.execute_kw(DB, uid, PASSWORD, 'pdp.product', 'get_weight_data', [product_id])
            if isinstance(result, dict):
                stones = len(result.get('stone_original', []))
                metals = len(result.get('metal', []))
                print(f"  [PASS] Stones: {stones}, Metals: {metals}")
            else:
                print(f"  [FAIL] Unexpected result: {result}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
        
        # Test get_full_data()
        print("\n[TEST] pdp.product.get_full_data()")
        try:
            result = models.execute_kw(DB, uid, PASSWORD, 'pdp.product', 'get_full_data', [product_id])
            if isinstance(result, dict) and 'product' in result:
                print(f"  [PASS] Full data keys: {list(result.keys())}")
            else:
                print(f"  [FAIL] Unexpected result: {type(result)}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    # =========================================================================
    # Test pdp.product.model methods
    # =========================================================================
    print("\n" + "-"*60)
    print("Testing pdp.product.model methods")
    print("-"*60)
    
    model_ids = models.execute_kw(DB, uid, PASSWORD, 'pdp.product.model', 'search', [[]], {'limit': 1})
    
    if not model_ids:
        print("[SKIP] No models found")
    else:
        model_id = model_ids[0]
        print(f"Testing with model id={model_id}")
        
        # Test to_dict()
        print("\n[TEST] pdp.product.model.to_dict()")
        try:
            result = models.execute_kw(DB, uid, PASSWORD, 'pdp.product.model', 'to_dict', [model_id])
            if isinstance(result, dict) and 'code' in result:
                print(f"  [PASS] Model code: {result.get('code')}")
            else:
                print(f"  [FAIL] Unexpected: {result}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
        
        # Test get_metal_weights()
        print("\n[TEST] pdp.product.model.get_metal_weights()")
        try:
            result = models.execute_kw(DB, uid, PASSWORD, 'pdp.product.model', 'get_metal_weights', [model_id])
            if isinstance(result, list):
                print(f"  [PASS] Metal weights: {len(result)} items")
            else:
                print(f"  [FAIL] Expected list, got: {type(result)}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    # =========================================================================
    # Test pdp.price.service
    # =========================================================================
    print("\n" + "-"*60)
    print("Testing pdp.price.service")
    print("-"*60)
    
    if product_ids:
        print("\n[TEST] pdp.price.service.compute_product_price()")
        try:
            # Call API service which uses price service
            result = models.execute_kw(DB, uid, PASSWORD, 'pdp.api.service', 'compute_price', 
                                       [], {'product_id': product_ids[0], 'margin_id': None, 'currency_id': 1})
            if isinstance(result, dict) and 'totals' in result:
                print(f"  [PASS] Totals: {result.get('totals')}")
            elif 'error' in result:
                print(f"  [INFO] {result.get('error')}")
            else:
                print(f"  [FAIL] Unexpected: {result}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    print("\n" + "="*60)
    print("Tests Complete")
    print("="*60)
    return 0

if __name__ == '__main__':
    exit(main())
