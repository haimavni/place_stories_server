from genericpath import isfile
import os

def index():
    app = request.application
    lang = 'he'
    app_name_rec = None
    try:
        app_name_rec = db(
            (db.TblLocaleCustomizations.lang == lang) & (db.TblLocaleCustomizations.key == 'app-title')).select().first()
    except Exception as e:
        comment("Failed to load locale customizations")
    app_name = app_name_rec.value if app_name_rec else 'Noname' 
    folder = f'applications/{app}/static/aurelia/scripts'
    #return f'folder is {folder}. app_name is {app_name}'
    lst = os.listdir(folder)
    fname = (app + '__').split('__')[0]
    private_ico_path = f'/apps_data/{fname}/images'
    comment(f"--------ico path: {private_ico_path}/favicon.ico")
    if os.path.exists(private_ico_path + '/favicon.ico'):
        ico_path = f'{app}/static' + private_ico_path # not working yet
    else:
        ico_path = f'/{app}/static/aurelia'
    vendor_bundle = None
    for fname in lst:
        if fname.endswith('.js'):
            if fname.startswith('vendor-bundle'):
                vendor_bundle = f'/{app}/static/aurelia/scripts/{fname}'
    if not vendor_bundle:
        raise Exception("Vendor bundle not found")
    hidden = "__" in app and app != "gbs__www"
    return dict(app=app, app_name=app_name, vendor_bundle=vendor_bundle, ico_path=ico_path, hidden=hidden)