#!/bin/bash
# backup.sh

# Variables de conexión (Render te da el DATABASE_URL en el dashboard)
DATABASE_URL="postgres://lubricantes_db_30om_user:tYAyUQvsOstVozG1LJdq6qK79tDS4Rkq@host:5432/lubricantes_db_30om"
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

mkdir -p $BACKUP_DIR

# Crear backup
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$TIMESTAMP.sql

# (Opcional) Subirlo a un bucket S3 / GCS
# aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql s3://mi-bucket/backups/
