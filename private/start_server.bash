systemctl restart memcached
systemctl start nginx
systemctl start emperor.uwsgi.service
systemctl start web2py-scheduler.service
