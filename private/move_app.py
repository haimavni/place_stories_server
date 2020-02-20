from hashlib import md5
from os import listdir
import sys

def db_id(app):
    prefix = 'postgres:psycopg2://lifestone:V3geHanu@localhost/'
    uri = prefix + app
    return md5(uri).hexdigest()
    
def move_app(app=None, src=None, dst=None):
    #collect all matching files and move them from src to dst
    #/home/haim/aurelia-gbs/server/tol_server
    if not app:
        app = raw_input("Enter app name: ")
    if not src:
        src = raw_input("Enter source: ")
    if not dst:
        dst = raw_input("Enter destination: ")
    app_id = db_id(app)
    path = src + '/databases'
    file_list = listdir(path)
    file_list = [f for f in file_list if app_id in f]
    with open("/home/haim/move_app.bash", "w") as out:
        for f in file_list:
            out.write("mv {path}/{src} {dst}\n".format(path=path, src=f, dst=dst))
    
def remove_obsolete_dbs(active_apps=None):
    active_ids = set([])
    path = raw_input("Enter folder name: ")
    path += '/databases/'
    if not active_apps:
        arr = []
        while True:
            app_name = raw_input("Enter app name: ")
            if not app_name:
                break
            arr.append(app_name)
        active_apps = set(arr)
    for app in active_apps:
        id = db_id(app)
        active_ids |= set([id])
    file_list = listdir(path)
    with open("/home/haim/remove_obsolete_apps.bash", "w") as out:
        for f in file_list:
            if ".table" not in f:
                continue
            app_id, dumm = f.split('_')[:2]
            if app_id not in active_ids:
                out.write("rm {path}{f}\n".format(path=path, f=f))
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "1 - show db id of app"
        print "2 - move app to another folder"
        print "3 - remove obsolete apps"
        option = raw_input("Enter option: ")
        if option == "1":
            app_name = raw_input("Enter app name: ")
            print "The db id is ", db_id(app_name)
        elif option == "2":
            move_app()
        elif option == "3":
            remove_obsolete_dbs()
        else:
            print "Unknown option"    
    else:
        app_name = sys.argv[1]
        print "The db id is ", db_id(app_name)


