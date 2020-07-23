#!/bin/sh

# todo: use .my.cnf to define this.
# [client]
# user = root
# password = XXXX

MYSQL_USER=root
MYSQL_PASSWORD=abcd123
DB_NAME=menagerie

run_mysql() {
    # -h <hostname>: host (not required)
    # -u <user>: user (ideally configured)
    # -p<password>:
    # -Bse: B - batch, s - silent, e - execute
    mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -Bse "$@"
}

