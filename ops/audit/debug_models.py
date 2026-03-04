def debug_models():
    print("Listing first 10 models:")
    models = env['pdp.product.model'].search([], limit=10)
    for m in models:
        print(f" - {m.code}")
    
    print("\nSearching for 'BQ204' variants...")
    variants = env['pdp.product.model'].search([('code', 'ilike', 'BQ204')])
    for m in variants:
        print(f" FOUND: {m.code} (ID: {m.id})")
        
    print("\nSearching for 'N247' variants...")
    variants = env['pdp.product.model'].search([('code', 'ilike', 'N247')])
    for m in variants:
        print(f" FOUND: {m.code} (ID: {m.id})")

if __name__ == '__main__':
    debug_models()
