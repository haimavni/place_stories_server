from injections import inject
import os
import subprocess

def create_an_app(rec):
    request = inject('request')
    rec.update_record(created=True)  #if failed will need to set it to False    request,comment = inject('request', 'comment')
    folder = os.path.abspath(request.folder)
    path = folder + '/private'
    comment("folder is {f}".format(f=folder))
    log_path = folder + '/logs/create-{app}.log'.format(app=rec.app_name)
    os.chdir(path)
    command = 'bash create_app.bash {app_name} test {email} {password} {first_name} {last_name}'. \
        format(app_name=rec.app_name, email=rec.email, password=rec.password, first_name=rec.first_name, last_name=rec.last_name)
    with open(log_path, 'w') as log_file:
        code = subprocess.call(command, stdout=log_file, stderr=log_file, shell=True)
    if code == 0:
        notify_customer(rec)
        notify_developer(rec, True)
    else:
        notify_developer(rec, False)
    return code

def notify_customer(rec):
    mail = inject('mail')
    manual_link = 'https://docs.google.com/document/d/1IoE3xIN3QZvqk-YZZH55PLzMnASVHsxs0_HuSjYRySc/edit?usp=sharing'
    message = ('', '''
    Welcome to your new stories site!
    
    You can read some useful information in the link below
    {ml}
    '''.format(ml=manual_link))
    mail.send(to=rec.email, message=message, subject='Starting your new site')
    
def notify_developer(rec, success):
    mail = inject('mail')
    status = 'was successfuly created ' if success else 'had errors while being created'
    message = ('', '''
    New site {site_name} {status}.
    '''.format(site_name=rec.app_name, status=status))
    mail.send(to='haimavni@gmail.com', message=message, subject='New app')

def create_pending_apps():
    db, log_exception = inject('db', 'log_exception')
    try:
        while True:
            rec = db((db.TblCustomers.created==False) & (db.TblCustomers.confirmation_key=='')).select().first()
            if not rec:
                break
            code = create_an_app(rec)
    except Exception, e:
        log_exception('Error creating apps')
        raise
