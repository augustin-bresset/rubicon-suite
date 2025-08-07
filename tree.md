.
├── latex_pdf
│   ├── api
│   │   ├── controller.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── model.py
│   ├── security
│   │   └── ir.model.access.csv
│   ├── services
│   │   ├── generate_exemple.py
│   │   ├── generate_pdf.py
│   │   ├── __init__.py
│   │   └── scan_variables.py
│   ├── templates
│   │   ├── build
│   │   │   ├── test.aux
│   │   │   ├── test.fdb_latexmk
│   │   │   ├── test.fls
│   │   │   ├── test.log
│   │   │   ├── test.pdf
│   │   │   └── test.synctex.gz
│   │   └── test.tex
│   ├── tests
│   │   ├── __init__.py
│   │   ├── test_pdf_generator.py
│   │   └── test_scan_variables.py
│   └── views
│       ├── pdfg_menus.xml
│       ├── pdfg_template_views.xml
│       └── pdfg_views.xml
├── pdp_labor
│   ├── data
│   │   ├── pdp.addon.cost.csv
│   │   ├── pdp.addon.type.csv
│   │   ├── pdp.labor.cost.model.csv
│   │   ├── pdp.labor.cost.product.csv
│   │   └── pdp.labor.type.csv
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models
│   │   ├── addon_type.py
│   │   ├── __init__.py
│   │   ├── labor_type.py
│   │   ├── model_labor_cost.py
│   │   ├── product_addon_cost.py
│   │   └── product_labor_cost.py
│   ├── security
│   │   └── ir.model.access.csv
│   └── views
│       ├── pdp_menus.xml
│       └── pdp_views.xml
├── pdp_margin
│   ├── data
│   │   ├── pdp.margin.addon.csv
│   │   ├── pdp.margin.csv
│   │   ├── pdp.margin.labor.csv
│   │   ├── pdp.margin.metal.csv
│   │   └── pdp.margin.stone.csv
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── margin_addon.py
│   │   ├── margin_labor.py
│   │   ├── margin_metal.py
│   │   ├── margin.py
│   │   └── margin_stone.py
│   ├── security
│   │   └── ir.model.access.csv
│   └── views
│       ├── pdp_menus.xml
│       └── pdp_views.xml
├── pdp_metal
│   ├── data
│   │   ├── pdp.metal.csv
│   │   ├── pdp.metal.purity.csv
│   │   ├── pdp.part.cost.csv
│   │   └── pdp.part.csv
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── metal_purity.py
│   │   ├── metal.py
│   │   ├── part_cost.py
│   │   └── part.py
│   ├── security
│   │   └── ir.model.access.csv
│   └── views
│       ├── pdp_menus.xml
│       └── pdp_views.xml
├── pdp_prices
│   ├── data
│   │   ├── pdp.margin.csv
│   │   ├── pdp.margin.metal.csv
│   │   ├── pdp.margin.misc.csv
│   │   └── pdp.price.csv
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── margin_addon.py
│   │   ├── margin_metal.py
│   │   ├── margin.py
│   │   ├── margin_stone.py
│   │   ├── price_line.py
│   │   └── prices.py
│   ├── security
│   │   └── ir.model.access.csv
│   └── views
│       ├── pdp_menus.xml
│       └── pdp_views.xml
├── pdp_product
│   ├── data
│   │   ├── pdp.product.category.csv
│   │   ├── pdp.product.csv
│   │   ├── pdp.product.model.csv
│   │   ├── pdp.product.model.matching.csv
│   │   ├── pdp.product.model.metal.csv
│   │   ├── pdp.product.part.csv
│   │   ├── pdp.product.stone.composition.csv
│   │   └── pdp.product.stone.csv
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── model_matching.py
│   │   ├── model_metal.py
│   │   ├── model.py
│   │   ├── product_category.py
│   │   ├── product_part.py
│   │   ├── product.py
│   │   ├── product_stone_composition.py
│   │   └── product_stone.py
│   ├── security
│   │   └── ir.model.access.csv
│   └── views
│       ├── pdp_menus.xml
│       └── pdp_views.xml
├── pdp_stone
│   ├── data
│   │   ├── pdp.stone.category.csv
│   │   ├── pdp.stone.csv
│   │   ├── pdp.stone.shade.csv
│   │   ├── pdp.stone.shape.csv
│   │   ├── pdp.stone.size.csv
│   │   ├── pdp.stone.type.csv
│   │   └── pdp.stone.weight.csv
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── stone_category.py
│   │   ├── stone.py
│   │   ├── stone_shade.py
│   │   ├── stone_shape.py
│   │   ├── stone_size.py
│   │   ├── stone_type.py
│   │   └── stone_weight.py
│   ├── security
│   │   └── ir.model.access.csv
│   └── views
│       ├── pdp_menus.xml
│       └── pdp_views.xml
└── rubicon_import
    ├── analysis
    │   ├── __init__.py
    │   └── solder_recutting.py
    ├── import_scripts
    │   ├── generic.py
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   └── __init__.cpython-312.pyc
    │   └── update.py
    ├── __init__.py
    ├── __manifest__.py
    ├── __pycache__
    │   └── __init__.cpython-312.pyc
    ├── raw_to_data
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   ├── __init__.cpython-312.pyc
    │   │   ├── raw_to_data.cpython-312.pyc
    │   │   ├── raw_to_data_labor.cpython-312.pyc
    │   │   ├── raw_to_data_margin.cpython-312.pyc
    │   │   ├── raw_to_data_prices.cpython-312.pyc
    │   │   ├── raw_to_data_product.cpython-312.pyc
    │   │   └── raw_to_data_stone.cpython-312.pyc
    │   ├── raw_to_data_labor.py
    │   ├── raw_to_data_margin.py
    │   ├── raw_to_data_metal.py
    │   ├── raw_to_data_price.py
    │   ├── raw_to_data_product.py
    │   ├── raw_to_data.py
    │   └── raw_to_data_stone.py
    ├── README.md
    └── tools
        ├── __init__.py
        ├── parsing.py
        ├── __pycache__
        │   ├── __init__.cpython-312.pyc
        │   ├── parsing.cpython-312.pyc
        │   └── standard.cpython-312.pyc
        └── standard.py

48 directories, 158 files
