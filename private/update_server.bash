#!/bin/bash

cd /srv/gbs_dev/gbs
fossil update
###systemctl stop web2py-scheduler-${dir}
###systemctl start web2py-scheduler-${dir}
fossil branch list>revision_info.txt
echo end-of-branches>>revision_info.txt
fossil stat>>revision_info.txt
chown -R www-data:developers .


/etc/init.d/apache2 restart
