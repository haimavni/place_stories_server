# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

from folders import local_folder, local_cards_folder, url_folder
from folders import url_cards_folder
from ws_messaging import send_message, messaging_group
from admin_support import AccessManager
from send_email import email
import create_card
from gluon.storage import Storage
from misc_utils import make_qr_code
import datetime

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################
import os

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    key = request.vars.key
    if key:
        rec = db(db.TblShortcuts.key==key).select().first()
        if rec:
            if request.is_https and not ":8000" in request.env.http_host:
                request.requires_https()
            redirect(rec.url)
    app = request.application
    fname = f'/{app}/static/aurelia/index.html'
    fname1 = f'{app}/static/aurelia/index-{app}.html'
    if os.path.isfile('./applications/' + fname1):
        fname = '/' + fname1
    fname = f'/{app}/aurelia'
    redirect(f"{fname}")

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

@serve_json
def get_tornado_host(vars):
    host = request.env.HTTP_HOST
    if ':' in host:
        host = host.split(':')[0]
    group = messaging_group(group=vars.group)
    if request.is_https:
        ws = 'wss'
        port = '8443' if host == 'tol.life' else '9443'
    else:
        ws = 'ws'
        port = '8888'
    return dict(ws=f'{ws}://{host}:{port}/realtime/{group}')

@serve_json
def read_privileges(vars):
    user_id = auth.current_user()  #if local : or 2
    if request.env.http_host.startswith('127'):
        user_id = user_id or 2
    if not user_id:
        return dict(user_id=0, privileges={}, user_name="")
    ###emails_suspended = rec.emails_suspended if rec else False
    user_name = auth.user_name(user_id)
    privileges = get_the_privileges(user_id)
    result = dict(
        privileges = privileges,
        user_id=user_id,
        user_name=user_name,
    )
    return result

def get_the_privileges(user_id):
    privileges = Storage()
    for const_name in membership_consts:
        const_id = auth.id_group(const_name)
        privileges[const_name] = auth.has_membership(const_id, user_id=user_id)
    return privileges

