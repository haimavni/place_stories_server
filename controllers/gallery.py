from os import listdir
from os.path import islink, isfile, join
from urllib.request import urlopen
import json
from gluon.storage import Storage
from http_utils import json_to_storage


@serve_json
def app_info(vars):
    lang = vars.lang or 'he'
    app_config = db(db.TblConfiguration).select().first()
    app_name_rec = db(
        (db.TblLocaleCustomizations.lang == lang) & (db.TblLocaleCustomizations.key == 'app-title')).select().first()
    app_name = app_name_rec.value if app_name_rec else 'Noname'
    app_description = app_config.description
    cover_photo = app_config.cover_photo if app_config.cover_photo else 'https://tol.life/gbs__www/static/apps_data/gbs/images/founders_group_photo.jpg'
    app0 = (request.application + '__').split("__")[0]
    host = calc_host()
    app = request.application
    logo_path = f'/apps_data/{app0}/images/app-logo.png'
    if not isfile(logo_path):
        logo_path = f'/apps_data/gbs/images/app-logo.png'
    logo_path = f'{host}/{app}/static' + logo_path
    return dict(
        host=host,
        app=request.application,
        app_name=app_name,
        app_description=app_description,
        logo_path=logo_path,
        cover_photo=cover_photo,
        allow_publishing=app_config.allow_publishing
    )


@serve_json
def apps_for_gallery(vars):
    apps = update_apps_table()
    host = calc_host()
    lst = db(db.TblApps).select()
    active = dict()
    for a in lst:
        active[a.app_name] = a.active
    app_list = []
    for app in apps:
        url = f'{host}/{app}/gallery/app_info'
        response = urlopen(url)
        info = json.loads(response.read())
        info = json_to_storage(info)
        if not info.allow_publishing and not vars.developer:
            continue
        if app not in active and not vars.editing:
            continue
        info.active = active[app]
        info.app = app
        app_list.append(info)
    return dict(app_list=app_list)


def update_apps_table():
    apps = app_list()
    for app in apps:
        if db(db.TblApps.app_name==app).isempty():
            db.TblApps.insert(app_name=app)
    return apps


@serve_json
def modify_app_state(vars):
    app = vars.app
    active = vars.active
    app_rec = db(db.TblApps.app_name==app).select().first()
    app_rec.update(active=active)
    return dict()


def app_list():
    path = './applications'
    my_app = request.application
    apps = [f for f in listdir(path) if islink(join(path, f)) and f != my_app]
    return apps

def calc_host():
    host = request.env.http_host
    if '8000' in host:
        host = f'http://{host}'
    else:
        host = f'https://{host}'
    return host