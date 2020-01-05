# coding: utf-8

from admin_support.access_manager import register_new_user, AccessManager
from gluon.utils import web2py_uuid

def init_database():
    if len(request.args) < 4:
        return "database initialized without admin"
    email,password,first_name,last_name = request.args
    usr_id = register_new_user(email, password, first_name, last_name)
    am = AccessManager()
    am.enable_all_roles(usr_id)
    db.commit()
    return "database initialized"

@serve_json
def request_new_app(vars):
    #check uniqueness first
    app = request.application
    r = app.find('_')
    if r >= 0:
        app = app[:r]
    app_name = app + '_' + vars.app_name
    if not db(db.TblCustomers.app_name==vars.app_name).isempty():
        error_message = "admin.duplicate-app-name"
    else:
        confirmation_key=web2py_uuid()
        db.TblCustomers.insert(
            first_name=vars.first_name,
            last_name=vars.last_name,
            email=vars.email,
            password=vars.password,
            app_name=app_name,
            confirmation_key=confirmation_key,
            locale=vars.locale
        )
        error_message = ""
        host=request.env.http_host.split(':')[0]
        confirmation_url = '/{app}/init_app/confirm_new_app?app_name={app_name}&confirmation_key={confirmation_key}'. \
            format(app=request.application, app_name=app_name, confirmation_key=confirmation_key)
        confirmation_link = '{host}{confirmation_url}'.format(host=host, confirmation_url=confirmation_url)
        if vars.locale == 'he':
            mail_message_fmt = '''
<div dir="rtl">
שלום {first_name} {last_name}, <br><br>
כדי להפעיל את האתר החדש שלך, הקלק {link}
</div>
            '''
        else:
            mail_message_fmt = '''
            Hi {first_name} {last_name},<br><br>
            
            Click {link} to activate your new site.<br><br>
            
            '''
        mail_message = ('', mail_message_fmt.format(first_name=vars.first_name, last_name=vars.last_name, link=confirmation_link))
        result = mail.send(to=vars.email, subject='Your new site', message=mail_message)
        if not result:
            error_message = mail.error.strerror
        comment('confirmation mail was sent to {email} with result {result}. message: {msg}', email=vars.email, result=result, msg=mail_message)
    return dict(error_message=error_message)

def confirm_new_app():
    vars = request.vars
    customer_rec = db(db.TblCustomers.app_name==vars.app_name).select().first()
    if not customer_rec.confirmation_key:
        return dict()
    if customer_rec.confirmation_key != vars.confirmation_key:
        comment('customer rec key: {crk}, vars.conf key: {vck}', crk=customer_rec.confirmation_key, vck=vars.confirmation_key)
        raise Exception('Confirmation key mismatch')
    customer_rec.update_record(confirmation_key='')
    promote_task('create_pending_apps')
    lang = '_he' if customer_rec.locale == 'he' else ''
    response.view = "%s/%s.%s".format(request.controller, request.function + lang, request.extension)
    return dict()

@serve_json
def get_frame_list(vars):
    result = []
    for rec in db(db.TblCustomers).select():
        url = 'https://{host}/{app}'.format(host = rec.host, app=rec.app_name)
        result.append(dict(url=url))
    return dict(frame_urls=result)