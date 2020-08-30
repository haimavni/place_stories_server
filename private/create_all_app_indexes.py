import os
import sys

def create_all_app_indexes():
    os.system('echo create all indexii>./logs/create_indexii.log')
    path = '../web2py/applications/'
    if len(sys.argv) > 1:
        apps = sys.argv[1:]
    else:
        apps = os.listdir(path)
    apps = [app for app in apps if os.path.islink(os.path.join(path, app))]
    for app in apps:
        if app in ['welcome', 'tol_hub', 'gbs']:
            continue
        os.system('python ../web2py/web2py.py -S {app}/admin/create_app_index>>./logs/create_indexii.log'.format(app=app))
    print 'all app indexes were created'

create_all_app_indexes()
