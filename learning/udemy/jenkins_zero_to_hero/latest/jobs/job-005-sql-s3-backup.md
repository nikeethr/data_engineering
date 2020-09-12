# mySQL

Install mysql client in Dockerfile

Create database within remote host via mysql client:

```sql
mysql> CREATE DATABASE patient_db;
mysql> USE patient_db;
mysql> CREATE TABLE patient(
    id MEDIUMINT NOT NULL AUTOINCREMENT,
    name VARCHAR(20) NOT NULL,
    gender CHAR(1),
    birth DATE,
    PRIMARY KEY (id)
);
mysql> LOAD DATA LOCAL INFILE '/path/filename.csv' REPLACE
    INTO TABLE table_name
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\r\n'
    (column_name3, column_name5);
```

If you forgot to add id:

```
mysql> ALTER TABLE table_name
mysql> ADD COLUMN id AUTOINCREMENT PRIMARY KEY FIRST;
```

# Create S3 bucket

**AWS Console -> S3 -> create bucket**


# Configure Secrets

**Security -> Manage Credentials -> Add Credentials -> Secret Text**


# Job

**Build Environment -> Use secrete text(s) or file(s)**

```sh
[Secret Text]
Variable = AWS_ACCESS_KEY_ID
Credentials -> Specific credentials = AWS_ACCESS_KEY_ID

[Secret Text]
Variable = AWS_SECRET_ACCESS_KEY
Credentials -> Specific credentials = AWS_SECRET_ACCESS_KEY

[Secret Text]
Variable = DB_PASSWD
Credentials -> Specific credentials = DB_PASSWD
```

**Build -> Execute shell script on rmemote host using SSH**

Execute on remote host

```sh
env \
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
DB_PASSWD=$DB_PASSWD \
/tmp/scripts/backup_db.sh $DB_HOST $DB_NAME
```
