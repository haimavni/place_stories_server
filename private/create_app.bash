#!/bin/bash

app_name=$1
ver=$2
email=$3
password=$4
if [-z "$ver"]
then
    ver="master"
fi
if [ -z "$email" ]
then
    vars=""
else
    vars="?email=$email&password=$password"
    server="tol_server_$ver"
fi
echo vars is $vars
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
#add the new app to the scheduler
#to do
#init the database. create owners account with all privileges
cd ..
python web2py.py -S $app_name/init_app/init_database$vars
python web2py.py -S $app_name/help/load_help_messages_from_csv
#update scheduler service
python /home/www-data/$server/private/add_app_to_scheduler.py $app_name
systemctl restart web2py-scheduler.service
systemctl daemon-reload

