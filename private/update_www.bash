cd /home/www-data/tol_www
git pull
python ./private/create_all_app_indexes.py
bash ./private/restart_servers.bash
cd /home/www-data/tol_www/static/aurelia
mv -f curr_version.tmp curr_version.txt