@serve_json
def read_configuration(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec.app_title:
        rec = db((db.TblLocaleCustomizations.key=='app-title') & (db.TblLocaleCustomizations.lang=='he')).select().first()
        if rec:
            config_rec.update_record(app_title=rec.value)
    config = config_rec.as_dict()
    return dict(config=config)

@serve_json
def translate(vars):
    result = dict()
    if isinstance(vars.phrases, dict):
        for p in vars.phrases:
            result[p] = T(vars.phrases[p])
    else:
        for p in vars.phrases:
            result[p] = T(p)
    return dict(translations=result)

def register():
    return dict(controller='RegisterCtrl')

@serve_json
def register_user(vars):
    new_user = auth.register_user(vars.user_info)
    new_user_id = new_user.id if new_user else None
    return dict(user_id=new_user_id);

def verify_email():
    success = auth.verify_email(key=request.args[0])
    return dict(success=success)

@serve_json
def check_if_logged_in(vars):
    is_logged_in = auth.is_logged_in()
    user_id=auth.current_user()
    comment(f"is logged in? {is_logged_in} user_id: {user_id}")
    return dict(is_logged_in=is_logged_in, user_id=user_id)

@serve_json
def login(vars):
    if not vars.email:
        return dict()
    result = auth.login_bare(vars.email, vars.password, sneak_in=vars.sneak_in)
    if isinstance(result, str):
        if vars.sneak_in:
            return dict(user=dict(id=0), unregistered=True)
        else:
            raise User_Error(result)
    user = Storage()
    for k in ['email', 'facebook', 'first_name', 'last_name', 'id', 'skype']:
        v = result[k]
        if v:
            user[k] = v

    user.privileges = get_the_privileges(user.id)
    return dict(user=user)

@serve_json
def logout(vars):
    auth.logout_bare()
    return dict(logged_out=True)

def reset_password_old():
    response.file = 'login.html'
    user = db(db.auth_user.email==request.vars.email).select().first()
    status = 'error'
    if not user:
        message = 'User {} does not exist'.format(request.vars.email)
    elif user.registration_key in ('pending', 'disabled', 'blocked'):
        message = auth.messages.registration_pending
    elif auth.email_reset_password(user):
        message = auth.messages.email_sent
        status = 'success'
    else:
        message = auth.messages.unable_to_send_email
    redirect(URL(r=request, f='login', vars=dict(message=message, status=status, controller='')))

def change_password():
    return dict(controller='ChangePasswordCtrl')

@serve_json
def do_change_password(vars):
    good = auth.change_password(vars.user_info.old_password, vars.user_info.new_password)
    if not good:
        raise User_Error('Wrong Password')
    return dict(good=True)

@serve_json
def get_curr_version(vars):
    try:
        with open(base_app_dir + 'static/aurelia/curr_version.txt') as f:
            s = f.read()
    except:
        s = ''
    return dict(version=s)

@serve_json
def get_interested_contact(vars):
    msg = vars.contact_message
    message = f'''
    <html>
    <div direction="{vars.rtltr}">
    <p>
    {vars.contact_first_name} {vars.contact_last_name} contacted.<br/>
    Mail: {vars.contact_email}<br/>
    mobile: {vars.contact_mobile} 
    </p>
    <p>
    Message is:
    </p>
    <p>
    {msg}
    </p>
    </div>
    </html>
    '''
    result = email(sender="admin", receivers="haimavni@gmail.com", subject = "New Tol.Life prospect", message=message)
    error = "" if result else "error sending email"
    return dict(result=result, error=error)

@serve_json
def save_feedback(vars):
    today = datetime.date.today()
    db.TblFeedback.insert(
        fb_date=today,
        fb_message=vars.feedback_message,
        fb_code_version=vars.code_version,
        fb_email=vars.feedback_email,
        fb_name=vars.feedback_name,
        fb_device_type=vars.device_type,
        fb_device_details=vars.device_details
    )
    notify_new_feedback()
    return dict()

@serve_json
def get_feedbacks(vars):
    lst = db(db.TblFeedback).select(limitby=(0,200), orderby=~db.TblFeedback.id)
    feedbacks = [dict(name=r.fb_name,
                      date=fb_date_str(r)  ,
                      email=r.fb_email,
                      message=r.fb_message,
                      version=r.fb_code_version,
                      device_type=r.fb_device_type,
                      device_details=r.fb_device_details) for r in lst]
    return dict(feedbacks=feedbacks)

def fb_date_str(fb_rec):
    date = fb_rec.fb_date
    if not date:
        return fb_rec.fb_code_version
    return date.strftime('%d.%m.%Y')

def test_collect_mail():
    from collect_emails import collect_mail
    collect_mail()

@serve_json
def get_languages(vars):
    s = db(db.TblConfig.id==1).select().first().languages
    languages=s.split(',')
    return dict(languages=languages)

@serve_json
def set_locale_override(vars):
    rec = db((db.TblLocaleCustomizations.lang==vars.lang) & (db.TblLocaleCustomizations.key==vars.key)).select().first()
    if rec:
        if vars.value == '---':
            n = db((db.TblLocaleCustomizations.lang==vars.lang) & (db.TblLocaleCustomizations.key==vars.key)).delete()
            if n != 1:
                raise Exception('Locale override was not deleted')
        else:
            rec.update_record(value=vars.value)
    else:
        db.TblLocaleCustomizations.insert(lang=vars.lang, key=vars.key, value=vars.value)
    return dict()

@serve_json
def get_locale_overrides(vars):
    result = dict()
    try:
        lst = db(db.TblLocaleCustomizations).select()
    except:
        return dict(locale_overrides={})
    for rec in lst:
        if rec.lang not in result:
            result[rec.lang] = dict()
        keys = rec.key.split('.')
        item = result[rec.lang]
        for key in keys[:-1]:
            if key not in item:
                item[key] = dict()
            item = item[key]
        key = keys[-1]
        item[key] = rec.value
    return dict(locale_overrides=result)

@serve_json
def notify_new_files(vars):
    uploaded_file_ids = vars.uploaded_file_ids
    send_message(key=vars.what +'-UPLOADED', group='ALL', uploaded_file_ids=uploaded_file_ids)
    return dict()

@serve_json
def reset_password(vars):
    user_rec = db(db.auth_user.email==vars.email).select().first()
    am = AccessManager()
    app_name = request.application
    host=request.env.http_host.split(':')[0]
    registration_key = am.replace_password(user_rec.id, vars.password)
    confirmation_url = '/{app}/default/confirm_password_reset?app_name={app_name}&registration_key={registration_key}&email={email}'. \
        format(app=request.application, app_name=app_name, registration_key=registration_key, email=vars.email)
    confirmation_link = 'http://{host}{confirmation_url}'.format(host=host, confirmation_url=confirmation_url)
    mail_message = f'''
    Hi {user_rec.first_name} {user_rec.last_name},<br><br>

    Click {confirmation_link} to confirm your new password.<br><br>

    '''
    result = email(receivers=vars.email, subject='New password', message=mail_message)
    if not result:
        error_message = mail.error.strerror
        raise Exception("Email could not be sent - {em}".format(em=error_message))
    else:
        return dict()

@serve_json
def get_shortcut(vars):
    url = vars.url
    rec = db(db.TblShortcuts.url==url).select().first()
    if rec:
        key = rec.key
    else:
        key = create_key() #if paranoid, ensure key is not in use yet
        if db(db.TblShortcuts.key==key).count() > 0:
            comment(f"duplicate key {key} found in get shortcut")
            raise Exception('Non unique key')
        db.TblShortcuts.insert(url=url, key=key)
    shortcut = '/' + request.application + '?key='  + key
    return dict(shortcut=shortcut)

def create_key():
    import random, base64
    r = random.randint(0, 0xffffffffffffffff)
    s = str(r)
    s_bytes = s.encode('ascii')
    s_64 = base64.b64encode(s_bytes)
    s = s_64.decode('ascii')
    while s[-1] == "=":
        s = s[:-1]
    return s

def confirm_password_reset():
    vars = request.vars
    user_rec = db(db.auth_user.email==vars.email).select().first()
    if user_rec.registration_key != vars.registration_key:
        raise Exception("Registration key mismatch")
    user_rec.update_record(registration_key="")
    return dict()


def notify_new_feedback():
    lst = db((db.auth_membership.group_id==ADMIN)&(db.auth_user.id==db.auth_membership.user_id)&(db.auth_user.id>1)).select(db.auth_user.email)
    receivers = [r.email for r in lst]
    app = request.application
    host = request.env.http_origin
    message = f'''
    New feedback has been received.


    Click <a href="{host}/{app}/static/aurelia/index.html#/feedbacks">here</a> to view.
    '''.replace('\n', '<br>')
    email(receivers=receivers, subject='New Stories Feedback', message=message)

@serve_json
def make_fb_card(vars):
    app = request.application
    host = request.env.http_host
    img_src = vars.img_src
    comment(f"============make fb card. img src: {img_src}")
    r = img_src.rfind('/')
    img_name = img_src[r+1:]
    img_src = url_cards_folder() + f'padded_images/{img_name}'
    fname = create_key()
    card_url = f'https://cards.{host}/{app}/{fname}.html'
    content = create_card.card_data(vars.url, img_src, vars.title, vars.description)
    folder = local_cards_folder()
    with open(f"{folder}" + fname + ".html", "w", encoding="utf-8") as f:
        f.write(content)
    return dict(card_url=card_url)

@serve_json
def create_qrcode(vars):
    url = vars.url
    name = vars.name
    return make_qr_code(url, name=name)

@serve_json
def save_app_title(vars):
    app_title = vars.app_title
    rec = db(db.TblConfiguration).select().first()
    rec.update_record(app_title=app_title)

