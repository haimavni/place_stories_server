from genericpath import isfile
import os

def index():
    curdir = os.getcwd()
    host = request.env.http_host
    app = request.application
    comment(f"app is {app}")
    lang = 'he'
    app_config = db(db.TblConfiguration).select().first()
    app_name_rec = db(
        (db.TblLocaleCustomizations.lang == lang) & (db.TblLocaleCustomizations.key == 'app-title')).select().first()
    app_name = app_name_rec.value if app_name_rec else 'Noname' 
    folder = f'applications/{app}/static/aurelia/scripts'
    #return f'folder is {folder}. app_name is {app_name}'
    lst = os.listdir(folder)
    path = f"https://{host}/{app}"
    comment(f"path is {path}")
    fname = app + '__'.split('__')[0]
    private_ico = f'/apps_data/images/{fname}'
    if os.path.exists(private_ico + '/favicn.ico'):
        ico_path = private_ico
    else:
        ico_path = path  + '/static/aurelia'
    vendor_bundle = None
    for fname in lst:
        if fname.endswith('.js'):
            if fname.startswith('vendor-bundle'):
                vendor_bundle = f'https://{host}/{app}/static/aurelia/scripts/{fname}'
    if not vendor_bundle:
        raise Exception("Vendor bundle not found")
    return dict(host=host, app=app, app_name=app_name, vendor_bundle=vendor_bundle, path=path, ico_path=ico_path)