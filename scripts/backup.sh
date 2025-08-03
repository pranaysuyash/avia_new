#!/bin/bash

# Video NER Application Backup Script
# This script performs automated backups of PostgreSQL database and uploaded files

set -e

# Configuration
BACKUP_DIR="/backups"
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-transcription_app}"
DB_USER="${POSTGRES_USER:-transcription_user}"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}/database"
mkdir -p "${BACKUP_DIR}/uploads"
mkdir -p "${BACKUP_DIR}/logs"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/logs/backup_${TIMESTAMP}.log"
}

# Function to check disk space
check_disk_space() {
    local required_space=$1
    local available_space=$(df -BG "${BACKUP_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [ "$available_space" -lt "$required_space" ]; then
        log "ERROR: Insufficient disk space. Required: ${required_space}GB, Available: ${available_space}GB"
        exit 1
    fi
}

# Function to perform database backup
backup_database() {
    log "Starting database backup..."
    
    # Check database size
    db_size=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT pg_database_size('${DB_NAME}')/(1024*1024*1024) as size_gb;")
    db_size_int=$(echo "$db_size" | awk '{print int($1+0.5)}')
    
    # Check disk space (require 2x database size)
    check_disk_space $((db_size_int * 2))
    
    # Perform backup
    backup_file="${BACKUP_DIR}/database/db_backup_${TIMESTAMP}.sql.gz"
    
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        --file="${backup_file}.tmp"
    
    # Verify backup
    if [ -f "${backup_file}.tmp" ]; then
        mv "${backup_file}.tmp" "${backup_file}"
        backup_size=$(du -h "${backup_file}" | cut -f1)
        log "Database backup completed successfully. Size: ${backup_size}"
        
        # Create checksum
        sha256sum "${backup_file}" > "${backup_file}.sha256"
    else
        log "ERROR: Database backup failed"
        exit 1
    fi
}

# Function to backup uploaded files
backup_uploads() {
    log "Starting uploads backup..."
    
    if [ -d "/app/uploads" ]; then
        uploads_file="${BACKUP_DIR}/uploads/uploads_${TIMESTAMP}.tar.gz"
        
        # Create compressed archive
        tar -czf "${uploads_file}.tmp" -C /app uploads/
        
        if [ -f "${uploads_file}.tmp" ]; then
            mv "${uploads_file}.tmp" "${uploads_file}"
            uploads_size=$(du -h "${uploads_file}" | cut -f1)
            log "Uploads backup completed successfully. Size: ${uploads_size}"
            
            # Create checksum
            sha256sum "${uploads_file}" > "${uploads_file}.sha256"
        else
            log "ERROR: Uploads backup failed"
            exit 1
        fi
    else
        log "Warning: Uploads directory not found"
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Remove database backups older than retention period
    find "${BACKUP_DIR}/database" -name "db_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}/database" -name "*.sha256" -mtime +${RETENTION_DAYS} -delete
    
    # Remove uploads backups older than retention period
    find "${BACKUP_DIR}/uploads" -name "uploads_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}/uploads" -name "*.sha256" -mtime +${RETENTION_DAYS} -delete
    
    # Remove old log files
    find "${BACKUP_DIR}/logs" -name "backup_*.log" -mtime +${RETENTION_DAYS} -delete
    
    log "Cleanup completed"
}

# Function to sync to cloud storage (optional)
sync_to_cloud() {
    if [ -n "${AWS_S3_BUCKET}" ]; then
        log "Syncing to S3..."
        aws s3 sync "${BACKUP_DIR}" "s3://${AWS_S3_BUCKET}/backups/" \
            --exclude "*.tmp" \
            --storage-class GLACIER_IR
        log "S3 sync completed"
    fi
    
    if [ -n "${GCS_BUCKET}" ]; then
        log "Syncing to Google Cloud Storage..."
        gsutil -m rsync -r "${BACKUP_DIR}" "gs://${GCS_BUCKET}/backups/"
        log "GCS sync completed"
    fi
}

# Function to send notification
send_notification() {
    local status=$1
    local message=$2
    
    if [ -n "${SLACK_WEBHOOK_URL}" ]; then
        curl -X POST "${SLACK_WEBHOOK_URL}" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"Backup ${status}: ${message}\"}"
    fi
}

# Main backup process
main() {
    log "=== Starting backup process ==="
    
    # Set error trap
    trap 'send_notification "FAILED" "Backup failed at $(date)"; exit 1' ERR
    
    # Perform backups
    backup_database
    backup_uploads
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Sync to cloud (if configured)
    sync_to_cloud
    
    # Calculate total backup size
    total_size=$(du -sh "${BACKUP_DIR}" | cut -f1)
    
    log "=== Backup process completed successfully ==="
    log "Total backup size: ${total_size}"
    
    # Send success notification
    send_notification "SUCCESS" "Backup completed. Size: ${total_size}"
}

# Run main function
main

# Add to crontab for daily backups at 3 AM:
# 0 3 * * * /backup.sh >> /var/log/backup.log 2>&1