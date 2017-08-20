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
            BRANCH="0"
        fi
    fi
fi
if [ "$BRANCH" == "0" ]
then
    echo -e "Branch to deploy: \c "
    read BRANCH
    printf "\n"
fi

echo -e "Deploy to branch " $BRANCH

pushd ~/aurelia-gbs/gbs
git pull
##git checkout $BRNACH
cp index.html index-orig.html
rm -R -f scripts/*
au build --env prod
rm -R -f ~/deployment_folder/*
cp -a ./scripts ~/deployment_folder/
cp ./index.html  ~/deployment_folder
cp ./favicon.ico  ~/deployment_folder
cp -a ./locales  ~/deployment_folder
cp -a ./froala-style ~/deployment_folder
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
" > ../server/place_stories_server/private/deploy.batch

ssh root@gbstories.org rm -R -f /home/www-data/tol_server_${BRANCH}/static/aurelia_prev/*
sftp -b ../server/tol_server_${BRANCH}/private/deploy.batch root@gbstories.org

ssh root@gbstories.org bash /home/www-data/tol_server_${BRANCH}/private/update_gbs_server.bash ${BRANCH}
rm deploy.batch

popd