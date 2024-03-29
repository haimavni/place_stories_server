# coding: utf-8

from .injections import inject
import os
import subprocess
from send_email import email

def create_an_app(rec):
    request, comment, log_path = inject('request', 'comment', 'log_path')
    folder = os.path.abspath(request.folder)
    path = folder + '/private/'
    logs_path = log_path()
    app = rec.app_name
    bash_name = path + "create_app.bash"
    comment(f'about to create {app}. bash name is {bash_name}')
    exists = os.path.exists(bash_name)
    comment(f"script  {bash_name} exists? {exists}")
    command = f'bash {bash_name} {app} master {rec.email} {rec.password} {rec.first_name} {rec.last_name}'
    log_file_name = logs_path + f"app-creation-{rec.app_name}.log"
    comment(f"log file name is {log_file_name}")
    command_line = command
    command = command.split()
    comment(f"command is {command}")
    
    result = subprocess.run(command, stdout=open(f"{log_file_name}", "w"), stderr=open(f"{log_file_name}" + ".err", "w"), shell=True)
    code = result.returncode
    comment(f'finished creation of {rec.app_name}. result = {result}')
    if code == 0:
        notify_developers(rec, True, command_line)
        notify_customer(rec)
    else:
        notify_developers(rec, False, command_line)
    with open('/home/www-data/tol_test/private/restart_now', 'w') as f:
        f.write("restart now")
    return dict(code=code, command=command, command_line=command_line)

def notify_customer(rec):
    mail, comment, request = inject('mail', 'comment', 'request')
    manual_link = 'https://docs.google.com/document/d/1IoE3xIN3QZvqk-YZZH55PLzMnASVHsxs0_HuSjYRySc/edit?usp=sharing'
    host = rec.host
    link = 'https://' + host + '/' + rec.app_name
    if rec.locale == 'he':
        message = f'''<div dir="rtl">
        אתר הסיפורים החדש שלך מוכן!<br><br>

        הקלק {link} כדי להיכנס לאתר.<br><br>

        להדרכה בנושא התאמת האתר ועריכת תוכנו הקלק על הקישור הבא:<br>
        {manual_link}
        </div>
        '''
    else:
        message = f'''
    Welcome to your new stories site!<br><br>
    
    Click {link} to visit.<br><br>

    You can read some useful information in the link below<br>
    {manual_link}
    '''
    result = email(receivers=rec.email, message=message, subject='Starting your new site')
    comment(f'mail sent to customer? {result}')

def notify_developers(rec, success, command_line):
    auth, comment, DEVELOPER = inject('auth', 'comment', "DEVELOPER")
    site_name=rec.app_name
    status = 'was successfuly created ' if success else 'had errors while being created'
    message = f'''
    New site {site_name} {status}.
    command is {command_line}
    '''
    receivers = auth.role_user_list(DEVELOPER)
    result = email(receivers=receivers, message=message, subject='New app')

def create_pending_apps():
    db, log_exception = inject('db', 'log_exception')
    try:
        lst = db((db.TblCustomers.created==False) & (db.TblCustomers.confirmation_key=='')).select()
        for rec in lst:
            rec.update_record(created=True)
            db.commit()
            create_an_app(rec)
    except Exception as e:
        log_exception('Error creating apps')
        raise
    
def create_app(customer_id):
    db, log_exception = inject('db', 'log_exception')
    rec = db(db.TblCustomers.id==customer_id).select().first()
    msg = "ok"
    result = "about to start"
    try:
        result = create_an_app(rec)
    except Exception as e:
        msg = str(e)
        log_exception(f'Error creating apps')
    return dict(msg=msg, result=result)
        
    
