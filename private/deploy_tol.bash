#!/bin/bash

HOST="haimavni.site"
echo host is ${HOST}
if [ "$1" == "master3" ]
then
    BRANCH="master3"
else 
    if [ "$1" == "test3" ]
    then
        BRANCH="test3"
    else 
        if [ "$1" == "www3" ]
        then
            BRANCH="www3"
        else
            if [ "$1" == "flex" ]
            then
                BRANCH1="flex"
                BRANCH="master"
            fi
        fi
    fi
fi
if [ "$BRANCH1" == "0" ]
then
    BRANCH1=${BRANCH}
    echo branch1 is ${BRANCH1} -- $BRANCH1
fi

if [ -z "$2" ]
then
    TARGET=$BRANCH
else
    TARGET=$2
fi

echo -e "Deploy to branch " $BRANCH
echo -d "Front branch is " $BRANCH1
echo -e "Deploy to branch " $BRANCH >> ~/log/deploy_history.log
echo -d "Front branch is " $BRANCH1 >> ~/log/deploy_history.log

pushd ~/aurelia
git pull
git checkout $BRANCH1
git pull

##git checkout $BRNACH
cp index.html index-orig.html
rm -R -f scripts/*
rm -R -f ~/deployment_folder/*

python ~/tol3/private/handle_locale.py
au build --env tmp_env
rm aurelia_project/environments/tmp_env.ts
cp -a ./scripts ~/deployment_folder/
ls -l ~/deployment_folder/scripts >> ~/log/deploy_history.log
git br -v >> ~/log/deploy_history.log
python ~/tol3/private/fix_index_html.py
cp ./index.html  ~/deployment_folder
cp ./favicon.ico  ~/deployment_folder
cp -a ./images ~/deployment_folder
cp index-orig.html index.html
rm index-orig.html
git checkout master3

echo "
lcd /home/haim/deployment_folder
cd /home/www-data/tol_server_${TARGET}/static
rename aurelia aurelia_prev
mkdir aurelia
cd aurelia
put -R *
" > ~/tol3/private/deploy.batch
ssh root@${HOST} rm -R -f /home/www-data/tol_server_${TARGET}/static/aurelia_prev/*
sftp -b ~/tol3/private/deploy.batch root@${HOST}
ssh root@${HOST} cp -r /apps_data/fontawesome /home/www-data/tol_server_${TARGET}/static/aurelia/

#version file is uploaded last to prevent immature updates for users
echo "
lcd /home/haim/
cd /home/www-data/tol_server_${TARGET}/static/aurelia
put curr_version.tmp
" > ~/tol3/private/deploy1.batch
sftp -b ~/tol3/private/deploy1.batch root@${HOST}

ssh root@${HOST} bash /home/www-data/tol_server_${TARGET}/private/update_target.bash $TARGET
rm ~/tol3/private/deploy1.batch
rm ~/tol3/private/deploy.batch
###au build --env dev
popd
