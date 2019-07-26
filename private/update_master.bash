cd /home/www-data/tol_server_master
git pull
bash ./private/restart_servers.bash
cd static/aurelia
mv curr_version.tmp curr_version.txt