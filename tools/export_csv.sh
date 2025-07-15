#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"      # racine rubicon-suite
LIST_FILE="$BASE_DIR/data/raw/sis_table_list.txt"
OUT_DIR="/var/opt/mssql/backup"                   # volume Docker

# --- Boucle d'export ---
while IFS= read -r full_table || [[ -n "$full_table" ]]; do
  table_name=${full_table#*.}
  echo "→ Export de $full_table vers ${table_name}.csv"

  # On enlève -i pour ne pas pomper le stdin du script
  docker exec sqlsrv /opt/mssql-tools18/bin/bcp \
    "JMS_SIS21.${full_table}" out \
    "${OUT_DIR}/${table_name}.csv" \
    -c -t, \
    -S "tcp:localhost,1433;TrustServerCertificate=yes" \
    -U SA -P 'Strong@Passw0rd'
done < "$LIST_FILE"
