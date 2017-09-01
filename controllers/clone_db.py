import os
import hashlib
from shutil import copyfile

def duplicate_db():
    #after we duplicate db to become the dev db, we need to copy the files in databases renamed using the name that is calculated from the new uri
    #todo: complete it
    new_dbname = request.vars.dbname
    dbname = request.application
    adapter = 'psycopg2:'
    src_folder = 'applications/{}/databases/'.format(dbname)
    dst_folder = 'applications/{}/databases/'.format(new_dbname)
    cmd = '''
    # clone {old_database_name} to {new_database_name}
    sudo su postgres
    psql
    CREATE DATABASE {new_database_name};
    GRANT ALL PRIVILEGES ON DATABASE {new_database_name} TO {user};
    \q
    ##Copy structure and data from the old database to the new one:

    pg_dump {old_database_name} | psql {new_database_name}
    '''.format(old_database_name=dbname, new_database_name=new_dbname, user='postgres')
    with open('applications/{dbname}/logs/{dbname}-to-{new_dbname}.log'.format(dbname=dbname, new_dbname=new_dbname), 'w') as f:
        f.write(cmd)
    hashlib_md5 = hashlib.md5
    uri = 'postgres:{ad}//lifestone:V3geHanu@localhost/{dbn}'.format(ad=adapter, dbn=dbname)    
    src_pat = hashlib_md5(uri).hexdigest()
    uri = 'postgres:{ad}//lifestone:V3geHanu@localhost/{dbn}'.format(ad=adapter, dbn=new_dbname)    
    dst_pat = hashlib_md5(uri).hexdigest()
    for (root, dirnames, filenames) in os.walk(src_folder):
        for filename in filenames:
            if filename.startswith(src_pat):
                dst_filename = filename.replace(src_pat, dst_pat)
                copyfile(src_folder+filename, dst_folder+dst_filename)
