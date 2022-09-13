# -*- coding: utf-8 -*-
{
    'name': "Health Wellness Website",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website/Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website','website_sale','website_appointment','portal'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/homepage.xml',
        'views/about.xml',
        'views/services_page.xml',
        'views/packages.xml',
        'data/menu.xml',
        'views/res_config.xml',
        'views/templates.xml',
        'views/footer.xml',


    ],
    'assets': {
                'website.assets_wysiwyg':  [
                    'nm_health_wellness_website/static/src/css/website.css',
                ],
    }
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
