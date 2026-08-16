#!/bin/bash

# Backup Script for Daanaa Automation Stack
# Backs up Chatwoot + n8n PostgreSQL databases
# Run daily via cron: 0 2 * * * /home/akbar/meritgiving/scripts/backup_automation_stack.sh

set -e

BACKUP_DIR="/data/automation_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CHATWOOT_BACKUP="${BACKUP_DIR}/chatwoot_${TIMESTAMP}.sql.gz"
N8N_BACKUP="${BACKUP_DIR}/n8n_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "=== Daanaa Automation Stack Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Backup dir: ${BACKUP_DIR}"

# Backup Chatwoot Database
echo "Backing up Chatwoot PostgreSQL..."
docker-compose -f /opt/chatwoot/docker-compose.yml exec -T postgres pg_dump \
  -U postgres \
  -d chatwoot_production \
  | gzip > "${CHATWOOT_BACKUP}"

if [ -f "${CHATWOOT_BACKUP}" ]; then
  CHATWOOT_SIZE=$(du -h "${CHATWOOT_BACKUP}" | cut -f1)
  echo "✅ Chatwoot backup: ${CHATWOOT_BACKUP} (${CHATWOOT_SIZE})"
else
  echo "❌ Chatwoot backup failed"
  exit 1
fi

# Backup n8n Database
echo "Backing up n8n PostgreSQL..."
docker-compose -f /opt/n8n/docker-compose.yml exec -T postgres pg_dump \
  -U n8n \
  -d n8n \
  | gzip > "${N8N_BACKUP}"

if [ -f "${N8N_BACKUP}" ]; then
  N8N_SIZE=$(du -h "${N8N_BACKUP}" | cut -f1)
  echo "✅ n8n backup: ${N8N_BACKUP} (${N8N_SIZE})"
else
  echo "❌ n8n backup failed"
  exit 1
fi

# Clean up old backups (keep last 30 days)
echo "Cleaning up old backups (keeping last ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
OLD_COUNT=$(find "${BACKUP_DIR}" -name "*.sql.gz" | wc -l)
echo "✅ Kept ${OLD_COUNT} backups"

# Log backup completion
echo "Backup completed successfully: $(date)" >> "${BACKUP_DIR}/backup.log"

echo ""
echo "✅ All backups complete"
echo "Total backups: $(ls ${BACKUP_DIR}/*.sql.gz 2>/dev/null | wc -l)"
