import json
# env is available in local scope of odoo shell
service = env['pdp.api.service']
data = service.get_full_pdp(11)
print(json.dumps(data, indent=4, default=str))
