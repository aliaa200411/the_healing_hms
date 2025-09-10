# -*- coding: utf-8 -*-
{
    'name': 'Custom Login Page User',
    'version': '18.0.1.0.0',
    'summary': 'Fully custom login page with separate template',
    'description': """
        Custom login page styling with green and blue theme.
        This module only adds CSS styling to the login page.
    """,
    'author': 'Your Name',
    'category': 'Website/Theme',
    'depends': ['web'],
    'data': [
        'views/login_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_login_page_user/static/src/css/login.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}