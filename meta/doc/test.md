# Tests

The CRUD modules are not tested because no logic is needed (pdp_stone, pdp_metal, ...)


## Testing modules 

In each modules a **tests** folder will be found. It contains the tests.

You can launch those test by launching 
```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  -u [INSERT_MODULE_NAME] \
  --stop-after-init \
  --test-enable
```

### Errors handling

1.Port 8069 is in use by another program.

It happens when odoo is already in use, you can add *--no-http* to the command before such as below 

```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  -u [INSERT_MODULE_NAME] \
  --stop-after-init \
  --test-enable \
  --no-http
```

Or choosing an other port with *--http-port=xxx* such as below :
```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  -u [INSERT_MODULE_NAME] \
  --stop-after-init \
  --test-enable \
  --http-port=8070
```

```sh
docker compose exec -T odoo \
  odoo -d rubicon \
  --stop-after-init \
  --test-enable \
  --test-tags=/rubicon_env \
  --http-port=8070
```



docker compose exec -T odoo \
  odoo -d rubicon \
  -u pdp_price \
  --stop-after-init \
  --test-enable \
  --http-port=8070