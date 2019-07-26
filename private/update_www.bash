cd /home/www-data/tol_server_www
git pull
bash ./private/restart_servers.bash
cd /home/www-data/tol_server_www/static/aurelia
mv curr_version.tmp curr_version.txt