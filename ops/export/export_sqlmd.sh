#!/usr/bin/env bash
set -e

BASE="$(cd "$(dirname "$0")/.." && pwd)"         # rubicon-suite
LIST="$BASE/mssql_backups/table_list.txt"       # liste des tables existante
OUTDIR="$BASE/mssql_backups"                    # où on stocke les CSV sur l’hôte

while IFS= read -r fullname; do
  tbl="${fullname#*.}"                          # ex: dbo.StoneSettings → StoneSettings
  echo "→ Export de $fullname vers $tbl.csv"
  docker exec -i sqlsrv /opt/mssql-tools18/bin/sqlcmd \
    -C \
    -S "tcp:localhost,1433;TrustServerCertificate=yes" \
    -U SA -P 'Strong@Passw0rd' \
    -s"," -W \
    -Q "SET NOCOUNT ON; SELECT * FROM $fullname" \
  > "$OUTDIR/$tbl.csv"
done < "$LIST"
