#!/bin/bash

echo Fix column names
echo ----------------
echo #
declare -a dbnames=("crossing" "gbs__test" "k_aza" "kavigdor" "rishpon")

for dbname in "${dbnames[@]}"
do
    echo fix column names for $dbname
    read -p "Are you sure? " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        sudo -u postgres psql $dbname < /home/www-data/tol_master/private/fix_column_case.sql 
    fi
    echo #
done


