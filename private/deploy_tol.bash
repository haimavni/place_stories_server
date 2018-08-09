#!/bin/bash

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
    BRANCH1=$BRANCH
fi

echo -e "Deploy to branch " $BRANCH
echo -d "Front branch is " $BRANCH1
echo -e "Deploy to branch " $BRANCH >> ~/log/deploy_history.log
echo -d "Front branch is " $BRANCH1 >> ~/log/deploy_history.log

pushd ~/aurelia-gbs/gbs
git pull
git checkout $BRANCH1
git pull

##git checkout $BRNACH
cp index.html index-orig.html
rm -R -f scripts/*
rm -R -f ~/deployment_folder/*
au build --env prod
python ~/aurelia-gbs/server/tol_server/private/save_curr_version.py
cp -a ./scripts ~/deployment_folder/
ls -l ~/deployment_folder/scripts >> ~/log/deploy_history.log
git br -v >> ~/log/deploy_history.log

cp ./index.html  ~/deployment_folder
cp ./favicon.ico  ~/deployment_folder
cp -a ./images ~/deployment_folder
cp index-orig.html index.html
rm index-orig.html
git checkout master

echo "
lcd /home/haim/deployment_folder
cd /home/www-data/tol_server_${BRANCH}/static
rename aurelia aurelia_prev
mkdir aurelia
cd aurelia
put -R *
rm curr_version.txt
rename curr_version.tmp curr_version.txt
" > ../server/tol_server/private/deploy.batch

ssh gbstories.org rm -R -f /home/www-data/tol_server_${BRANCH}/static/aurelia_prev/*
sftp -b ../server/tol_server/private/deploy.batch gbstories.org

ssh root@gbstories.org bash /home/www-data/tol_server_${BRANCH}/private/update_${BRANCH}.bash
rm ../server/tol_server/private/deploy.batch

popd
