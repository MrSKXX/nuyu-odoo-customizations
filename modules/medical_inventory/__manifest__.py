{
    'name': 'NuYu Medical Spa - Inventory Management',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Medical spa inventory with expiry tracking, consignment, and room transfers',
    'author': 'Georges Skaf - Symufolk/Home Logic',
    'website': 'https://github.com/MrSKXX/nuyu-odoo-customizations',
    'depends': [
        'base',
        'stock',
        'product',
        'product_expiry',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_location_data.xml',
        'views/medical_inventory_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}