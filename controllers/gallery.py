from os import listdir
from os.path import islink, isfile, join
from urllib.request import urlopen
import json
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
    logo_path = '/apps_data/{app0}/images/app-logo.png'
    if not isfile(logo_path):
        logo_path = '/apps_data/gbs/images/app-logo.png'
    return dict(
        app_name=app_name,
        app_description=app_description,
        logo_path=logo_path,
        cover_photo=cover_photo,
        allow_publishing=app_config.allow_publishing
    )


@serve_json
def apps_for_gallery(vars):
    apps = app_list()
    host = request.env.http_host
    if '8000' in host:
        host = f'http://{host}'
    else:
        host = f'https://{host}'
    lang = vars.lang or 'he'
    lst = db(db.TblApps).select()
    active = dict()
    for a in lst:
        active[a.app_name] = a.active
    result = []
    for app in apps:
        url = f'{host}/{app}/gallery/app_info'
        response = urlopen(url)
        info = json.loads(response.read())
        info = json_to_storage(info)
        if app not in active:
            continue
        info.active = active[app]
        info.app = app
        result.append(info)
    return dict(result=result)


@serve_json
def update_apps_table():
    apps = app_list()
    for app in apps:
        if db(db.TblApps.app_name==app).isempty():
            db.TblApps.insert(app_name=app)
    n = db(db.TblApps).count()
    return dict(apps_count=n)


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
