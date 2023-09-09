import os
from dotenv import load_dotenv

from sys import platform
if platform == 'linux':
    from pwd import getpwnam, getpwuid

import stat
import getpass
from .injections import inject
from operator import attrgetter
import qrcode
from folders import local_folder, url_folder
import ws_messaging


def find_owner(filename):
    return getpwuid(os.stat(filename).st_uid).pw_name


def fix_log_owner(log_file_name):
    if platform != 'linux':
        return
    path, fname = os.path.split(log_file_name)
    curr_user = getpass.getuser()
    if curr_user != 'root':
        return
    file_owner = find_owner(log_file_name)
    if file_owner != 'root':
        return
    try:
        request = inject('request')
        parts = request.folder.split('/')
        if len(parts) >= 3:
            u = parts[2]
        else:
            u = 'haim'
        w_rec = getpwnam(u)
        wuid, wgid = w_rec.pw_uid, w_rec.pw_gid
        if file_owner != u:
            os.chown(log_file_name, wuid, wgid)
            os.chmod(log_file_name, stat.S_IRGRP | stat.S_IWGRP | stat.S_IREAD | stat.S_IWRITE | stat.S_IROTH)
    except Exception as e:
        path, fname = os.path.split(log_file_name)
        with open(path + '/' + 'fix_log_owner_failed.log', 'a') as f:
            f.write('folder: ' + request.folder + ' log name: ' + log_file_name + ' error: ' + str(e) + '\n')

def multisort(xs, specs):
    for key, reverse in reversed(specs):
        xs.sort(key=attrgetter(key), reverse=reverse)
    return xs

def make_qr_code(txt, name='qrcode'):
    img = qrcode.make(txt)
    path = local_folder('temp')
    filename = path + name + ".png"
    img.save(filename)
    download_url = url_folder("temp") + name + '.png'
    return dict(download_url=download_url)


def split_and_send(key, arr, target, chunk_size):
    for offset in range(0, len(arr), chunk_size):
        chunk = arr[offset:offset+chunk_size]
        ws_messaging.send_message(key=key, group=target,data=dict(offset=offset, chunk=chunk))

def chmod(path, mod):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), mod)
        for f in files:
            os.chmod(os.path.join(root, f), mod)

def get_env_var(var_name):            
    load_dotenv('/home/www-data/web2py/.env')
    return os.getenv(var_name)

def timestamp(path):
    if not os.path.exists(path):
        return ""
    ctime = round(os.path.getctime(path))
    return f"?d={ctime}"

if __name__ == '__main__':
    fname = '/home/haim/aurelia-gbs/server/tol_server/logs/log_all.log'
    fix_log_owner(fname)
