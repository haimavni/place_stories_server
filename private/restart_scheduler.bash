FILE=./restart_now
if test -f "$FILE"; then
    #echo "$FILE exists."
    #echo about to restart >> restarts.log
    systemctl restart web2py-scheduler.service
    rm $FILE
fi
