cd /home/www-data/tol_$1
rm logs/apply-fixes*.lock>&/dev/null
git pull
# python ./private/create_all_app_indexes.py
bash ./private/restart_servers.bash
cd /home/www-data/tol_$1/static/aurelia
mv -f curr_version.tmp curr_version.txt
echo finished