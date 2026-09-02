# Security

## Access levels and roles (Odoo)

Defined in `rubicon_addons/rubicon_env/security/security.xml` and applied by every
module's `security/ir.model.access.csv` (three rows per model).

| Level ID | Name | Rights on Rubicon models |
|----------|------|--------------------------|
| `group_rubicon_user` | Rubicon / User | read — implied by *Internal User*, so every login has it |
| `group_rubicon_production` | Rubicon / Production Operator | read + write the production floor records: `pcs.transaction`, `pcs.ssp.transaction`, the clearances, barcode tags (no delete, no master data) |
| `group_rubicon_editor` | Rubicon / Editor | read, create, write |
| `group_rubicon_manager` | Rubicon / Manager | read, create, write, delete — implied by *Settings* (administrators) |

Configuration models (`pdp.config`, `rubicon.uom*`, `pdp.role`, `pdp.permission`,
import logs) stay read-only for everyone but administrators.

| Role ID | Name | Implies | Purpose |
|---------|------|---------|---------|
| `group_rubicon_director` | Director | Manager | Full validation and oversight |
| `group_rubicon_manager_role` | Team Manager | Manager | Team leader, validation rights |
| `group_rubicon_officer` | Officer | Editor | Sales Order management |
| `group_rubicon_product_designer` | Product Designer | Editor | 3D modeling and design |
| `group_rubicon_stone_buyer` | Stone Buyer | Editor | Stone procurement |
| `group_rubicon_metal_buyer` | Metal Buyer | Editor | Metal procurement |
| `group_rubicon_stock_manager` | Stock Manager | Editor | Inventory operations |
| `group_rubicon_accountant` | Accountant | User | Financial operations (records vouchers in the external accounting system, reads prices) |
| `group_rubicon_quality_controller` | Quality Controller | Production Operator | records QC checks and collects sign-offs at every production stage (audit §2.3) |
| `group_rubicon_lapidary_supervisor` | Lapidary Supervisor | Production Operator | processes the order through production (audit §2.3) |

Upgrading to `rubicon_env` 18.0.1.1 grants Editor to every existing internal
user (nobody loses write access at deploy time); narrow it by assigning roles.

The audit (`meta/audit.pdf` §2.3) also describes a *Metal Manager* job (3D
model, mold, wax frame): covered by the Product Designer role. The *Metal
Purchaser* process is still marked TODO in the audit and should be completed
there before refining the Metal Buyer role.

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