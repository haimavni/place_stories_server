#!/bin/bash

HOST="lifestone.net"
echo host is ${HOST}
if [ "$1" == "master" ]
then
    BRANCH="master"
else 
    if [ "$1" == "test" ]
    then
        BRANCH="test"
    else 
        if [ "$1" == "www" ]
        then
            BRANCH="www"
        fi
    fi
fi
TARGET=$BRANCH

echo -e "Deploy to branch " $BRANCH
echo -e "Deploy to branch " $BRANCH >> ~/log/deploy_history.log

pushd ~/aurelia
git pull
git checkout $BRANCH
git pull
cp index.html index-orig.html

rm -R -f scripts/*
rm -R -f ~/deployment_folder/*

python ~/server_src/private/handle_locale.py
au build --env tmp_env
rm aurelia_project/environments/tmp_env.ts
cp -a ./scripts ~/deployment_folder/
ls -l ~/deployment_folder/scripts >> ~/log/deploy_history.log
git br -v >> ~/log/deploy_history.log
python ~/server_src/private/fix_index_html.py
cp ./index.html  ~/deployment_folder
cp ./favicon.ico  ~/deployment_folder
#cp -a ./images ~/deployment_folder
cp index-orig.html index.html
rm index-orig.html
git checkout master

echo "
lcd /home/haim/deployment_folder
cd /home/www-data/tol_${TARGET}/static
rename aurelia aurelia-prev
mkdir aurelia
cd aurelia
ln -s ../fontawesome ./fontawesome
put -R *
" > ~/deployment_folder/deploy.batch
ssh root@${HOST} rm -R -f /home/www-data/tol_${TARGET}/static/aurelia-prev/*
echo sftp -b ~/deployment_folder/deploy.batch root@${HOST}
sftp -b ~/deployment_folder/deploy.batch root@${HOST}
#ssh root@${HOST} cp -r /apps_data/fontawesome /home/www-data/tol_${TARGET}/static/aurelia/

#version file is uploaded last to prevent immature updates for users
echo "
lcd /home/haim/
cd /home/www-data/tol_${TARGET}/static/aurelia
put curr_version.tmp
" > ~/deployment_folder/deploy1.batch
echo sftp -b ~/deployment_folder/deploy1.batch root@${HOST}
sftp -b ~/deployment_folder/deploy1.batch root@${HOST}
echo ssh root@${HOST} bash /home/www-data/tol_${TARGET}/private/update_target.bash $TARGET
ssh root@${HOST} bash /home/www-data/tol_${TARGET}/private/update_target.bash $TARGET
popd
echo Done
