# Security

## Permission Groups (Odoo)

Defined in `rubicon_addons/rubicon_env/security/security.xml`:

| Group ID | Name | Purpose |
|----------|------|---------|
| `group_rubicon_director` | Director | Full validation and oversight |
| `group_rubicon_manager` | Manager | Team leader, validation rights |
| `group_rubicon_stone_buyer` | Stone Buyer | Stone procurement |
| `group_rubicon_metal_buyer` | Metal Buyer | Metal procurement |
| `group_rubicon_quality_controller` | Quality Controller | QC and traceability |
| `group_rubicon_product_designer` | Product Designer | 3D modeling and design |
| `group_rubicon_officer` | Officer | Sales Order management |
| `group_rubicon_accountant` | Accountant | Financial operations |
| `group_rubicon_stock_manager` | Stock Manager | Inventory operations |
| `group_rubicon_lapidary_supervisor` | Lapidary Supervisor | Production supervision |

## PDP Roles

Defined in `rubicon_addons/pdp_permission/data/pdp_permission_data.xml`:

### Officer
Sales Order management, pricing via PDP, and invoicing.
- Products: read, create, update
- Prices: read, compute, update
- Orders: read, create
- Invoices: read, create
- Export: PDF

### Stone Purchaser
Stone procurement: compares stock, contacts suppliers, creates confirmation vouchers.
- Stones: read, update
- Stock: read
- Vouchers: read, create
- Products/Prices: read

### Metal Purchaser
Metal procurement: compares stock, contacts suppliers, creates confirmation vouchers.
- Metals: read, update
- Stock: read
- Vouchers: read, create
- Products/Prices: read

### Director
Full access. Reviews vouchers, validates prices, approves critical operations.
- ALL permissions including admin.roles and admin.users

### Accountant
Records vouchers in accounting system, manages payments.
- Vouchers: read
- Prices: read
- Invoices: read
- Orders: read

### Stock Manager
Updates stock records, selects resources for production orders.
- Stock: read, update
- Products/Stones/Metals: read
- Orders: read

### Designer
Creates 3D models from client designs.
- Products: read, create, update
- Stones/Metals/Prices: read

### Lapidary Supervisor
Processes orders through production.
- Products/Prices/Stock: read
- Stones/Metals: read
- Orders: read

### Quality Controller
Collects stakeholder signatures, checks quality of WIP.
- Products/Stock: read
- Orders/Stones/Metals: read

## Permission Categories

| Category | Description |
|----------|-------------|
| product | Product management |
| price | Pricing operations |
| stone | Stone compositions |
| metal | Metal compositions |
| labor | Labor costs |
| margin | Margin settings |
| order | Sales orders |
| invoice | Invoice operations |
| stock | Inventory management |
| purchase | Purchasing/vouchers |
| export | PDF/Excel exports |
| admin | Role/user management |