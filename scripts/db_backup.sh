#!/usr/bin/env bash
# =============================================================================
# scripts/db_backup.sh
#
# Backup manual do PostgreSQL de produção (DigitalOcean Managed).
# Pode ser chamado diretamente no servidor ou via pipeline.
#
# Uso:
#   chmod +x scripts/db_backup.sh
#   source .env && ./scripts/db_backup.sh
#
# Variáveis de ambiente esperadas (do .env):
#   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_SSL_MODE
#
# Variáveis opcionais para upload ao Spaces:
#   DO_SPACES_KEY, DO_SPACES_SECRET, DO_SPACES_BUCKET, DO_SPACES_REGION
#
# Saída:
#   /home/deploy/backups/sca_backup_YYYYMMDD_HHMMSS.dump (localmente)
#   s3://BUCKET/backups/YYYY/MM/sca_backup_*.dump (se Spaces configurado)
# =============================================================================

set -euo pipefail

# ─── Configuração ─────────────────────────────────────────────────────────────

BACKUP_DIR="${BACKUP_DIR:-/home/deploy/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sca_backup_${TIMESTAMP}.dump"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# ─── Validação ────────────────────────────────────────────────────────────────

for var in DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERRO: variável de ambiente '$var' não definida."
    echo "Execute: source .env && ./scripts/db_backup.sh"
    exit 1
  fi
done

# ─── Backup ───────────────────────────────────────────────────────────────────

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup do banco: $DB_NAME"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Destino local: $BACKUP_FILE"

PGPASSWORD="$DB_PASSWORD" PGSSLMODE="${DB_SSL_MODE:-require}" pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --format=custom \
  --no-password \
  --file="$BACKUP_FILE"

BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup concluído: $BACKUP_SIZE"

# ─── Upload para DigitalOcean Spaces (opcional) ───────────────────────────────

if [[ -n "${DO_SPACES_KEY:-}" && -n "${DO_SPACES_SECRET:-}" && -n "${DO_SPACES_BUCKET:-}" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Enviando para Spaces..."

  YEAR=$(date +%Y)
  MONTH=$(date +%m)
  DEST="s3://${DO_SPACES_BUCKET}/backups/${YEAR}/${MONTH}/sca_backup_${TIMESTAMP}.dump"

  s3cmd put "$BACKUP_FILE" "$DEST" \
    --access_key="$DO_SPACES_KEY" \
    --secret_key="$DO_SPACES_SECRET" \
    --host="${DO_SPACES_REGION:-nyc3}.digitaloceanspaces.com" \
    --host-bucket="%(bucket)s.${DO_SPACES_REGION:-nyc3}.digitaloceanspaces.com" \
    --acl-private \
    --no-progress

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upload concluído: $DEST"
else
  echo "[INFO] Spaces não configurado — backup apenas local."
fi

# ─── Limpeza de backups antigos locais ────────────────────────────────────────

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Removendo backups locais com mais de ${RETENTION_DAYS} dias..."
find "$BACKUP_DIR" -name "sca_backup_*.dump" -mtime "+${RETENTION_DAYS}" -delete

REMAINING=$(find "$BACKUP_DIR" -name "sca_backup_*.dump" | wc -l)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backups locais restantes: $REMAINING"

echo ""
echo "=== Backup finalizado com sucesso ==="
echo "  Arquivo: $BACKUP_FILE ($BACKUP_SIZE)"
