#!/bin/bash
echo 'Requires Ubuntu = 16.04 and installs Nginx + uWSGI + Web2py'
# https://gist.github.com/niphlod/8a13025001363657f0201b2a15dad41c
# Check if user has root privileges
if [[ $EUID -ne 0 ]]; then
   echo "You must run the script as root or using sudo"
   exit 1
fi
# parse env vars
WEB2PY_PASS="${WEB2PY_PASS:-0}"
NOPASSWORD="${NOPASSWORD:-0}"
NOCERTIFICATE="${NOCERTIFICATE:-0}"
WITH_DATABASE="${WITH_DATABASE:-0}"
# parse command line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-password) NOPASSWORD="1"; shift 1;;
    --no-certificate) NOCERTIFICATE="1"; shift 1;;
    --with_database) WITH_DATABASE="1"; shift 1;;
  esac
done

echo "SETTINGS"
if [ "$NOCERTIFICATE" = "0" ]
then
    echo "   generate certificate..........................YES"
else
    echo "   generate certificate..........................NO"
    if [[ -f /etc/nginx/ssl/web2py.key && -f /etc/nginx/ssl/web2py.crt ]]
    then
        echo "ERROR: private key and cert must exist:"
        echo "private key............/etc/nginx/ssl/web2py.key"
        echo "public certificate...../etc/nginx/ssl/web2py.crt"
        exit 1
    fi
fi
if [ "$NOPASSWORD" != "0" ]
then
    echo "   do not set web2py password....................YES"
fi
if [ "$WEB2PY_PASS" != "0" ]
then
    echo "   web2py password...............................set from env"
fi
if [ "$WITH_DATABASE" = "0" ]
then
    echo "   install database..............................NO"
else
    echo "   install database..............................YES"
fi
# Get Web2py Admin Password
if [ "$NOPASSWORD" = "0" ]
then
    if [ "$WEB2PY_PASS" == "0" ]
        then
        echo -e "Web2py Admin Password: \c "
        read  -s WEB2PY_PASS
        printf "\n"
    fi
fi
# Upgrade and install needed software
apt update
apt autoremove
apt autoclean
apt -y install nginx-full
apt -y install build-essential python2.7 python2.7-dev unzip virtualenv
if [ "$WITH_DATABASE" != "0" ]
then
    apt -y install postgresql libpq-dev
fi
# Create common nginx sections
mkdir /etc/nginx/conf.d/web2py
echo '
gzip_static on;
gzip_http_version   1.1;
gzip_proxied        expired no-cache no-store private auth;
gzip_disable        "MSIE [1-6]\.";
gzip_vary           on;
' > /etc/nginx/conf.d/web2py/gzip_static.conf
echo '
gzip on;
gzip_disable "msie6";
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_buffers 16 8k;
gzip_http_version 1.1;
gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;
' > /etc/nginx/conf.d/web2py/gzip.conf

echo '
###to enable correct use of response.static_version
location ~* ^/(\w+)/static(?:/_[\d]+\.[\d]+\.[\d]+)?/(.*)$ {
    alias /home/www-data/py27env/web2py/applications/$1/static/$2;
    expires max;
    ### if you want to use pre-gzipped static files (recommended)
    ### check scripts/zip_static_files.py and remove the comments
    # include /etc/nginx/conf.d/web2py/gzip_static.conf;
}
###
###if you use something like myapp = dict(languages=['en', 'it', 'jp'], default_language='en') in your routes.py
#location ~* ^/(\w+)/(en|it|jp)/static/(.*)$ {
#    alias /home/www-data/py27env/web2py/applications/$1/;
#    try_files static/$2/$3 static/$3 =404;
#}
###
'> /etc/nginx/conf.d/web2py/serve_static.conf

echo '
location / {
    uwsgi_pass      web2py27;
    include         uwsgi_params;
    uwsgi_param     UWSGI_SCHEME $scheme;
    uwsgi_param     SERVER_SOFTWARE    nginx/$nginx_version;
    ###remove the comments to turn on if you want gzip compression of your pages
    # include /etc/nginx/conf.d/web2py/gzip.conf;
    ### end gzip section
    ### remove the comments if you use uploads (max 10 MB)
    #client_max_body_size 10m;
    ###
    }
'> /etc/nginx/conf.d/web2py/serve_web2py27.conf

