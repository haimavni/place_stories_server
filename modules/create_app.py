# coding: utf-8

from .injections import inject
import os
import subprocess
from send_email import email

def create_an_app(rec):
    request, comment, log_path = inject('request', 'comment', 'log_path')
    folder = os.path.abspath(request.folder)
    path = folder + '/private'
    logs_path = log_path()
    app = rec.app_name
    comment(f'about to create {app} and run it from {path}')
    orig_dir = os.getcwd()
    os.chdir(path)
    curr_dir = os.getcwd()
    comment(f"curr dir is {curr_dir}")
    exists = os.path.exists("create_app.bash")
    comment(f"script exists? {exists}")
    command = f'bash create_app.bash {app} master {rec.email} {rec.password} {rec.first_name} {rec.last_name}'
    log_file_name = logs_path + f"app-creation-{rec.app_name}.log"
    comment(f"log file name is {log_file_name}")
    command = command.split()
    comment(f"command is {command}")
    
    result = subprocess.run(command, stdout=open(f"log_file_name", "w"), stderr=open(f"log_file_name" + ".err", "w"), shell=True)
    code = result.returncode
    comment(f'finished creation of {rec.app_name}. result = {result}')
    os.chdir(orig_dir)
    if code == 0:
        notify_developers(rec, True)
        notify_customer(rec)
    else:
        notify_developers(rec, False)
    #command = 'systemctl restart web2py-scheduler'
    with open('/home/www-data/tol_test/private/restart_now', 'w') as f:
        f.write("restart now")
    #with open(log_file_name, 'a') as log_file:
        #log_file.write('before systemctl restart')
        #code = subprocess.call(command, stdout=log_file, stderr=log_file, shell=True)
        #log_file.write('after systemctl restart')                       
    return dict(code=code, command=command)

def notify_customer(rec):
    mail, comment, request = inject('mail', 'comment', 'request')
    manual_link = 'https://docs.google.com/document/d/1IoE3xIN3QZvqk-YZZH55PLzMnASVHsxs0_HuSjYRySc/edit?usp=sharing'
    ####host=request.env.http_host.split(':')[0]
    host = rec.host
    link = 'https://' + host + '/' + rec.app_name
    if rec.locale == 'he':
        message_fmt = '''<div dir="rtl">
        אתר הסיפורים החדש שלך מוכן!<br><br>

        הקלק {link} כדי להיכנס לאתר.<br><br>

        להדרכה בנושא התאמת האתר ועריכת תוכנו הקלק על הקישור הבא:<br>
        {ml}
        </div>
        '''
    else:
        message_fmt = '''
    Welcome to your new stories site!<br><br>
    
    Click {link} to visit.<br><br>

    You can read some useful information in the link below<br>
    {ml}
    '''
    message = ('', message_fmt.format(ml=manual_link, link=link))
    result = email(receivers=rec.email, message=message, subject='Starting your new site')
    comment(f'mail sent to customer? {result}')

def notify_developers(rec, success):
    auth, comment, DEVELOPER = inject('auth', 'comment', "DEVELOPER")
    site_name=rec.app_name
    status = 'was successfuly created ' if success else 'had errors while being created'
    message = f'''
    New site {site_name} {status}.
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
        
    
