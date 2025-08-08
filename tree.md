.
├── alembic
│   ├── env.py
│   ├── __pycache__
│   │   └── env.cpython-312.pyc
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 3b5a5a348ade_initial_models.py
│       └── __pycache__
│           ├── 36a6887f925f_initial_schema_with_integer_ids.cpython-312.pyc
│           ├── 3b5a5a348ade_initial_models.cpython-312.pyc
│           ├── 709b36246ae9_field_delete_rate_from_currency.cpython-312.pyc
│           ├── 7221da7dc787_initial_schema_with_integer_ids.cpython-312.pyc
│           ├── 727dee78cdf6_initial_models.cpython-312.pyc
│           ├── 8366d3448a28_normalize_id_integer_autoincrement.cpython-312.pyc
│           ├── 9f18c7ca38b3_initial_schema_with_integer_ids.cpython-312.pyc
│           ├── c92f563785e7_initial_schema_with_integer_ids.cpython-312.pyc
│           └── fbd895d3e4de_initial_schema_with_integer_ids.cpython-312.pyc
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
│   │   ├── ProductCategories.csv
│   │   ├── ProductLaborCost.csv
│   │   ├── ProductMiscCost.csv
│   │   ├── ProductParts.csv
│   │   ├── Products.csv
│   │   ├── StoneCategories.csv
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
│   ├── odoo
│   ├── raw
│   │   ├── pictures_columns.csv
│   │   ├── pictures_table_list.txt
│   │   ├── sis_table_list.txt
│   │   ├── StoneSettings.csv
│   │   └── table_list.txt
│   └── tmp
│       └── ModelStone.csv
├── docker-compose.yml
├── external_addons
│   └── oca_currency
│       ├── checklog-odoo.cfg
│       ├── currency_rate_update
│       │   ├── data
│       │   │   └── cron.xml
│       │   ├── i18n
│       │   │   ├── am.po
│       │   │   ├── ar.po
│       │   │   ├── bg.po
│       │   │   ├── bs.po
│       │   │   ├── ca_ES.po
│       │   │   ├── ca.po
│       │   │   ├── cs.po
│       │   │   ├── currency_rate_update.pot
│       │   │   ├── da.po
│       │   │   ├── de.po
│       │   │   ├── el_GR.po
│       │   │   ├── en_GB.po
│       │   │   ├── es_AR.po
│       │   │   ├── es_CL.po
│       │   │   ├── es_CO.po
│       │   │   ├── es_CR.po
│       │   │   ├── es_DO.po
│       │   │   ├── es_EC.po
│       │   │   ├── es_ES.po
│       │   │   ├── es_MX.po
│       │   │   ├── es_PE.po
│       │   │   ├── es.po
│       │   │   ├── es_PY.po
│       │   │   ├── es_VE.po
│       │   │   ├── et.po
│       │   │   ├── eu.po
│       │   │   ├── fa.po
│       │   │   ├── fi.po
│       │   │   ├── fr_CA.po
│       │   │   ├── fr_CH.po
│       │   │   ├── fr.po
│       │   │   ├── gl_ES.po
│       │   │   ├── gl.po
│       │   │   ├── gu.po
│       │   │   ├── he.po
│       │   │   ├── hr_HR.po
│       │   │   ├── hr.po
│       │   │   ├── hu.po
│       │   │   ├── id.po
│       │   │   ├── it.po
│       │   │   ├── ja.po
│       │   │   ├── ko.po
│       │   │   ├── lt_LT.po
│       │   │   ├── lt.po
│       │   │   ├── lv.po
│       │   │   ├── mk.po
│       │   │   ├── mn.po
│       │   │   ├── nb_NO.po
│       │   │   ├── nb.po
│       │   │   ├── nl_BE.po
│       │   │   ├── nl.po
│       │   │   ├── pl.po
│       │   │   ├── pt_BR.po
│       │   │   ├── pt.po
│       │   │   ├── pt_PT.po
│       │   │   ├── ro.po
│       │   │   ├── ru.po
│       │   │   ├── sk.po
│       │   │   ├── sl.po
│       │   │   ├── sr@latin.po
│       │   │   ├── sr.po
│       │   │   ├── sv.po
│       │   │   ├── th.po
│       │   │   ├── tr.po
│       │   │   ├── tr_TR.po
│       │   │   ├── uk.po
│       │   │   ├── vi.po
│       │   │   ├── vi_VN.po
│       │   │   ├── zh_CN.po
│       │   │   └── zh_TW.po
│       │   ├── __init__.py
│       │   ├── __manifest__.py
│       │   ├── models
│       │   │   ├── __init__.py
│       │   │   ├── res_company.py
│       │   │   ├── res_config_settings.py
│       │   │   ├── res_currency_rate_provider_ECB.py
│       │   │   ├── res_currency_rate_provider.py
│       │   │   └── res_currency_rate.py
│       │   ├── pyproject.toml
│       │   ├── readme
│       │   │   ├── CONFIGURE.md
│       │   │   ├── CONTRIBUTORS.md
│       │   │   ├── DESCRIPTION.md
│       │   │   └── USAGE.md
│       │   ├── README.rst
│       │   ├── security
│       │   │   ├── ir.model.access.csv
│       │   │   └── res_currency_rate_provider.xml
│       │   ├── static
│       │   │   └── description
│       │   │       ├── icon.png
│       │   │       └── index.html
│       │   ├── tests
│       │   │   ├── __init__.py
│       │   │   └── test_currency_rate_update.py
│       │   ├── views
│       │   │   ├── res_config_settings.xml
│       │   │   ├── res_currency_rate_provider.xml
│       │   │   └── res_currency_rate.xml
│       │   └── wizards
│       │       ├── __init__.py
│       │       ├── res_currency_rate_update_wizard.py
│       │       └── res_currency_rate_update_wizard.xml
│       ├── eslint.config.cjs
│       ├── LICENSE
│       ├── prettier.config.cjs
│       ├── README.md
│       └── setup
│           └── _metapackage
│               └── pyproject.toml
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
│   ├── report
│   │   ├── core.tex
│   │   ├── main.tex
│   │   └── remarks.md
│   └── sandbox
│       ├── diagram.md
│       └── diagram.png
├── meta.md
├── mssql_backups
│   ├── CompanyInfo.csv
│   ├── JMS-PDP21_20250502.bak
│   ├── JMS-SIS21_20250502.bak
│   ├── Pictures.bak
│   ├── table_list.txt
│   └── test.txt
├── odoo_conf
│   └── odoo.conf
├── README.md
├── roadmap.md
├── rubicon_addons
│   ├── latex_pdf
│   │   ├── api
│   │   │   ├── controller.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── model.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   ├── services
│   │   │   ├── generate_exemple.py
│   │   │   ├── generate_pdf.py
│   │   │   ├── __init__.py
│   │   │   └── scan_variables.py
│   │   ├── templates
│   │   │   ├── build
│   │   │   │   ├── test.aux
│   │   │   │   ├── test.fdb_latexmk
│   │   │   │   ├── test.fls
│   │   │   │   ├── test.log
│   │   │   │   ├── test.pdf
│   │   │   │   └── test.synctex.gz
│   │   │   └── test.tex
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   ├── test_pdf_generator.py
│   │   │   └── test_scan_variables.py
│   │   └── views
│   │       ├── pdfg_menus.xml
│   │       ├── pdfg_template_views.xml
│   │       └── pdfg_views.xml
│   ├── pdp_labor
│   │   ├── data
│   │   │   ├── pdp.addon.cost.csv
│   │   │   ├── pdp.addon.type.csv
│   │   │   ├── pdp.labor.cost.model.csv
│   │   │   ├── pdp.labor.cost.product.csv
│   │   │   └── pdp.labor.type.csv
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   ├── addon_type.py
│   │   │   ├── __init__.py
│   │   │   ├── labor_type.py
│   │   │   ├── model_labor_cost.py
│   │   │   ├── product_addon_cost.py
│   │   │   └── product_labor_cost.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   └── views
│   │       ├── pdp_menus.xml
│   │       └── pdp_views.xml
│   ├── pdp_margin
│   │   ├── data
│   │   │   ├── pdp.margin.addon.csv
│   │   │   ├── pdp.margin.csv
│   │   │   ├── pdp.margin.labor.csv
│   │   │   ├── pdp.margin.metal.csv
│   │   │   └── pdp.margin.stone.csv
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── margin_addon.py
│   │   │   ├── margin_labor.py
│   │   │   ├── margin_metal.py
│   │   │   ├── margin.py
│   │   │   └── margin_stone.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   └── views
│   │       ├── pdp_menus.xml
│   │       └── pdp_views.xml
│   ├── pdp_metal
│   │   ├── data
│   │   │   ├── pdp.metal.csv
│   │   │   ├── pdp.metal.purity.csv
│   │   │   ├── pdp.part.cost.csv
│   │   │   └── pdp.part.csv
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── metal_purity.py
│   │   │   ├── metal.py
│   │   │   ├── part_cost.py
│   │   │   └── part.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   └── views
│   │       ├── pdp_menus.xml
│   │       └── pdp_views.xml
│   ├── pdp_prices
│   │   ├── data
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── price_abstract.py
│   │   │   ├── price_addon.py
│   │   │   ├── price_labor.py
│   │   │   ├── price_metal.py
│   │   │   ├── price.py
│   │   │   └── price_stone.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   └── views
│   │       ├── pdp_menus.xml
│   │       └── pdp_views.xml
│   ├── pdp_product
│   │   ├── data
│   │   │   ├── pdp.product.category.csv
│   │   │   ├── pdp.product.csv
│   │   │   ├── pdp.product.model.csv
│   │   │   ├── pdp.product.model.matching.csv
│   │   │   ├── pdp.product.model.metal.csv
│   │   │   ├── pdp.product.part.csv
│   │   │   ├── pdp.product.stone.composition.csv
│   │   │   └── pdp.product.stone.csv
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── model_matching.py
│   │   │   ├── model_metal.py
│   │   │   ├── model.py
│   │   │   ├── product_category.py
│   │   │   ├── product_part.py
│   │   │   ├── product.py
│   │   │   ├── product_stone_composition.py
│   │   │   └── product_stone.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   └── views
│   │       ├── pdp_menus.xml
│   │       └── pdp_views.xml
│   ├── pdp_stone
│   │   ├── data
│   │   │   ├── pdp.stone.category.csv
│   │   │   ├── pdp.stone.csv
│   │   │   ├── pdp.stone.shade.csv
│   │   │   ├── pdp.stone.shape.csv
│   │   │   ├── pdp.stone.size.csv
│   │   │   ├── pdp.stone.type.csv
│   │   │   └── pdp.stone.weight.csv
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── stone_category.py
│   │   │   ├── stone.py
│   │   │   ├── stone_shade.py
│   │   │   ├── stone_shape.py
│   │   │   ├── stone_size.py
│   │   │   ├── stone_type.py
│   │   │   └── stone_weight.py
│   │   ├── security
│   │   │   └── ir.model.access.csv
│   │   └── views
│   │       ├── pdp_menus.xml
│   │       └── pdp_views.xml
│   ├── rubicon_env
│   │   ├── hooks.py
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models
│   │   │   └── __init__.py
│   │   └── scripts
│   │       ├── init_currency.py
│   │       └── __init__.py
│   └── rubicon_import
│       ├── analysis
│       │   ├── __init__.py
│       │   └── solder_recutting.py
│       ├── import_scripts
│       │   ├── generic.py
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   └── __init__.cpython-312.pyc
│       │   └── update.py
│       ├── __init__.py
│       ├── __manifest__.py
│       ├── __pycache__
│       │   └── __init__.cpython-312.pyc
│       ├── raw_to_data
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   ├── raw_to_data.cpython-312.pyc
│       │   │   ├── raw_to_data_labor.cpython-312.pyc
│       │   │   ├── raw_to_data_margin.cpython-312.pyc
│       │   │   ├── raw_to_data_metal.cpython-312.pyc
│       │   │   ├── raw_to_data_prices.cpython-312.pyc
│       │   │   ├── raw_to_data_product.cpython-312.pyc
│       │   │   └── raw_to_data_stone.cpython-312.pyc
│       │   ├── raw_to_data_labor.py
│       │   ├── raw_to_data_margin.py
│       │   ├── raw_to_data_metal.py
│       │   ├── raw_to_data_price.py
│       │   ├── raw_to_data_product.py
│       │   ├── raw_to_data.py
│       │   └── raw_to_data_stone.py
│       ├── README.md
│       ├── tests
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   └── test_import_csv.cpython-312.pyc
│       │   └── test_import_csv.py
│       └── tools
│           ├── __init__.py
│           ├── parsing.py
│           ├── __pycache__
│           │   ├── __init__.cpython-312.pyc
│           │   ├── parsing.cpython-312.pyc
│           │   └── standard.cpython-312.pyc
│           └── standard.py
├── rubicon_core
│   ├── data_import
│   │   ├── cli.py
│   │   ├── __init__.py
│   │   ├── mapping.py
│   │   ├── processors.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── mapping.cpython-312.pyc
│   │   │   ├── processors.cpython-312.pyc
│   │   │   └── tools.cpython-312.pyc
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
│   ├── export_sqlmd.sh
│   └── pdp_data.py
├── tree.md
└── workflow.md

99 directories, 419 files
