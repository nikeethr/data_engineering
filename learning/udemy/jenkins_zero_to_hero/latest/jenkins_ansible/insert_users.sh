#!/bin/sh

set -eu

USER_INFO_FILE=$1
DB_PASSWD=$2
DB_USER=root
DB_NAME=users_db
DB_TABLE=register

query=$(awk 'BEGIN {
    print "INSERT INTO '$DB_TABLE' (Id, FirstName, LastName, Age) VALUES"
    maxlines = 50
}
{
    cmd = "shuf -i 10-90 -n 1"
    cmd | getline age
    close(cmd)

    if (NR <= maxlines) {
        printf("\\n\\t(%s, %s, %s, %s)", NR, $1, $2, age)
    }
    if (NR < maxlines) { print(",") }
    if (NR == maxlines) { print(";") }
}
END {}' $1)

echo $query

mysql --user=$DB_USER --password=$DB_PASSWD $DB_NAME $query
