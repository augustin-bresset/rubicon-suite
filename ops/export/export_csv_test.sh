#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"      # Rubicon-suite root
LIST_FILE="$BASE_DIR/data/raw/sis_table_list.txt"
OUT_DIR="/var/opt/mssql/backup"                   # Docker Volum

# --- Export Loop ---
while IFS= read -r full_table || [[ -n "$full_table" ]]; do
  table_name=${full_table#*.}
  echo "→ Export de $full_table vers ${table_name}.csv"

  # We take out -i to not consume the stdin of the script
  docker exec sqlsrv /opt/mssql-tools18/bin/bcp \
    "JMS_SIS21.${full_table}" out \
    "${OUT_DIR}/${table_name}.csv" \
    -c -t";" \
    -S "tcp:localhost,1433;TrustServerCertificate=yes" \
    -U SA -P 'Strong@Passw0rd'
done < "$LIST_FILE"
