#!/bin/bash

app_name=$1
email=$2
password=$3
if [ -z "$2" ]
then
    vars=""
else
    vars="?email=$email&password=$password"
fi
echo vars is $vars
server="tol_server_dev"
#uncomment below when ready
#server=tol_server_www
#create database
sudo -u postgres createdb $app_name
#create photos and other resources folder
cp -a /gb_photos/tolbase /gb_photos/$app_name
chown -R www-data:www-data /gb_photos/$app_name
#create link to make the app accessible
ln --symbolic -T /home/www-data/$server /home/www-data/web2py/applications/$app_name
#add the new app to the scheduler
#to do
#init the database. create owners account with all privileges
python /home/www-data/web2py/web2py.py -S $app_name/init_app/init_database$vars

