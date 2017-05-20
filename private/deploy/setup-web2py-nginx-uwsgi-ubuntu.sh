#!/bin/bash

# from https://groups.google.com/forum/#!topic/web2py/57PnJZsS3l0
echo 'setup-web2py-nginx-uwsgi-ubuntu-precise.sh'
echo 'Requires Ubuntu > 12.04 or Debian >= 8 and installs Nginx + uWSGI + Web2py'
mypath=`realpath $0`
mypath=`dirname $mypath`

#to prevent locale error messages
#Just add the following to your .bashrc file (assuming you're using bash)

#export LC_ALL="en_US.UTF-8"

# Check if user has root privileges
if [[ $EUID -ne 0 ]]; then
   echo "You must run the script as root or using sudo"
   exit 1
fi
# parse command line arguments
nopassword=0
nocertificate=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-password) nopassword=1; shift 1;;
    --no-certificate) nocertificate=1; shift 1;;
  esac
done
# Get Web2py Admin Password
if [ "$nopassword" -eq 0 ]
then
  echo -e "Web2py Admin Password: \c "
  read -s PW
  printf "\n"  # fix no new line artifact of "read -s" to avoid cleartext password
fi
# Upgrade and install needed software
apt-get update
apt-get -y upgrade
apt-get autoremove
apt-get autoclean
apt-get -y install nginx-full
apt-get -y install build-essential python-dev libxml2-dev python-pip unzip
apt-get -y install fcgiwrap
pip install setuptools --no-use-wheel --upgrade
PIPPATH=`which pip`
$PIPPATH install --upgrade uwsgi
# Create common nginx sections
mkdir /etc/nginx/conf.d/web2py
ln -s ${mypath}/gzip_static.conf /etc/nginx/conf.d/web2py/gzip_static.conf
ln -s ${mypath}/gzip.conf /etc/nginx/conf.d/web2py/gzip.conf
ln -s ${mypath}/fcgiwrap.conf /etc/nginx/fcgiwrap.conf

# Create configuration file /etc/nginx/sites-enabled/web2py
ln -s ${mypath}/web2py /etc/nginx/sites-enabled/web2py
rm /etc/nginx/sites-enabled/default
mkdir /etc/nginx/ssl
cd /etc/nginx/ssl
if [ "$nocertificate" -eq 0 ]
then
  openssl genrsa 1024 > web2py.key
  chmod 400 web2py.key
  openssl req -new -x509 -nodes -sha1 -days 1780 -key web2py.key > web2py.crt
  openssl x509 -noout -fingerprint -text < web2py.crt > web2py.info
fi
# Prepare folders for uwsgi
sudo mkdir /etc/uwsgi
sudo mkdir /var/log/uwsgi
sudo mkdir /etc/systemd
sudo mkdir /etc/systemd/system

#uWSGI Emperor
ln -s ${mypath}/emperor.uwsgi.service /etc/systemd/system/emperor.uwsgi.service

# Create configuration file /etc/uwsgi/web2py.ini
ln -s ${mypath}/web2py.ini /etc/uwsgi/web2py.ini

#Create a configuration file for uwsgi in emperor-mode
#for Upstart in /etc/init/uwsgi-emperor.conf
ln -s ${mypath}/uwsgi-emperor.conf /etc/init/uwsgi-emperor.conf
# Install Web2py
mkdir /home/www-data
cd /home/www-data
wget http://web2py.com/examples/static/web2py_src.zip
unzip web2py_src.zip
mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py
rm web2py_src.zip
chown -R www-data:www-data web2py
cd /home/www-data/web2py
if [ "$nopassword" -eq 0 ]
then
   sudo -u www-data python -c "from gluon.main import save_password; save_password('$PW',443)"
fi

/etc/init.d/nginx start
systemctl start emperor.uwsgi.service

echo <<EOF
you can stop uwsgi and nginx with

  sudo /etc/init.d/nginx stop
  sudo systemctl start emperor.uwsgi.service
 
and start it with

  sudo /etc/init.d/nginx start
  systemctl start emperor.uwsgi.service

EOF