# Create configuration file /etc/nginx/sites-available/web2py
echo '
upstream web2py27 {
    server unix:///run/uwsgi/web2py27.socket;
}
server {
        listen          80;
        server_name     $hostname;
        
        # static serving
        include /etc/nginx/conf.d/web2py/serve_static.conf;
        include /etc/nginx/conf.d/web2py/serve_web2py27.conf;
}
server {
        listen 443 default_server ssl;
        server_name     $hostname;
        ssl_certificate         /etc/nginx/ssl/web2py.crt;
        ssl_certificate_key     /etc/nginx/ssl/web2py.key;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_prefer_server_ciphers on;
        ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
        ssl_ecdh_curve secp384r1; # Requires nginx >= 1.1.0
        ssl_session_cache shared:SSL:10m;
        ssl_session_tickets off; # Requires nginx >= 1.5.9
        ssl_stapling on; # Requires nginx >= 1.3.7
        ssl_stapling_verify on; # Requires nginx => 1.3.7
        resolver 8.8.8.8 8.8.4.4 valid=300s;
        resolver_timeout 5s;
        ssl_dhparam /etc/ssl/certs/dhparam.pem;
        ## remove only if you know what you are doing
        #add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";
        #add_header X-Frame-Options DENY;
        #add_header X-Content-Type-Options nosniff;
        include /etc/nginx/conf.d/web2py/serve_static.conf;
        include /etc/nginx/conf.d/web2py/serve_web2py27.conf;
}' >/etc/nginx/sites-available/web2py27

ln -s /etc/nginx/sites-available/web2py27 /etc/nginx/sites-enabled/web2py27
rm /etc/nginx/sites-enabled/default
cd /etc/ssl/certs
openssl dhparam -out dhparam.pem 4096
mkdir /etc/nginx/ssl
cd /etc/nginx/ssl

if [ "$NOCERTIFICATE" == "0" ]
then
    openssl req -x509 -newkey rsa:2048 -nodes -keyout web2py.key -out web2py.crt -days 1780
    chmod 400 web2py.key
    openssl x509 -noout -fingerprint -text < web2py.crt > web2py.info
fi
# Prepare folders for uwsgi
mkdir /etc/uwsgi
mkdir /etc/uwsgi/vassals


#uWSGI Emperor
echo '[Unit]
Description = uWSGI Emperor
After = syslog.target
[Service]
ExecStart = /home/www-data/py27env/bin/uwsgi --ini /etc/uwsgi/emperor.ini
RuntimeDirectory = uwsgi
Restart = always
KillSignal = SIGQUIT
Type = notify
StandardError = syslog
NotifyAccess = all
User = www-data
Group = www-data
[Install]
WantedBy = multi-user.target
' > /etc/systemd/system/emperor.uwsgi.service
# Create configuration for emperor
echo '[uwsgi]
emperor = /etc/uwsgi/vassals
uid = www-data
gid = www-data
'>/etc/uwsgi/emperor.ini
# Create configuration file /etc/uwsgi/web2py.ini
echo '[uwsgi]
home = /home/www-data/py27env
socket = /run/uwsgi/web2py27.socket
pythonpath = /home/www-data/py27env/web2py
mount = /=wsgihandler:application
processes = 4
vacuum = true
master = true
harakiri = 60
reload-mercy = 8
cpu-affinity = 1
stats = /run/uwsgi/web2pystats.socket
max-requests = 2000
limit-as = 512
reload-on-as = 256
reload-on-rss = 192
uid = www-data
gid = www-data
touch-reload = /home/www-data/py27env/web2py/routes.py
cron = 0 0 -1 -1 -1 python2.7 /home/www-data/py27env/web2py/web2py.py -Q -S welcome -M -R scripts/sessions2trash.py -A -o
no-orphans = true
' >/etc/uwsgi/vassals/web2py.ini

# Install Web2py
mkdir /home/www-data
cd /home/www-data
virtualenv --python=python2.7 py27env
cd py27env/
source bin/activate
pip install --upgrade uwsgi
if [ "$WITH_DATABASE" != "0" ]
then
    pip install --upgrade psycopg2
fi
# optional pip requirements go here

# end of pip requirements
wget http://web2py.com/examples/static/web2py_src.zip
unzip web2py_src.zip

mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py
rm web2py_src.zip
cd /home/www-data/py27env/web2py
if [ "$NOPASSWORD" == "0" ]
then
   python -c "from gluon.main import save_password; save_password('$WEB2PY_PASS',443)"
fi
chown -R www-data:www-data /home/www-data/py27env/web2py
deactivate

systemctl enable emperor.uwsgi.service
systemctl restart nginx
systemctl restart emperor.uwsgi.service
if [ "$WITH_DATABASE" != "0" ]
then
    systemctl restart postgresql
fi

echo <<EOF
you can stop uwsgi and nginx with
  sudo systemctl stop nginx
  sudo systemctl stop emperor.uwsgi.service
 
and start it with
  sudo systemctl start nginx
  sudo systemctl start emperor.uwsgi.service
EOF

