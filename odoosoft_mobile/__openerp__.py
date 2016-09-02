# -*- coding: utf-8 -*-
{
    'name': 'Odoosoft Mobile Module',
    'version': '0.2',
    'category': 'odoosoft',
    'complexity': "easy",
    'description': """
Odoosoft Mobile Module""",
    'author': 'Matt Cai',
    'website': 'http://odoosoft.com',
    'depends': ['base', 'web'],
    'data': [
        'views/templates.xml',
        # 'views/contact_templates.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'demo': [],
    'application': True
}
