import os

def debug_import():
    # 1. Check Field
    print("Checking 'drawing_1920' field availability...")
    fields = env['pdp.picture'].fields_get(['drawing_1920'])
    if 'drawing_1920' in fields:
        print("Field 'drawing_1920' EXISTS.")
    else:
        print("Field 'drawing_1920' MISSING!")

    # 2. Check File Access
    DRAWING_DIR = '/mnt/extra-addons/drawings'
    test_file = 'BQ204.jpg'
    filepath = os.path.join(DRAWING_DIR, test_file)
    
    print(f"Checking access to {filepath}...")
    if os.path.exists(filepath):
        print("File EXISTS.")
        try:
            with open(filepath, 'rb') as f:
                data = f.read(10)
                print(f"File READ OK (first 10 bytes: {data})")
        except Exception as e:
            print(f"File READ FAILED: {e}")
    else:
        print("File NOT FOUND via os.path.exists.")
        # List dir to see what IS there
        try:
            print(f"Listing {DRAWING_DIR}:")
            print(os.listdir(DRAWING_DIR)[:10])
        except Exception as e:
            print(f"Listing FAILED: {e}")

    # 3. Check Model Logic for N247
    print(f"Listing {DRAWING_DIR} (first 20):")
    try:
        print(os.listdir(DRAWING_DIR)[:20])
    except Exception as e:
        print(f"ListDir failed: {e}")

    model = env['pdp.product.model'].search([('code', '=', 'N247')], limit=1)
    if model:
        print(f"Model N247 FOUND (ID: {model.id}).")
        safe_code = model.code.replace('/', '_').replace('\\', '_')
        safe_code = "".join([c for c in safe_code if c.isalnum() or c in ('-','_','.')])
        print(f"Safe Code: {safe_code}")
        
        target_path = os.path.join(DRAWING_DIR, f"{safe_code}.jpg")
        print(f"Target Path: {target_path}")
        print(f"Exists? {os.path.exists(target_path)}")
        
        # Check Picture
        pic = env['pdp.picture'].search([('model_id', '=', model.id)], limit=1)
        if pic:
            print(f"Picture record found (ID: {pic.id}). Ready to write.")
        else:
            print("Picture record NOT found.")
    else:
        print("Model N247 NOT FOUND.")

if __name__ == '__main__':
    debug_import()
