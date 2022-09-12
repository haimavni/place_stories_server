import os
import sys

def create_all_app_indexes():
    web2py_dir = '/home/www-data/py38env/web2py'
    os.system('echo create all indexii>./logs/create_indexii.log')
    path = f'{web2py_dir}/applications/'
    if len(sys.argv) > 1:
        apps = sys.argv[1:]
    else:
        apps = os.listdir(path)
    apps = [app for app in apps if os.path.islink(os.path.join(path, app))]
    failed = []
    for app in apps:
        if app in ['welcome', 'gbs']:
            continue
        result = os.system(f'python {web2py_dir}/web2py.py -S {app}/admin/create_app_index>>./logs/create_indexii.log')
        if result:
            failed.append(app)
    if failed:
        print(f'apps that failed to create app index: {failed}')
    else:
        print('all app indexes were created')

create_all_app_indexes()
