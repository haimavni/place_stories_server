#!/bin/bash

HOST="lifestone.net"
echo host is ${HOST}
TARGET=$1
case $1 in
    test)
        BRANCH="test"
        ;;
    
    www)
        BRANCH="www"
        ;;

    push_state)
        BRANCH="push_state"
        TARGET="master"
        ;;

    *)
        BRANCH="master"
        ;;
esac

echo -e "Deploy to branch " $BRANCH
echo -e "Deploy to branch " $BRANCH >> ~/log/deploy_history.log

pushd ~/client_src
cp index-public.html index.html
git pull
git checkout $BRANCH
git pull

rm -R -f scripts/*
rm -R -f ~/deployment_folder/*

python ~/server_src/private/handle_locale.py $2
cp ./index.html ./index-orig.html
au build --env tmp_env
### rm aurelia_project/environments/tmp_env.ts
cp ./index.html ~/deployment_folder/
cp -a ./scripts ~/deployment_folder/
cp ./index-orig.html ./index.html
rm ./index-orig.html
ls -l ~/deployment_folder/scripts >> ~/log/deploy_history.log
git br -v >> ~/log/deploy_history.log
python ~/server_src/private/fix_index_html.py $1
cp ./favicon.ico  ~/deployment_folder
### git checkout master until merge with master

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
