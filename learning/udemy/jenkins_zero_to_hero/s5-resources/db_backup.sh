#/bin/bash

set -eu

# --- usage | IO ---

if [ $# -eq 0 ]; then
    echo "Usage: ./backup_db.sh <db_host> <db_name> <db_passwd>"
    exit 1
fi

# --- variables ---

# SQL
DB_HOST=$1
DB_NAME=$2
DB_PASSWD=$3

# Backup file
BKP_DATE=$(date -u +%Y-%m-%dT%H%M)
BKP_DIR=/tmp/db_backups
BKP_FILENAME="${DB_NAME}_dump_${BKP_DATE}.sql"
BKP_FILEPATH=$BKP_DIR/$BKP_FILENAME

# AWS
# TODO: need to store secret key somewhere better
AWS_ACCESS_KEY_ID=INSERT_KEY_ID_HERE
AWS_SECRET_ACCESS_KEY=INSERT_SECRET_ACCESS_KEY_HERE
AWS_DEFAULT_REGION=ap-southeast-2
AWS_BUCKET_URI=s3://insert-s3-uri-here
AWS_RESOURCE_PATH=$AWS_BUCKET_URI/$BKP_FILENAME

# --- setup directories ---

[ ! -d $BKP_DIR ] && mkdir $BKP_DIR

# --- run commands ---

dump_sql() {
  mysqldump \
    --column-statistics=0 \
    --host=$DB_HOST \
    --user=root \
    -p$DB_PASSWD \
    $DB_NAME > $BKP_FILEPATH
}

copy_to_s3() {
  aws s3 cp $BKP_FILEPATH $AWS_RESOURCE_PATH
}

dump_sql && copy_to_s3

