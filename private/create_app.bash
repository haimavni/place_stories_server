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
        first="Admin"
    fi
    if [ -z "$last" ]
    then
        last="Admin"
    fi
    args="/$email/$password/$first/$last"
    server="tol_$ver"
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
cp -a /apps_data/tolbase /apps_data/$app_name
chown -R www-data:www-data /apps_data/$app_name

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
echo daemon reload
systemctl daemon-reload
echo restart scheduler

#create app version of index.html
python /home/www-data/$server/private/create_all_app_indexes.py $app_name

##todo: it hangs! systemctl restart web2py-scheduler.service
echo finished creation of $app_name
