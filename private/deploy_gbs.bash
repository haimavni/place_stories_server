pushd ~/aurelia-gbs/gbs
git pull
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

sftp -b ../server/place_stories_server/private/deploy.batch root@gbstories.org
popd

