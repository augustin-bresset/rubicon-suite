# PDP Workflows (Adapted to Implementation)

## 1. Create a New Model
**Goal**: Initialize a new design model structure (e.g. `R133`).
**Method**: Backend (Odoo Menu).
1. Go to `PDP Frontend` -> `Models`.
2. Click `New`.
3. Enter Code (e.g. `R133`), Drawing #, Quotation #.
4. Save.

## 2. Create a New Reference (Product Variant)
**Goal**: Create a product variant (e.g. `R133-GA...`) from a Model.
**Method**: Frontend (PDP Page).
1. Go to `PDP Frontend` -> `PDP Page` (or `/pdp`).
2. Click `List` (in Select Model modal) to find your Model `R133`.
3. Select the Model.
4. Click `New` (Footer Button).
5. Enter attributes (Stones, etc.) in the modal inputs.
6. Click `Make Blank` (Creates `NEW-DESIGN`) or `Copy` (if copying existing).
7. The new product is loaded.
8. Edit details (Stones, Metals, Labor) and click `Save` (Footer).

## 3. Manage Stone Types
**Goal**: Register a new Category/Type of stone.
**Method**: Backend (Odoo Menu).
1. Go to `Manage` -> `Stones and Diamonds`.
2. This opens the `pdp.product.stone` view? (Note: Menu points to `action_pdp_stone`, check if this is Type or Stone).
   *Actual Implementation check*: Menu `Stones and Diamonds` points to `pdp_stone.action_pdp_stone`.
   Use this view to add stone data.

## 4. Manage Metals
**Goal**: Register Metal prices/types.
**Method**: Backend (Odoo Menu).
1. Go to `Manage` -> `Metals`.
2. Edit Metal records.

## 5. Manage Labor Costs
**Goal**: Manage Manual Labor costs (e.g. Setting, Polishing rates) and other labor types.
**Method**: Backend (Odoo Menu).
1. Go to `Manage` -> `Labor Types` (to define new types like "Engraving" or "Manual Polish").
2. Go to `Manage` -> `Labor Costs (Model)` to set costs per model/type.
3. Edit records to update rates.

## 6. Manage Product Images
**Goal**: Associate images with products or models.
**Method**: Backend (Odoo Menu).
1. Go to `PDP Frontend` -> `Products` (to add specific product image).
2. Open a Product.
3. Click the image placeholder (top right) to upload.
4. Save.
5. Alternatively, for Model-level images, go to `PDP Frontend` -> `Models` and upload there.
