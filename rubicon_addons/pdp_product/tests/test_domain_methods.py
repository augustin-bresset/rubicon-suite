#!/usr/bin/env python3
"""
Test script for PDP domain methods.
Run from within Odoo shell or as Odoo test.

Usage:
    docker exec -it rubicon-suite-odoo-1 odoo shell -d rubicon < test_domain_methods.py
"""

def test_domain_methods(env):
    """Test all new domain methods on pdp models."""
    results = []
    
    # =========================================================================
    # Test pdp.product.to_dict()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.product.to_dict()")
    print("="*60)
    
    Product = env['pdp.product']
    product = Product.search([], limit=1)
    
    if product:
        try:
            data = product.to_dict()
            assert 'id' in data, "Missing 'id' key"
            assert 'code' in data, "Missing 'code' key"
            assert data['id'] == product.id, "ID mismatch"
            print(f"[PASS] to_dict() returned: {data}")
            results.append(('pdp.product.to_dict()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('pdp.product.to_dict()', False, str(e)))
    else:
        print("[SKIP] No products found in database")
        results.append(('pdp.product.to_dict()', None, 'No data'))

    # =========================================================================
    # Test pdp.product.get_weight_data()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.product.get_weight_data()")
    print("="*60)
    
    if product:
        try:
            weights = product.get_weight_data()
            assert 'stone_original' in weights, "Missing 'stone_original'"
            assert 'stone_recut' in weights, "Missing 'stone_recut'"
            assert 'metal' in weights, "Missing 'metal'"
            print(f"[PASS] get_weight_data() keys: {list(weights.keys())}")
            print(f"       Stones: {len(weights['stone_original'])}, Metals: {len(weights['metal'])}")
            results.append(('pdp.product.get_weight_data()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('pdp.product.get_weight_data()', False, str(e)))

    # =========================================================================
    # Test pdp.product.get_full_data()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.product.get_full_data()")
    print("="*60)
    
    if product:
        try:
            full = product.get_full_data()
            assert 'product' in full, "Missing 'product'"
            assert 'weights' in full, "Missing 'weights'"
            assert 'costing' in full, "Missing 'costing'"
            assert 'metadata' in full, "Missing 'metadata'"
            print(f"[PASS] get_full_data() keys: {list(full.keys())}")
            results.append(('pdp.product.get_full_data()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('pdp.product.get_full_data()', False, str(e)))

    # =========================================================================
    # Test pdp.product.model.to_dict()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.product.model.to_dict()")
    print("="*60)
    
    Model = env['pdp.product.model']
    model = Model.search([], limit=1)
    
    if model:
        try:
            data = model.to_dict()
            assert 'id' in data, "Missing 'id'"
            assert 'code' in data, "Missing 'code'"
            print(f"[PASS] Model to_dict(): {data}")
            results.append(('pdp.product.model.to_dict()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('pdp.product.model.to_dict()', False, str(e)))
    else:
        print("[SKIP] No models found")
        results.append(('pdp.product.model.to_dict()', None, 'No data'))

    # =========================================================================
    # Test pdp.product.model.get_metal_weights()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.product.model.get_metal_weights()")
    print("="*60)
    
    if model:
        try:
            metals = model.get_metal_weights()
            assert isinstance(metals, list), "Should return list"
            print(f"[PASS] get_metal_weights() returned {len(metals)} items")
            if metals:
                print(f"       First: {metals[0]}")
            results.append(('pdp.product.model.get_metal_weights()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('pdp.product.model.get_metal_weights()', False, str(e)))

    # =========================================================================
    # Test pdp.product.stone.composition.get_weight_summary()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.product.stone.composition.get_weight_summary()")
    print("="*60)
    
    Comp = env['pdp.product.stone.composition']
    comp = Comp.search([], limit=1)
    
    if comp:
        try:
            summary = comp.get_weight_summary()
            assert 'total_weight' in summary, "Missing 'total_weight'"
            assert 'total_pieces' in summary, "Missing 'total_pieces'"
            print(f"[PASS] Weight summary: {summary}")
            results.append(('composition.get_weight_summary()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('composition.get_weight_summary()', False, str(e)))
    else:
        print("[SKIP] No compositions found")
        results.append(('composition.get_weight_summary()', None, 'No data'))

    # =========================================================================
    # Test pdp.price.service.compute_product_price()
    # =========================================================================
    print("\n" + "="*60)
    print("TEST: pdp.price.service.compute_product_price()")
    print("="*60)
    
    if product:
        try:
            PriceService = env['pdp.price.service']
            result = PriceService.compute_product_price(product)
            assert 'lines' in result, "Missing 'lines'"
            assert 'totals' in result, "Missing 'totals'"
            assert 'currency' in result, "Missing 'currency'"
            print(f"[PASS] Price service returned keys: {list(result.keys())}")
            print(f"       Totals: {result['totals']}")
            results.append(('pdp.price.service.compute_product_price()', True, None))
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            results.append(('pdp.price.service.compute_product_price()', False, str(e)))

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r[1] is True)
    failed = sum(1 for r in results if r[1] is False)
    skipped = sum(1 for r in results if r[1] is None)
    
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    
    if failed > 0:
        print("\nFailures:")
        for name, status, error in results:
            if status is False:
                print(f"  - {name}: {error}")
    
    return results


# Run if executed directly in Odoo shell
if __name__ == '__main__' or 'env' in dir():
    try:
        test_domain_methods(env)
    except NameError:
        print("Run this script in Odoo shell:")
        print("  docker exec -it rubicon-suite-odoo-1 odoo shell -d rubicon")
