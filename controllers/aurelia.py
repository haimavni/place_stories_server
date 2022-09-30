import os

def index():
    curdir = os.getcwd()
    return curdir
    host = request.env.http_host
    app = request.application
    lang = 'he'
    app_config = db(db.TblConfiguration).select().first()
    app_name_rec = db(
        (db.TblLocaleCustomizations.lang == lang) & (db.TblLocaleCustomizations.key == 'app-title')).select().first()
    app_name = app_name_rec.value if app_name_rec else 'Noname' 
    folder = f'applications/{app}/static/aurelia/script'
    lst = os.listdir(folder)
    for fname in lst:
        if fname.endswith('.js'):
            if fname.startswith('vendor-bundle'):
                vendor_bundle = f'https://{host}/{app}/static/aurelia/scripts/{fname}'
    return dict(app=app, app_name=app_name, vendor_bundle=vendor_bundle)