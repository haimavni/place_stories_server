cd /home/www-data
chown -R www-data:www-data .
systemctl stop web2py-scheduler-master.service
systemctl stop web2py-scheduler-test.service
systemctl stop web2py-scheduler-www.service
systemctl stop nginx
systemctl stop emperor.uwsgi.service
systemctl start nginx
systemctl start emperor.uwsgi.service
systemctl start web2py-scheduler-master.service
systemctl start web2py-scheduler-test.service
systemctl start web2py-scheduler-www.service
