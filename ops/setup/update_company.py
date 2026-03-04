from odoo import api, SUPERUSER_ID

def update_company_info(env):
    company = env.ref('base.main_company')
    company.write({
        'name': 'Rubicon Co., Ltd.',
        'street': '807-809 Silom-Shanghai bldg., 5/F,',
        'street2': 'Silom 17 road, Bangrak',
        'city': 'Bangkok',
        'zip': '10500',
        'country_id': env.ref('base.th').id,
        'phone': '+66 2236 7043 ext 105',
        'email': 'info@rubicon.co.th',
        'website': 'www.rubicon.co.th',
    })
    
    # Load logo
    import base64
    import os
    logo_path = '/home/smaug/rubicon-suite/rubicon_addons/sis_document/static/src/img/logo.webp'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            company.logo = base64.b64encode(f.read())
    
    print(f"Updated company: {company.name}")

if __name__ == '__main__':
    # This part is for running within odoo shell
    update_company_info(env)
    env.cr.commit()
