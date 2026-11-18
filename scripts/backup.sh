#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/opt/video-automation/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ENV_FILE="/opt/video-automation/.env"

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

echo "[$(date)] Starting backup..."

# Source env safely
if [ -f "${ENV_FILE}" ]; then
    set -a
    source "${ENV_FILE}"
    set +a
else
    echo "ERROR: .env file missing at ${ENV_FILE}" >&2
    exit 1
fi

# 1. Backup PostgreSQL database if container is running
if docker ps --format '{{.Names}}' | grep -q "^automation-postgres$"; then
    echo "[$(date)] Dumping PostgreSQL database '${POSTGRES_DB}'..."
    docker exec automation-postgres pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/postgres_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
    echo "[$(date)] Database dump completed: ${BACKUP_DIR}/postgres_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
else
    echo "[$(date)] PostgreSQL container not running. Skipping DB dump."
fi

# 2. Backup .env and compose configuration
echo "[$(date)] Backing up configuration files..."
tar -czf "${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz" -C /opt/video-automation .env docker-compose.yml
chmod 600 "${BACKUP_DIR}"/*

# 3. Retain last 14 days of backups
find "${BACKUP_DIR}" -type f -name "*.tar.gz" -mtime +14 -delete
find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +14 -delete

echo "[$(date)] Backup completed successfully."
