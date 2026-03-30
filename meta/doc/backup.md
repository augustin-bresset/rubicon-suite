## Backup

We got the backup file of the current database from Rubicon's server.

This is three files :
* JMS-PDP21_20250502.bak
* JMS-SIS21_20250502.bak
* Pictures.bak

### Restoring the database


#### DOCKER

We need the mssql server to restore the database. Here we use docker to run it easily.

```
docker pull mcr.microsoft.com/mssql/server:2019-latest
```

```
docker run -d   --name sqlsrv   -e "ACCEPT_EULA=Y"   -p 1433:1433   -v /INSERT_PATH/TO/mssql_backups:/var/opt/mssql/backup   mcr.microsoft.com/mssql/server:2019-latest
```

#### RESTORING

Restore file to see what to put where [BACKUP_FILE]:
```
docker exec -it sqlsrv   /opt/mssql-tools18/bin/sqlcmd   -N -C   -S localhost -U SA -P 'Strong@Passw0rd'   -Q "RESTORE FILELISTONLY 
      FROM DISK = '/var/opt/mssql/backup/[BACKUP_FILE].bak';"
```

For PDP

```
docker exec -it sqlsrv /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Strong@Passw0rd' \
  -C \
  -Q "RESTORE DATABASE JMS_PDP21
      FROM DISK = '/var/opt/mssql/backup/JMS-PDP21_20250502.bak'
      WITH MOVE 'JMS_PDP21_Data' TO '/var/opt/mssql/data/JMS_PDP21.mdf',
           MOVE 'JMS_PDP21_Log'  TO '/var/opt/mssql/data/JMS_PDP21_log.ldf';"
```


FOR SIS
```
docker exec -it sqlsrv \
  /opt/mssql-tools18/bin/sqlcmd \
  -N -C \
  -S localhost -U SA -P 'Strong@Passw0rd' \
  -Q "RESTORE DATABASE JMS_SIS21
      FROM DISK = '/var/opt/mssql/backup/JMS-SIS21_20250502.bak'
      WITH 
        MOVE 'SIS_Data' TO '/var/opt/mssql/data/JMS_SIS21.mdf',
        MOVE 'SIS_Log'  TO '/var/opt/mssql/data/JMS_SIS21_log.ldf',
        REPLACE;"

```

For Pictures (manual — see `meta/tutorials/restore_database_picture.md` for the automated pipeline)
```
docker exec -it sqlsrv \
  /opt/mssql-tools18/bin/sqlcmd \
  -N -C \
  -S localhost -U SA -P 'Strong@Passw0rd' \
  -Q "RESTORE DATABASE PICTURES
      FROM DISK = '/var/opt/mssql/backup/Pictures.bak'
      WITH 
        MOVE 'Pictures_Data' TO '/var/opt/mssql/data/Pictures_db.mdf',
        MOVE 'Pictures_Log'  TO '/var/opt/mssql/data/Pictures_db.ldf',
        REPLACE;"
```


### To csv file


Create the table list
```
mkdir -p data/raw
docker exec -i sqlsrv \
  /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Strong@Passw0rd' \
  -d [DATABASE_NAME] -N -C \
  -h -1 -W -s "," \
  -Q "SELECT TABLE_SCHEMA + '.' + TABLE_NAME
      FROM INFORMATION_SCHEMA.TABLES
      WHERE TABLE_TYPE = 'BASE TABLE';" \
  > data/raw/table_list.txt
```


~/rubicon-suite/tools/export.sh
```
#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"      # racine rubicon-suite
LIST_FILE="$BASE_DIR/data/raw/sis_table_list.txt" # <<== HERE CHANGE TO PUT THE GOOD TABLE FILES
OUT_DIR="/var/opt/mssql/backup"                   # volume Docker

# --- Boucle d'export ---
while IFS= read -r full_table || [[ -n "$full_table" ]]; do
  table_name=${full_table#*.}
  echo "→ Export de $full_table vers ${table_name}.csv"

  # On enlève -i pour ne pas pomper le stdin du script
  docker exec sqlsrv /opt/mssql-tools18/bin/bcp \
    "JMS_SIS21.${full_table}" out \ # <<== HERE CHANGE THE NAME OF THE TABLE
    "${OUT_DIR}/${table_name}.csv" \
    -c -t, \
    -S "tcp:localhost,1433;TrustServerCertificate=yes" \
    -U SA -P 'Strong@Passw0rd'
done < "$LIST_FILE"
```