#!/bin/bash

echo fix column names

dbname=$1

if [ -z "$dbname" ]
then
    dbname="gbs__master"
fi
echo fix column names for $dbname  

read -p "Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi

sudo -u postgres psql $dbname -f /home/www-data/tol_master/private/fix_column_case.sql
