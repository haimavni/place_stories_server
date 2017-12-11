#!/bin/bash

d=$(date +%Y-%m-%d)
echo arg=$1
if [ -z "$1" ]
then
    dbname="gbs_www"
else
    dbname=$1
fi

echo $d

sudo -u postgres pg_dump $dbname > $dbname.$d.bkp