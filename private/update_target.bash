cd /home/www-data/tol_$1
rm logs/apply-fixes*.lock>&/dev/null
git pull
python ./private/create_all_app_indexes.py
bash ./private/restart_servers.bash
cd /apps_data
find . | grep logs/apply-fixes | grep .lock | xargs rm
cd /home/www-data/tol_$1/static/aurelia
mv -f curr_version.tmp curr_version.txt
