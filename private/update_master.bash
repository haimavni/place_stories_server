cd /home/www-data/tol_server_master
git pull
bash ./private/restart_servers.bash
python private/create_all_app_indexes.py
cd /home/www-data/tol_server_master/static/aurelia
mv -f curr_version.tmp curr_version.txt