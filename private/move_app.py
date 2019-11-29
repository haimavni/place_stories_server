from hashlib import md5
from os import listdir

def db_id(app):
    prefix = 'postgres:psycopg2://lifestone:V3geHanu@localhost/'
    uri = prefix + app
    return md5(uri).hexdigest()
    
def move_app(app, src, dst):
    #collect all matching files and move them from src to dst
    path = os.curdir + 'databases'  #todo....
    file_list = listdir(path)
    pass
    
def remove_obsolete_dbs(active_apps):
    active_ids = set([])
    for app in active_apps:
        id = db_id(app)
        active_ids |= set([id])
    #todo: us to filter out obsolete files

