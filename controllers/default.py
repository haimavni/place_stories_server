# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

from ws_messaging import send_message, messaging_group
from admin_support.access_manager import AccessManager

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    response.flash = T("Hello World")
    return dict(message=T('Welcome to web2py!'))


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
    return dict(ws='ws://{host}:8888/realtime/{group}'.format(host=host, group=group))

@serve_json
def read_privileges(vars):
    if not auth.current_user():
        return dict()
    ###emails_suspended = rec.emails_suspended if rec else False
    privileges = dict()
    for const_name in membership_consts:
        const_id = auth.id_group(const_name)
        if auth.has_membership(const_id):
            privileges[const_name] = True
    result = dict(
        privileges = privileges,
        user_id=auth.current_user()
    )
    return result

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

def notify_registration(vars):
    ui = vars.user_info
    user_name = ui.first_name + ' ' + ui.last_name
    user_email = ui.email
    lst = db((db.auth_membership.group_id==ADMIN)&(db.auth_user.id==db.auth_membership.user_id)).select(db.auth_user.email)
    receivers = [r.email for r in lst]    
    message = ('', '''
    {uname} has just registered to <b>Coolano</b>.
    Email adddress is {uemail}.


    Click <a href="www.coolano.biz/coolano/admin/access_manager">here</a> for access manager.
    '''.format(uname=user_name, uemail=user_email).replace('\n', '<br>'))
    mail.send(to=receivers, subject='New Coolano user', message=message)

@serve_json
def register_user(vars):
    from gluon.utils import web2py_uuid
    u = vars.user_info
    if not db(db.auth_user.email==u.email).isempty():
        raise User_Error('<br><h4>Email is already in use!</h4>')
    u.registration_key = key = web2py_uuid()

    am = AccessManager()
    user_data, new_user = am.add_or_update_user(u)
    #send verification email to new user
    link = auth.url('verify_email', args=[key], scheme=True)
    u.update(dict(key=key, link=link, username=u.email))
    good = auth.settings.mailer and auth.settings.mailer.send(
        to=u.email,
        subject=auth.messages.verify_email_subject,
        message='Click on the link {lnk} to verify your email'.format(lnk=link))
    if not good:
        db.rollback()
        raise User_Error(auth.messages.unable_send_email)
    notify_registration(vars)
    return dict(good=True);

def verify_email():
    auth.verify_email()

@serve_json
def check_if_logged_in(vars):
    return dict(is_logged_in = auth.is_logged_in() or True)  ###temporary for dev!!!

@serve_json
def login(vars):
    result = auth.login_bare(vars.user_email, vars.password)
    if not result:
        raise User_Error('login_failed')
    user = Storage()
    for k in ['email', 'facebook', 'first_name', 'last_name', 'id', 'skype']:
        v = result[k]
        if v:
            user[k] = v
        
    user.privileges = auth.get_privileges()
    return dict(user=user)

@serve_json
def logout(vars):
    auth.logout_bare()
    return dict(logged_out=True)

def reset_password():
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


