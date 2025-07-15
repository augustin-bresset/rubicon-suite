.
├── alembic
│   ├── env.py
│   ├── __pycache__
│   │   └── env.cpython-312.pyc
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 709b36246ae9_field_delete_rate_from_currency.py
│       ├── 727dee78cdf6_initial_models.py
│       └── __pycache__
│           ├── 709b36246ae9_field_delete_rate_from_currency.cpython-312.pyc
│           └── 727dee78cdf6_initial_models.cpython-312.pyc
├── alembic.ini
├── data
│   ├── backup_pdp
│   │   ├── ComponentTree.csv
│   │   ├── Conditions.csv
│   │   ├── Countries.csv
│   │   ├── Globals.csv
│   │   ├── Grades.csv
│   │   ├── LaborTypes.csv
│   │   ├── Margins.csv
│   │   ├── MatchingModels.csv
│   │   ├── MetalConv.csv
│   │   ├── MetalMargins.csv
│   │   ├── MetalPurities.csv
│   │   ├── MetalPurityConv.csv
│   │   ├── Metals.csv
│   │   ├── MiscMargins.csv
│   │   ├── MiscTypes.csv
│   │   ├── ModelLabor.csv
│   │   ├── ModelMetal.csv
│   │   ├── ModelMetalParts.csv
│   │   ├── Models.csv
│   │   ├── ModelStone.csv
│   │   ├── OrnCatagories.csv
│   │   ├── PartsCost.csv
│   │   ├── Parts.csv
│   │   ├── Prices.csv
│   │   ├── ProductCatagories.csv
│   │   ├── ProductLaborCost.csv
│   │   ├── ProductMiscCost.csv
│   │   ├── ProductParts.csv
│   │   ├── Products.csv
│   │   ├── StoneCatagories.csv
│   │   ├── StoneLots.csv
│   │   ├── StoneMarginsConditional.csv
│   │   ├── StoneMargins.csv
│   │   ├── StoneSettingCost.csv
│   │   ├── StoneSettings.csv
│   │   ├── StoneShades.csv
│   │   ├── StoneShapes.csv
│   │   ├── StoneSizes.csv
│   │   ├── StoneTypes.csv
│   │   ├── StoneWeights.csv
│   │   └── VarSetting.csv
│   ├── backup_sis
│   │   ├── CompanyInfo.csv
│   │   ├── Countries.csv
│   │   ├── Customers.csv
│   │   ├── DocInMode.csv
│   │   ├── DocOrnSizePers.csv
│   │   ├── DocTypes.csv
│   │   ├── dtproperties.csv
│   │   ├── PayTerms.csv
│   │   ├── Regions.csv
│   │   ├── SalesDocItemDetails.csv
│   │   ├── SalesDocItems.csv
│   │   ├── SalesDocs.csv
│   │   ├── Shippers.csv
│   │   └── TradeFairs.csv
│   ├── examples
│   │   ├── client_order.json
│   │   └── client_order_table.csv
│   ├── fixtures
│   │   ├── currencies.json
│   │   ├── gold_purities.json
│   │   └── metals.json
│   └── raw
│       ├── pictures_columns.csv
│       ├── pictures_table_list.txt
│       ├── sis_table_list.txt
│       ├── StoneSettings.csv
│       └── table_list.txt
├── docker-compose.yml
├── meta
│   ├── doc
│   │   └── backup.md
│   ├── documents
│   │   ├── 10_stock_card_EMA25114_P761.pdf
│   │   ├── 11_stock_card_EMA25114_P934.pdf
│   │   ├── 12_stock_card_EMA25114_r403C.pdf
│   │   ├── 13_invoice.pdf
│   │   ├── 1_client_order.pdf
│   │   ├── 2_sales_order.pdf
│   │   ├── 3_sis_metal.pdf
│   │   ├── 4_stones_list_rs.pdf
│   │   ├── 5_metal_prices.pdf
│   │   ├── 6_stone_invoice_on_approval.pdf
│   │   ├── 7_stone_invoice_confirmed.pdf
│   │   ├── 8_stock_update_hand.pdf
│   │   └── 9_stock_update_info.pdf
│   └── report
│       ├── core.tex
│       ├── main.tex
│       └── remarks.md
├── meta.md
├── mssql_backups
│   ├── JMS-PDP21_20250502.bak
│   ├── JMS-SIS21_20250502.bak
│   ├── Pictures.bak
│   ├── table_list.txt
│   └── test.txt
├── odoo_conf
│   └── stop_odoo.conf
├── README.md
├── roadmap.md
├── rubicon_addons
│   └── pdp
│       ├── __init__.py
│       └── __manifest__.py
├── rubicon_core
│   ├── data_import
│   │   ├── cli.py
│   │   ├── mapping.py
│   │   └── tools.py
│   ├── db.py
│   ├── __init__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   └── __init__.cpython-312.pyc
│   │   ├── reference
│   │   │   ├── __init__.py
│   │   │   ├── metal.py
│   │   │   ├── misc.py
│   │   │   ├── parts.py
│   │   │   ├── prices.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── metal.cpython-312.pyc
│   │   │   │   ├── misc.cpython-312.pyc
│   │   │   │   ├── parts.cpython-312.pyc
│   │   │   │   ├── prices.cpython-312.pyc
│   │   │   │   └── stone.cpython-312.pyc
│   │   │   └── stone.py
│   │   └── transaction
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   ├── __init__.cpython-312.pyc
│   │       │   ├── stock.cpython-312.pyc
│   │       │   └── stone.cpython-312.pyc
│   │       ├── stock.py
│   │       └── stone.py
│   ├── __pycache__
│   │   ├── db.cpython-312.pyc
│   │   └── __init__.cpython-312.pyc
│   ├── README.md
│   └── requirements.txt
├── tools
│   ├── export_csv.sh
│   └── export_sqlmd.sh
└── tree.md

29 directories, 135 files
