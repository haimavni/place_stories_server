pushd ~/aurelia-gbs/place_stories_client
au build
echo Copy client files
cp -a ./scripts ../server/place_stories_server/static/aurelia/
cp ./index.html ../server/place_stories_server/static/aurelia/
cp ./favicon.ico ../server/place_stories_server/static/aurelia/
cp -a ./locales ../server/place_stories_server/static/aurelia/
cp -a ./images ../server/place_stories_server/static/aurelia/
echo Finished copying
popd
