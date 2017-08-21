cd /home/www-data/tol_server_${$1}
git pull
chown -R www-data:www-data .
sudo systemctl stop web2py-scheduler-${$1}.service
sudo systemctl stop nginx
sudo systemctl stop emperor.uwsgi.service
sudo systemctl start nginx
sudo systemctl start emperor.uwsgi.service
sudo systemctl start web2py-scheduler-${$1}.service
