{
    'name': 'Seed Theme',
    'description': 'A common colors for seed website',
    'version': '1.0',
    'author': 'Rawan',
    'category': 'Theme/Creative',

    'depends': ['website','web'],
    'data': [
        'views/assets.xml',
    ],
    'images': [
        'static/description/banner.jpg'
    ],

    'assets': {
        'web._assets_primary_variables': [
            'theme_nm_health_wellness_website/static/src/scss/primary_variables.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}