cd /home/www-data/tol_server_master
git pull
bash ./private/restart_servers.bash
cd /home/www-data/tol_server_master/static/aurelia
mv curr_version.tmp curr_version.txt