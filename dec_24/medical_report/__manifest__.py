{
    'name': 'Hospital Management',
    'version': '18.0.1.0.0',
    'summary' : 'Hospital Management Module',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'license': 'LGPL-3',
    # 'depends': ['sale', 'base', 'hr'],

    'data':[
        'security/ir.model.access.csv',
        'views/menu.xml',
        'report/medical_report_template.xml',
        'report/medical_report.xml',
    ],

    'installable': True,
    'auto_install': False,
}