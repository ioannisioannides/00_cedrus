#!/bin/bash
# ==============================================================================
# POSTGRESQL AUTOMATED BACKUP SCRIPT
# ==============================================================================
# Self-hosted database backup solution
# Retention: 30 days by default
# 
# Built by: Dr. Thomas Berg (Caltech PhD, DevOps, 23 years)
# ==============================================================================

set -e

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
mkdir -p ${BACKUP_DIR}

# Perform backup
echo "[INFO] Starting database backup..."
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h postgres \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    | gzip > ${BACKUP_FILE}

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Backup completed successfully!"
    echo "[INFO] Backup size: $(du -h ${BACKUP_FILE} | cut -f1)"
else
    echo "[ERROR] Backup failed!"
    exit 1
fi

# Remove old backups (retention policy)
echo "[INFO] Cleaning up old backups (keeping last ${RETENTION_DAYS} days)..."
find ${BACKUP_DIR} -name "cedrus_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# List current backups
echo "[INFO] Current backups:"
ls -lh ${BACKUP_DIR}/cedrus_backup_*.sql.gz 2>/dev/null || echo "No backups found"

# Backup statistics
BACKUP_COUNT=$(ls -1 ${BACKUP_DIR}/cedrus_backup_*.sql.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh ${BACKUP_DIR} | cut -f1)

echo "======================================================================"
echo "Backup Summary:"
echo "- Total backups: ${BACKUP_COUNT}"
echo "- Total size: ${TOTAL_SIZE}"
echo "- Latest backup: ${BACKUP_FILE}"
echo "======================================================================"

# Optional: Send notification (implement as needed)
# Example: curl -X POST https://your-monitoring-endpoint/backup-success

exit 0
