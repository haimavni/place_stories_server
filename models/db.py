# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

import os

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig

## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)


def __open_db():
    db_host = os.getenv('POSTGRES_HOST')
    dbname = request.application
    adapter = 'psycopg2:'
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')

    _debugging = False  # request.function not in ('whats_up', 'log_file_data')
    db_spec = f'postgres:{adapter}//{db_user}:{db_password}@{db_host}/{dbname}'
    try:
        db = DAL(db_spec,
                 pool_size=50,
                 debug=_debugging,
                 lazy_tables=False)  # it causes an exeption!
    except Exception as e:
        comment(f'Failed to open db {db_spec}. Error: {e}.')
        raise
    return db


db = __open_db()

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = myconf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.take('forms.separator')
response.headers['Access-Control-Allow-Origin'] = '*'

## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Service, PluginManager
from my_auth import MyAuth

auth = MyAuth(db)
auth.expiration = 31 * 24 * 3600
service = Service()
plugins = PluginManager()

## create all tables needed by auth if not custom tables
# todo: the lines below cause "auth user table redefined" error on the server but not on the development system. do not use it for now
auth.settings.extra_fields['auth_user'] = [Field('skype'), Field('facebook')]
auth.define_tables(username=False, signature=False)

## configure email
_host = request.env.http_host
mail = auth.settings.mailer
mail.settings.server = 'localhost'
mail.settings.sender = f'info@{_host}'
mail.settings.login = ''

## configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

membership_consts = ['ADMIN', 'DEVELOPER', 'EDITOR', 'COMMENTATOR', 'PHOTO_UPLOADER', 'ACCESS_MANAGER', 'CHATTER',
                     'CHAT_MODERATOR', 'TEXT_AUDITOR', 'DATA_AUDITOR', 'HELP_AUTHOR', 'ADVANCED', 'MAIL_WATCHER',
                     'ARCHIVER', 'TESTER', 'RESTRICTED', 'VIDEO_EDITOR']


def __calc_membership_const(const_name):
    display_name = ' '.join([z.capitalize() for z in const_name.split('_')])
    const_id = auth.id_group(const_name)
    if not const_id:
        lock_file_name = '{p}membership[{a}].lock'.format(p=log_path(), a=request.application)
        if os.path.isfile(lock_file_name):
            return
        with open(lock_file_name, 'w') as f:
            f.write('locked')
        try:
            const_id = auth.add_group(const_name, display_name)
            db.commit()
        finally:
            if os.path.isfile(lock_file_name):
                os.remove(lock_file_name)
    globals()[const_name] = const_id


for membership_name in membership_consts:
    __calc_membership_const(membership_name)


def no_admin():
    return db(db.auth_user.email == 'admin@gbs.com').isempty()


from admin_support.access_manager import register_new_user

try:
    if no_admin():
        admin_id = register_new_user('admin@gbs.com', '931632', 'admin', 'admin')
        auth.login_bare('admin@gbs.com', '931632')
        auth.set_access_manager(ACCESS_MANAGER, admin_id)
except Exception as e:
    pass

base_app_dir = 'applications/' + request.application + '/'
response.delimiters = ('{!', '!}')
response.controller = 'none'

BASE_URL = (request.env.http_origin or request.env.http_host) + '/' + request.application + '/'

story_visibility_values = ['SV_NO_CHANGE', 'SV_PUBLIC', 'SV_ADMIN_ONLY', 'SV_ARCHIVER_ONLY', 'SV_LOGGEDIN_ONLY']
for i, v in enumerate(story_visibility_values):
    globals()[v] = i
