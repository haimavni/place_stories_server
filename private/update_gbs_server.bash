cd /home/www-data/place_stories_server
git pull
chown -R www-data:www-data .
systemctl stop web2py-scheduler.service
systemctl stop nginx
systemctl stop emperor.uwsgi.service
systemctl start nginx
systemctl start emperor.uwsgi.service
systemctl start web2py-scheduler.service
