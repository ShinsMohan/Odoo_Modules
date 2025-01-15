{
    'name': 'HR Dashboard',
    'version': '17.0.1.0.0',
    'summary': """Enterprise HR Management Dashboard.""",
    'description': """Enterprise HR Management Dashboard.""",
    'category': 'HR',
    'author': 'Code-OX Technologies',
    'company': 'Code-OX Technologies',
    'maintainer': 'Code-OX Technologies',
    'website': "https://www.code-ox.com/",
    'depends': ['hr', 'hr_contract', 'hr_holidays', 'hr_payroll', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard.xml',
        'views/hr.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_dashboard/static/src/components/**/*.js',
            'hr_dashboard/static/src/components/**/*.xml'
        ]},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}