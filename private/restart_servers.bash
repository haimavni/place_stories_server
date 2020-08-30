cd /home/www-data
chown -R www-data:www-data .
systemctl stop web2py-scheduler.service
systemctl stop nginx
systemctl stop emperor.uwsgi.service
systemctl stop sslmessaging.service
systemctl stop sslmessagingtol.service
systemctl restart memcached
systemctl start sslmessaging.service
systemctl start sslmessagingtol.service
systemctl start nginx
systemctl start emperor.uwsgi.service
systemctl start web2py-scheduler.service

