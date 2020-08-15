# coding: utf-8

from injections import inject
import os
import subprocess

def create_an_app(rec):
    request, comment, log_path = inject('request', 'comment', 'log_path')
    folder = os.path.abspath(request.folder)
    path = folder + '/private'
    logs_path = log_path()
    ###comment('in create app. path: {p}, folder: {f}, request.folder: {rf}', p=path, f=folder, rf=request.folder)
    comment('about to create {app}'.format(app=rec.app_name))
    orig_dir = os.getcwd()
    os.chdir(path)
    command = 'bash create_app.bash {app_name} test {email} {password} {first_name} {last_name}'. \
        format(app_name=rec.app_name, email=rec.email, password=rec.password, first_name=rec.first_name, last_name=rec.last_name)
    log_file_name = logs_path + "app-creation-{}.log".format(rec.app_name)
    with open(log_file_name, 'w') as log_file:
        code = subprocess.call(command, stdout=log_file, stderr=log_file, shell=True)
    comment('finished creation of {}. code = {}', rec.app_name, code)
    os.chdir(orig_dir)
    if code == 0:
        notify_developer(rec, True)
        notify_customer(rec)
    else:
        notify_developer(rec, False)
    command = 'systemctl restart web2py-scheduler'
    with open(log_file_name, 'a') as log_file:
        log_file.write('before systemctl restart')
        code = subprocess.call(command, stdout=log_file, stderr=log_file, shell=True)
        log_file.write('after systemctl restart')                       
    return code

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
    result = mail.send(to=rec.email, message=message, subject='Starting your new site')
    comment('mail sent to customer? {}', result)

def notify_developer(rec, success):
    mail, comment = inject('mail', 'comment')
    comment('about to nofity me')
    status = 'was successfuly created ' if success else 'had errors while being created'
    message = ('', '''
    New site {site_name} {status}.
    '''.format(site_name=rec.app_name, status=status))
    result = mail.send(to='haimavni@gmail.com', message=message, subject='New app')
    comment('mail sent to developer? {}', result)

def create_pending_apps():
    db, log_exception = inject('db', 'log_exception')
    try:
        for rec in db((db.TblCustomers.created==False) & (db.TblCustomers.confirmation_key=='')).select():
            rec.update_record(created=True)
            db.commit()
            code = create_an_app(rec)
    except Exception, e:
        log_exception('Error creating apps')
        raise
