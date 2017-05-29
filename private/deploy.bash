pushd aurelia_gbs/place_stories_client
au build
cp -a ./scripts ../server/place_stories_server/static/aurelia/
cp ./index.html ../server/place_stories_server/static/aurelia/
cp -a ./locales ../server/place_stories_server/static/aurelia/
popd
