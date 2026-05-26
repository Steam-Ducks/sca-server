#!/usr/bin/env bash
# =============================================================================
# scripts/db_restore.sh
#
# Restaura um backup PostgreSQL (.dump) para o banco de destino.
#
# Uso:
#   chmod +x scripts/db_restore.sh
#   source .env && ./scripts/db_restore.sh /caminho/para/sca_backup_20260525_030000.dump
#
# ATENÇÃO: o restore apaga e recria todos os objetos do banco.
# Execute apenas com autorização explícita da equipe.
#
# Opções de segurança:
#   CONFIRM_RESTORE=yes  — necessário para evitar restore acidental
# =============================================================================

set -euo pipefail

# ─── Validação de argumento ───────────────────────────────────────────────────

BACKUP_FILE="${1:-}"
if [[ -z "$BACKUP_FILE" ]]; then
  echo "Uso: source .env && ./scripts/db_restore.sh <arquivo.dump>"
  echo ""
  echo "Backups disponíveis em /home/deploy/backups/:"
  ls -lh /home/deploy/backups/sca_backup_*.dump 2>/dev/null | tail -10 || echo "  (nenhum encontrado)"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "ERRO: arquivo não encontrado: $BACKUP_FILE"
  exit 1
fi

# ─── Validação de variáveis ───────────────────────────────────────────────────

for var in DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERRO: variável de ambiente '$var' não definida."
    exit 1
  fi
done

# ─── Confirmação explícita ────────────────────────────────────────────────────

if [[ "${CONFIRM_RESTORE:-}" != "yes" ]]; then
  echo "========================================================"
  echo "  ATENÇÃO: RESTORE DESTRUTIVO"
  echo "========================================================"
  echo ""
  echo "  Banco de destino: $DB_NAME @ $DB_HOST:$DB_PORT"
  echo "  Arquivo de restore: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"
  echo ""
  echo "  Esta operação APAGA e RECRIA todos os objetos do banco."
  echo ""
  echo "  Para confirmar, execute:"
  echo "  CONFIRM_RESTORE=yes source .env && ./scripts/db_restore.sh $BACKUP_FILE"
  echo ""
  exit 1
fi

# ─── Restore ──────────────────────────────────────────────────────────────────

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando restore..."
echo "  Fonte: $BACKUP_FILE"
echo "  Destino: $DB_NAME @ $DB_HOST:$DB_PORT"

PGPASSWORD="$DB_PASSWORD" PGSSLMODE="${DB_SSL_MODE:-require}" pg_restore \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --no-password \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --verbose \
  "$BACKUP_FILE"

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restore concluído com sucesso."
echo ""
echo "Próximos passos recomendados:"
echo "  1. Verifique a integridade: python manage.py check"
echo "  2. Confirme migrations: python manage.py showmigrations"
echo "  3. Rode smoke tests: k6 run k6/scenarios/smoke.js"
