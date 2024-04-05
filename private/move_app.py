from hashlib import md5
from os import listdir
import sys

def db_id(app, port=""):
    prefix = f'postgres:psycopg2://lifestone:V3geHanu@localhost{port}/'
    uri = prefix + app
    uri = uri.encode('utf-8')
    return md5(uri).hexdigest()
    
def move_app(cp_or_mv, app=None, new_app=None, src=None, dst=None):
    #collect all matching files and move them from src to dst
    #/home/haim/aurelia-gbs/server/tol_server
    if not app:
        app = input("Enter app name: ")
    if not src:
        print("Select source:")
        print("1 - www")
        print("2 - test")
        print("3 - master")
        print("4 - local")
        option = input("Enter option: ")
        if option == "4":
            src = "/home/haim/sandbox/src"
        else:
            src = "/home/www-data/tol_" + ("www" if option == "1" else "test" if option == "2" else "master")
        print(f"source is {src}")
    src_port = select_port("source")
    if not dst:
        print("Select destination:")
        print("1 - www")
        print("2 - test")
        print("3 - master")
        print("4 - local")
        option = input("Enter option: ")
        if option == "4":
            dst = "/home/haim/sandbox/dst"
        else:
            dst = "/home/www-data/tol_" + ("www" if option == "1" else "test" if option == "2" else "master" if option == "3" else "local")
        print(f"Destination is {dst}")
    dst_port = select_port("destination")
        
    src_app_id = db_id(app, src_port)
    target_app = input(f"enter target app ({app}): ")
    if not target_app:
        if (src == dst) and (src_port == dst_port):
            print("Copying into itself!")
            exit()
        target_app = ""
    path = src + '/databases'
    file_list = listdir(path)
    n = len(src_app_id)
    target_app_id = db_id(target_app, dst_port)
    file_list = [f for f in file_list if src_app_id in f]
    if not file_list:
        print(f"app {app} not found in {path}!")
        exit()
    with open(f"/home/haim/fixes/move_app_{target_app}.bash", "w") as out:
        out.write(f"rm -f {dst}/databases/*{target_app_id}*\n")
        for src in file_list:
            if target_app:
                out.write(f"{cp_or_mv} {path}/{src:64} {dst}/databases/{target_app_id + src[n:]}\n")
            else:
                out.write(f"{cp_or_mv} {path}/{src:64} {dst}/\n")
        out.write(f"chown www-data:www-data {dst}/databases/*")
        
def select_port(what):
    print(f"Select {what} port:")
    print("1 - 5432")
    print("2 - 5433")
    print("3 - Omit port")
    option = input("Enter option: ")
    return ":5432" if option == "1" else ":5433" if option == "2" else ""
   
def remove_obsolete_dbs(active_apps=None):
    active_ids = set([])
    path = input("Enter folder name: ")
    path += '/databases/'
    if not active_apps:
        arr = []
        while True:
            app_name = input("Enter app name: ")
            if not app_name:
                break
            arr.append(app_name)
        active_apps = set(arr)
    for app in active_apps:
        port = select_port("")
        id = db_id(app, port)
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
        print("1 - show db id of app")
        print("2 - move app to another folder")
        print("3 - remove obsolete apps")
        option = input("Enter option: ")
        if option == "1":
            app_name = input("Enter app name: ")
            port = select_port("")
            print("The db id is ", db_id(app_name, port))
        elif option == "2":
            cp_or_mv = input("Enter cp or mv (cp): ")
            if not cp_or_mv:
                cp_or_mv = "cp"
            if cp_or_mv not in ("mv", "cp"):
                print("Please enter cp or mv")
                exit()
            move_app(cp_or_mv)
        elif option == "3":
            remove_obsolete_dbs()
        else:
            print("Unknown option")    
    else:
        app_name = sys.argv[1]
        print("The db id is ", db_id(app_name))


