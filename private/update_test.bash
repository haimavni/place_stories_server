cd /home/www-data/tol_server_test
git pull
python ./private/create_all_app_indexes.py
bash ./private/restart_servers.bash
cd /home/www-data/tol_server_test/static/aurelia
mv -f curr_version.tmp curr_version.txt