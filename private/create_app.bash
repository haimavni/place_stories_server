#!/bin/bash

echo CREATE NEW APP

app_name=$1
ver=$2
email=$3
password=$4
first=$5
last=$6
if [ -z "$ver" ]
then
    ver="master"
fi
if [ -z "$email" ]
then
    args=""
else
    if [ -z "$first" ]
    then
        first_name="Admin"
    else
        first_name="$first"
    fi
    if [ -z "$last" ]
    then
        last_name="Admin"
    else
        last_name="$last"
    fi
    args="/$email/$password/$first_name/$last_name"
    server="tol_server_$ver"
fi
###----------------------temporary. for local only!-------------------
###server="gbs__www"
###cd /home/haim/aurelia-gbs/server/web2py
###python web2py.py -S $app_name/init_app/init_database$args
###exit
###-------------------------------end local---------------------------
#uncomment below when ready
#server="tol_server_www"

#create database
sudo -u postgres createdb $app_name
#create photos and other resources folder
cp -a /gb_photos/tolbase /gb_photos/$app_name
chown -R www-data:www-data /gb_photos/$app_name

#create link to make the app accessible
cd /home/www-data/web2py/applications
ln --symbolic -T ../../$server $app_name
cd ..

#init the database. create owners account with all privileges
python web2py.py -S $app_name/init_app/init_database$args

#load help messages
python web2py.py -S $app_name/help/load_help_messages_from_csv

#update scheduler service
python /home/www-data/$server/private/add_app_to_scheduler.py $app_name
systemctl restart web2py-scheduler.service
systemctl daemon-reload

