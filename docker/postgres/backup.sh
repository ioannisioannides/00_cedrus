#!/bin/bash
# ==============================================================================
# POSTGRESQL AUTOMATED BACKUP SCRIPT
# ==============================================================================
# Self-hosted database backup solution
# Retention: 30 days by default
# 
# Built by: Dr. Thomas Berg (Caltech PhD, DevOps, 23 years)
# ==============================================================================

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
BACKUP_FILE="${BACKUP_DIR}/cedrus_backup_${TIMESTAMP}.sql.gz"

echo "======================================================================"
echo "Cedrus PostgreSQL Backup Script"
echo "======================================================================"
echo "Timestamp: $(date)"
echo "Database: ${POSTGRES_DB}"
echo "Backup file: ${BACKUP_FILE}"
echo "Retention: ${RETENTION_DAYS} days"
echo "======================================================================"

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

# Perform backup
echo "[INFO] Starting database backup..."
if PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h postgres \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    | gzip > "${BACKUP_FILE}"; then
    echo "[SUCCESS] Backup completed successfully!"
    echo "[INFO] Backup size: $(du -h "${BACKUP_FILE}" | cut -f1)"
else
    echo "[ERROR] Backup failed!"
    exit 1
fi

# Remove old backups (retention policy)
echo "[INFO] Cleaning up old backups (keeping last ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name 'cedrus_backup_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete

# List current backups
echo "[INFO] Current backups:"
if ! find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'cedrus_backup_*.sql.gz' -ls 2>/dev/null; then
    echo "No backups found"
fi

# Backup statistics
BACKUP_COUNT=$(find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'cedrus_backup_*.sql.gz' | wc -l || true)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)

echo "======================================================================"
echo "Backup Summary:"
echo "- Total backups: ${BACKUP_COUNT}"
echo "- Total size: ${TOTAL_SIZE}"
echo "- Latest backup: ${BACKUP_FILE}"
echo "======================================================================"

# Optional: Send notification (implement as needed)
# Example: curl -X POST https://your-monitoring-endpoint/backup-success

exit 0
