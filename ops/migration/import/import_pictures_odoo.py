import os
import base64
# from odoo import env


# Configuration
EXPORT_DIR = '/mnt/extra-addons/pictures'  # Container path

def import_images():
    # 1. Import Product Images (Done)
    # products = env['pdp.product'].search([])
    # ... (commented out) ...
    print("Skipping Products (already imported).")

    # 2. Import Model Images
    models = env['pdp.product.model'].search([])
    print(f"Checking {len(models)} models for images...")
    
    model_count = 0
    updated_count = 0
    Picture = env['pdp.picture']
    
    for model in models:
        safe_code = model.code.replace('/', '_').replace('\\', '_')
        safe_code = "".join([c for c in safe_code if c.isalnum() or c in ('-','_','.')])
        filepath = os.path.join(EXPORT_DIR, f"{safe_code}.jpg")
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                img_data = base64.b64encode(f.read())
            
            # Check if picture already exists
            existing = Picture.search([('model_id', '=', model.id)], limit=1)
            if existing:
                existing.write({
                    'image_1920': img_data,
                    'filename': f"{safe_code}.jpg"
                })
                updated_count += 1
            else:
                Picture.create({
                    'model_id': model.id,
                    'image_1920': img_data,
                    'filename': f"{safe_code}.jpg"
                })
                model_count += 1
            
            if (model_count + updated_count) % 100 == 0:
                env.cr.commit()
                print(f"Processed {model_count + updated_count} model images...")
    
    # 3. Import Drawings
    DRAWING_DIR = '/mnt/extra-addons/drawings'
    print(f"Checking Drawings in {DRAWING_DIR}...")
    if not os.path.exists(DRAWING_DIR):
        print(f"ERROR: {DRAWING_DIR} does not exist!")
    
    # Iterate Models
    models = env['pdp.product.model'].search([])
    print(f"Scanning {len(models)} models for drawings...")
    drawing_update_count = 0
    skipped_garbage = 0
    
    for model in models:
        safe_code = model.code.replace('/', '_').replace('\\', '_')
        safe_code = "".join([c for c in safe_code if c.isalnum() or c in ('-','_','.')])
        filepath = os.path.join(DRAWING_DIR, f"{safe_code}.jpg")
        
        # DEBUG for N247
        if model.code == 'N247':
            print(f"DEBUG: Processing N247. Path: {filepath}, Exists: {os.path.exists(filepath)}")
        
        if os.path.exists(filepath):
             with open(filepath, 'rb') as f:
                header = f.read(4)
                f.seek(0)
                # Simple JPEG check (FF D8)
                if header[:2] != b'\xff\xd8':
                    # print(f"Skipping {safe_code}.jpg: Invalid JPEG header {header}")
                    skipped_garbage += 1
                    continue
                
                img_data = base64.b64encode(f.read())
            
             # Find existing picture
             val = {
                 'drawing_1920': img_data,
                 'drawing_filename': f"{safe_code}.jpg"
             }
             
             existing = Picture.search([('model_id', '=', model.id)], limit=1)
             
             try:
                 with env.cr.savepoint():
                     if existing:
                         existing.write(val)
                         drawing_update_count += 1
                     else:
                         val['model_id'] = model.id
                         Picture.create(val)
                         drawing_update_count += 1
                 
                 if drawing_update_count % 50 == 0:
                    env.cr.commit()
                    print(f"Imported {drawing_update_count} drawings...")
             except Exception as e:
                 print(f"ERROR processing {safe_code}.jpg: {e}")
                 skipped_garbage += 1

    env.cr.commit()
    print(f"Finished Drawings. Imported: {drawing_update_count}, Skipped (Invalid): {skipped_garbage}.")

if __name__ == '__main__':
    import_images()
